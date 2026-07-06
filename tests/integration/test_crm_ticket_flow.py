"""Integration test for rich Arabic CRM ticket creation flow."""

import json
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
from agent.graph import run_agent
from core.db import get_leads_collection


def _make_choice(content: str = "", tool_calls=None, usage_tokens=(0, 0)):
    """Build a mock chat.completion choice."""
    message = MagicMock()
    message.content = content
    message.reasoning = None
    message.tool_calls = tool_calls or []

    choice = MagicMock()
    choice.message = message

    usage = MagicMock()
    usage.prompt_tokens, usage.completion_tokens = usage_tokens

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _make_tool_call(name: str, arguments: dict, call_id: str = "call_1"):
    """Build a mock tool call object."""
    func = MagicMock()
    func.name = name
    func.arguments = json.dumps(arguments)

    tc = MagicMock()
    tc.id = call_id
    tc.function = func
    tc.model_dump.return_value = {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": func.arguments},
    }
    return tc


def test_run_agent_creates_rich_arabic_ticket():
    """When the LLM calls create_lead_ticket, the graph extracts Arabic fields and stores them."""
    coll = get_leads_collection()
    initial_count = coll.count_documents({})

    fake_extraction = {
        "fields": {
            "name": "أحمد منصور",
            "phone": "01001234567",
            "email": "",
            "city": "القاهرة، مصر",
            "language_dialect": "العربية — اللهجة المصرية",
            "products": "دبلومة SOC Track",
            "goal": "التحول إلى أمن سيبراني",
            "level": "مبتدئ",
            "temperature": "ساخن",
            "buying_signals": "سأل عن السعر والتقسيط",
            "objections": "قلق من السعر",
            "conversation_summary": "عميل جاد يريد التسجيل.",
            "next_action": "تواصل واتساب",
            "preferred_contact": "واتساب",
        },
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }

    # First LLM response: decide to create a lead ticket
    tool_call = _make_tool_call("create_lead_ticket", {"name": "أحمد", "products": "SOC Track"})
    first_response = _make_choice(tool_calls=[tool_call], usage_tokens=(100, 50))
    # Second LLM response: final answer after tool result
    second_response = _make_choice("تمام، هتواصل معاك مستشار المبيعات قريب.", usage_tokens=(80, 30))

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = [first_response, second_response]

    fake_openai_class = MagicMock(return_value=fake_client)

    with patch("agent.graph.OpenAI", fake_openai_class), \
         patch("agent.graph._extract_crm_fields", return_value=fake_extraction):
        result = run_agent(
            user_message="أنا أحمد من القاهرة، عايز أسجل في دبلومة SOC Track",
            conversation_history=[
                {"role": "user", "content": "عندكم دبلومة SOC؟"},
                {"role": "assistant", "content": "آه، فيها مسار كامل للمبتدئين."},
            ],
            username="ahmed",
        )

    final_count = coll.count_documents({})
    assert final_count == initial_count + 1, f"Expected one new ticket, got {final_count - initial_count}"

    new_doc = coll.find_one({"name": "أحمد منصور"})
    assert new_doc is not None
    assert new_doc["city"] == "القاهرة، مصر"
    assert new_doc["temperature"] == "ساخن"
    assert "LEAD-" in new_doc.get("ticket_id", "")

    # Cleanup
    coll.delete_one({"_id": ObjectId(new_doc["_id"])})
