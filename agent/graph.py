"""
Agent graph / loop: orchestrates tool-calling between the LLM and tools.

Flow:
1. Receive user message + conversation history
2. Classify visitor intent and conversation stage
3. Call LLM with a sales-aware system prompt + tools
4. If LLM wants to call a tool → execute tool, append result, re-call LLM
5. If LLM returns a direct response → deliver to user
6. Log usage and behaviour at each step

This is a simple ReAct-style loop using OpenAI's function-calling API,
augmented with lightweight sales-state tracking.
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from openai import OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt

from core.config import get_settings, estimate_cost
from agent.prompts import format_system_prompt, CRM_TICKET_PROMPT
from agent.tools import TOOL_SCHEMAS, dispatch_tool
from agent.usage_logger import log_llm_usage, log_behaviour, generate_run_id

settings = get_settings()


# ---------------------------------------------------------------------------
# Lightweight intent & stage classification
# ---------------------------------------------------------------------------

def classify_intent(user_message: str, conversation_history: List[Dict[str, str]]) -> str:
    """Classify visitor intent from the current message and recent history."""
    msg_lower = user_message.lower()

    # Arabic/English ready-to-enroll signals
    ready_signals = [
        "enroll", "register", "sign up", "join", "apply", "payment", "pay",
        "call me", "callback", "contact me", "next steps", "want to start",
        "سجل", "أسجل", "التسجيل", "الدفع", "اتصل", "كلموني", "أشترك", "أنضم",
    ]
    for signal in ready_signals:
        if signal in msg_lower:
            return "ready_to_enroll"

    # Price-sensitive signals
    price_signals = [
        "price", "cost", "how much", "discount", "cheap", "expensive", "budget",
        "installment", "fees", "usd", "$", "السعر", "التكلفة", "الدفع", "التقسيط",
        "خصم", "رخيص", "غالي", "الميزانية",
    ]
    for signal in price_signals:
        if signal in msg_lower:
            return "price_sensitive"

    # Comparing signals
    compare_signals = [
        "vs", "versus", "compare", "difference between", "which is better",
        "which one", "or", "أفضل", "أحسن", "مقارنة", "الفرق", "ولا", "أو",
    ]
    for signal in compare_signals:
        if signal in msg_lower:
            return "comparing"

    # Hesitant signals
    hesitant_signals = [
        "not sure", "hesitant", "doubt", "afraid", "worried", "unsure", "maybe",
        "thinking about it", "don't know", "لست متأكد", "متردد", "خايف", "قلق",
        "ربما", "أفكر", "مش عارف",
    ]
    for signal in hesitant_signals:
        if signal in msg_lower:
            return "hesitant"

    # If history has several turns and previous intent was comparing/price_sensitive,
    # stay there instead of dropping back to browsing.
    if conversation_history:
        recent_user_msgs = [
            m.get("content", "").lower()
            for m in conversation_history[-4:]
            if m.get("role") == "user"
        ]
        for recent in recent_user_msgs:
            if any(s in recent for s in ["vs", "compare", "difference", "أفضل", "الفرق"]):
                return "comparing"
            if any(s in recent for s in ["price", "cost", "how much", "السعر", "التقسيط"]):
                return "price_sensitive"

    return "browsing"


def derive_stage(
    intent: str,
    turn_count: int,
    conversation_history: List[Dict[str, str]],
) -> str:
    """Derive conversation stage from intent and turn depth."""
    if intent == "ready_to_enroll":
        return "converting"
    if intent == "hesitant" and turn_count >= 3:
        return "deciding"
    if intent in ("comparing", "price_sensitive") and turn_count >= 3:
        return "evaluating"
    if intent in ("comparing", "price_sensitive"):
        return "exploring"
    if turn_count == 1:
        return "early"
    return "exploring"


def is_buying_signal_strong(
    intent: str,
    stage: str,
    user_message: str,
) -> bool:
    """Return True if the visitor has shown enough signal to create a lead ticket."""
    if intent == "ready_to_enroll":
        return True
    if stage in ("evaluating", "deciding", "converting"):
        ready_words = [
            "enroll", "register", "sign up", "join", "apply", "pay", "payment",
            "call me", "callback", "contact", "advisor", "next steps",
            "سجل", "أسجل", "التسجيل", "الدفع", "اتصل", "كلموني", "مستشار",
        ]
        msg_lower = user_message.lower()
        return any(w in msg_lower for w in ready_words)
    return False


def _build_conversation_text(
    user_message: str,
    conversation_history: List[Dict[str, str]],
) -> str:
    """Build a single Arabic/English transcript for CRM extraction."""
    lines = []
    for msg in conversation_history[-10:]:
        role = "User" if msg.get("role") == "user" else "Kayfa"
        lines.append(f"{role}: {msg.get('content', '')}")
    lines.append(f"User: {user_message}")
    return "\n".join(lines)


def _extract_crm_fields(
    client: OpenAI,
    model: str,
    provider: str,
    conversation_text: str,
) -> Dict[str, Any]:
    """Use the LLM to extract rich Arabic CRM fields from the conversation.

    Returns a dict with keys:
      - fields: extracted CRM fields
      - input_tokens, output_tokens, cost_usd: usage/cost estimates (0 on failure)
    """
    messages = [
        {"role": "system", "content": CRM_TICKET_PROMPT},
        {"role": "user", "content": conversation_text},
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
    except Exception:
        return {"fields": {}, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}

    if not response.choices:
        return {"fields": {}, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}

    raw = _extract_message_text(response.choices[0].message)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract a JSON object from the text
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            return {"fields": {}, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"fields": {}, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}

    # Normalize nulls to empty strings for string fields
    fields_set = {
        "name", "phone", "email", "city", "language_dialect",
        "products", "goal", "level", "temperature", "buying_signals",
        "objections", "conversation_summary", "next_action", "preferred_contact",
    }
    fields = {}
    for field in fields_set:
        value = parsed.get(field)
        if value is None:
            value = ""
        elif isinstance(value, list):
            # Join Arabic lists with an Arabic comma for display consistency
            value = "، ".join(str(v) for v in value)
        else:
            value = str(value)
        fields[field] = value

    input_tokens = response.usage.prompt_tokens if response.usage else 0
    output_tokens = response.usage.completion_tokens if response.usage else 0
    cost_usd = estimate_cost(provider, model, input_tokens, output_tokens)

    return {
        "fields": fields,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }


def _extract_message_text(assistant_msg) -> str:
    """Extract usable text from an assistant message.

    Some free models put text in the `reasoning` field and leave `content` empty.
    """
    if assistant_msg.content:
        return assistant_msg.content
    # Check for reasoning field (OpenRouter-style)
    reasoning = getattr(assistant_msg, "reasoning", None)
    if reasoning:
        return reasoning
    return ""


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------

def run_agent(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    username: str = "visitor",
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the sales agent for a single turn.

    Args:
        user_message: The current user message.
        conversation_history: Previous messages [{"role": "user"|"assistant", "content": str}].
        username: The logged-in user's name.
        run_id: Optional existing run ID (for multi-turn conversations).

    Returns:
        Dict with keys: response (str), run_id (str), tool_calls (list), cost (float).
    """
    # Initialize OpenAI-compatible client (OpenRouter or native OpenAI)
    client_kwargs = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url
    client = OpenAI(**client_kwargs)
    model = settings.llm_model
    provider = settings.llm_provider
    run_id = run_id or generate_run_id()
    turn_count = len(conversation_history) // 2 + 1

    # Classify visitor state
    visitor_intent = classify_intent(user_message, conversation_history)
    conversation_stage = derive_stage(visitor_intent, turn_count, conversation_history)

    # Build system prompt
    system_prompt = format_system_prompt(
        today_date=datetime.now().strftime("%Y-%m-%d"),
        username=username,
        turn_count=turn_count,
        visitor_intent=visitor_intent,
        conversation_stage=conversation_stage,
    )

    # Build messages
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
    ]
    # Add conversation history (last 10 messages to stay within context)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    tool_calls_log = []
    total_cost = 0.0
    max_iterations = 3

    # ------------------------------------------------------------------
    # ReAct loop: LLM → tool call → LLM → ... → final response
    # ------------------------------------------------------------------

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True,
    )
    def _call_llm(tools: Optional[list] = None):
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return client.chat.completions.create(**kwargs)

    for iteration in range(max_iterations):
        try:
            response = _call_llm(tools=TOOL_SCHEMAS)
        except Exception as e:
            return {
                "response": f"I apologize, I'm having trouble connecting to my knowledge base right now. Please try again later. (Error: {str(e)})",
                "run_id": run_id,
                "tool_calls": tool_calls_log,
                "cost": total_cost,
            }

        if not response.choices:
            return {
                "response": "I apologize, I received an empty response from the language model. Please try again.",
                "run_id": run_id,
                "tool_calls": tool_calls_log,
                "cost": total_cost,
            }
        choice = response.choices[0]
        assistant_msg = choice.message
        msg_text = _extract_message_text(assistant_msg)

        # Track token usage
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        call_cost = estimate_cost(provider, model, input_tokens, output_tokens)
        total_cost += call_cost

        # Log LLM usage
        log_llm_usage(
            run_id=run_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=call_cost,
            user_message=user_message if iteration == 0 else "",
            response_summary=msg_text,
            metadata={
                "visitor_intent": visitor_intent,
                "conversation_stage": conversation_stage,
                "iteration": iteration,
            },
        )

        # Log behaviour trace
        log_behaviour(
            run_id=run_id,
            step_type="llm_call",
            detail={
                "iteration": iteration,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": call_cost,
                "has_tool_calls": bool(assistant_msg.tool_calls),
                "visitor_intent": visitor_intent,
                "conversation_stage": conversation_stage,
            },
        )

        # Check if the LLM wants to call tools
        if assistant_msg.tool_calls:
            # Append assistant's tool-call request to messages
            messages.append({
                "role": "assistant",
                "content": msg_text,
                "tool_calls": [tc.model_dump() for tc in assistant_msg.tool_calls],
            })

            # Execute each tool call
            for tc in assistant_msg.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                # Guard: don't create lead tickets before buying signal is strong enough
                if tool_name == "create_lead_ticket":
                    if not is_buying_signal_strong(visitor_intent, conversation_stage, user_message):
                        result = {
                            "status": "deferred",
                            "message": (
                                "Lead ticket creation was deferred because the visitor has not "
                                "shown a clear buying signal yet. Provide more value first."
                            ),
                        }
                    else:
                        # Extract rich Arabic CRM fields from the full conversation
                        conversation_text = _build_conversation_text(user_message, conversation_history)
                        extraction = _extract_crm_fields(client, model, provider, conversation_text)
                        extracted = extraction["fields"]

                        # Track extraction cost
                        total_cost += extraction["cost_usd"]
                        log_llm_usage(
                            run_id=run_id,
                            provider=provider,
                            model=model,
                            input_tokens=extraction["input_tokens"],
                            output_tokens=extraction["output_tokens"],
                            estimated_cost=extraction["cost_usd"],
                            user_message="",
                            response_summary="crm_extraction",
                            metadata={
                                "visitor_intent": visitor_intent,
                                "conversation_stage": conversation_stage,
                                "extraction_call": True,
                            },
                        )
                        log_behaviour(
                            run_id=run_id,
                            step_type="crm_extraction",
                            detail={
                                "input_tokens": extraction["input_tokens"],
                                "output_tokens": extraction["output_tokens"],
                                "cost_usd": extraction["cost_usd"],
                                "extracted_fields": list(extracted.keys()),
                            },
                        )

                        # Merge extracted fields with any fields the LLM already provided.
                        # The extraction call is authoritative for Arabic copy; tool args fill gaps.
                        merged = dict(extracted)
                        for key in extracted:
                            if not merged.get(key) and arguments.get(key):
                                merged[key] = arguments.get(key)

                        # Legacy fallback: old schema used "interest" and "contact"
                        if not merged.get("products"):
                            merged["products"] = arguments.get("products") or arguments.get("interest", "")
                        if not merged.get("name"):
                            merged["name"] = arguments.get("name", username)
                        if not merged.get("phone"):
                            merged["phone"] = arguments.get("phone") or arguments.get("contact", "")
                        if not merged.get("email"):
                            merged["email"] = arguments.get("email", "")

                        # Append internal metadata to the summary
                        meta = (
                            f"inferred_intent={visitor_intent}; "
                            f"stage={conversation_stage}; "
                            f"language={'Arabic' if re.search(r'[\u0600-\u06FF]', user_message) else 'English'}"
                        )
                        summary = merged.get("conversation_summary", "")
                        merged["conversation_summary"] = f"{summary} | {meta}".strip(" |") if summary else meta

                        # Ensure required fields exist
                        merged.setdefault("name", username)
                        merged.setdefault("products", "")
                        merged.setdefault("temperature", "دافئ")
                        merged.setdefault("preferred_contact", "واتساب")

                        arguments = merged
                        result = dispatch_tool(tool_name, arguments)
                else:
                    result = dispatch_tool(tool_name, arguments)

                tool_calls_log.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                })

                # Log behaviour
                log_behaviour(
                    run_id=run_id,
                    step_type="tool_call",
                    detail={
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result_status": result.get("status", "unknown"),
                    },
                )

                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

            # If this was the last allowed iteration, force a final answer now.
            if iteration >= max_iterations - 1:
                messages.append({
                    "role": "system",
                    "content": (
                        "You have already used the available tool calls. "
                        "Now answer the user directly based on the tool results above. "
                        "Do not call any more tools."
                    ),
                })
                continue

            # Otherwise loop back to let the LLM process the tool results
            continue

        # No tool calls — final response
        final_content = msg_text or "I'm not sure how to answer that. Could you rephrase?"

        # Log final response behaviour
        log_behaviour(
            run_id=run_id,
            step_type="final_response",
            detail={
                "response_length": len(final_content),
                "total_iterations": iteration + 1,
                "total_cost_usd": total_cost,
                "visitor_intent": visitor_intent,
                "conversation_stage": conversation_stage,
            },
        )

        return {
            "response": final_content,
            "run_id": run_id,
            "tool_calls": tool_calls_log,
            "cost": total_cost,
        }

    # Max iterations reached — try one final no-tools synthesis
    try:
        final_response = _call_llm(tools=None)
        if final_response.choices:
            final_content = _extract_message_text(final_response.choices[0].message)
        else:
            final_content = ""
    except Exception:
        final_content = ""

    if not final_content:
        final_content = (
            "I've gathered the information you need. Let me connect you with a human advisor "
            "who can help you take the next step. Would you like me to create a lead ticket?"
        )

    return {
        "response": final_content,
        "run_id": run_id,
        "tool_calls": tool_calls_log,
        "cost": total_cost,
    }
