"""
Agent tools: search_kb, get_roadmap, create_lead_ticket.

These are the tools exposed to the LLM via function-calling.
Each tool:
1. Has a JSON schema descriptor (for the LLM)
2. Has a Python implementation
3. Logs usage for cost monitoring
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from rag.retriever import search_kb, get_roadmap_by_id
from core.db import get_leads_collection
from agent.usage_logger import log_tool_usage


# ---------------------------------------------------------------------------
# Tool schemas (for OpenAI function-calling)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": (
                "Search Kayfa's knowledge base for courses, tracks, diplomas, "
                "policies, instructors, prices, accreditation, or any platform information. "
                "This is your first step before answering any substantive question. "
                "Use it to ground recommendations, policy answers, and comparisons in real data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query in English or Arabic. Be specific.",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_roadmap",
            "description": (
                "Get detailed information about a specific learning path (track or diploma) "
                "by its exact ID. Use this when the user asks about a specific track/diploma name, "
                "or when comparing tracks/diplomas after searching the catalog."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "roadmap_id": {
                        "type": "string",
                        "description": (
                            "The exact roadmap/track/diploma ID, e.g. 'kayfa_data_science_track', "
                            "'kayfa_soc_diploma', 'kayfa_ai_diploma', 'kayfa_fullstack_diploma'."
                        ),
                    },
                },
                "required": ["roadmap_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_lead_ticket",
            "description": (
                "Create a rich Arabic CRM lead ticket when the visitor shows real buying signals. "
                "Use after providing value. The ticket should be in Arabic with course/tech terms in original form."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "الاسم الكامل للعميل"},
                    "phone": {"type": "string", "description": "رقم الهاتف / واتساب"},
                    "email": {"type": "string", "description": "البريد الإلكتروني"},
                    "city": {"type": "string", "description": "المدينة والدولة"},
                    "language_dialect": {"type": "string", "description": "اللغة واللهجة، مثال: العربية — اللهجة المصرية"},
                    "products": {"type": "string", "description": "المنتجات محل الاهتمام (كورسات، مسارات، دبلومات)"},
                    "goal": {"type": "string", "description": "الهدف من التعلم / التحول المهني"},
                    "level": {"type": "string", "description": "مستوى الخبرة الحالي"},
                    "temperature": {"type": "string", "enum": ["ساخن", "دافئ", "بارد"], "description": "درجة حرارة العميل"},
                    "buying_signals": {"type": "string", "description": "إشارات الشراء التي أظهرها العميل"},
                    "objections": {"type": "string", "description": "الاعتراضات وكيف تمت معالجتها"},
                    "conversation_summary": {"type": "string", "description": "ملخص المحادثة بالعربية"},
                    "next_action": {"type": "string", "description": "الإجراء التالي الموصى به"},
                    "preferred_contact": {"type": "string", "enum": ["واتساب", "هاتف", "بريد"], "description": "طريقة التواصل المفضلة"},
                },
                "required": ["name", "products"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_ticket_id() -> str:
    """Generate a sequential ticket ID like LEAD-2026-0042."""
    coll = get_leads_collection()
    year = datetime.utcnow().year
    prefix = f"LEAD-{year}-"
    count = coll.count_documents({"ticket_id": {"$regex": f"^{prefix}"}})
    return f"{prefix}{count + 1:04d}"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_search_kb(query: str, k: int = 5) -> Dict[str, Any]:
    """Search the knowledge base."""
    log_tool_usage("search_kb", {"query": query, "k": k})
    results = search_kb(query, k=k)
    return {
        "status": "success",
        "results_count": len(results),
        "results": results,
    }


def tool_get_roadmap(roadmap_id: str) -> Dict[str, Any]:
    """Get a specific roadmap by ID."""
    log_tool_usage("get_roadmap", {"roadmap_id": roadmap_id})
    result = get_roadmap_by_id(roadmap_id)
    if result is None:
        return {
            "status": "not_found",
            "message": f"No roadmap found with ID '{roadmap_id}'.",
        }
    return {
        "status": "success",
        "roadmap": result,
    }


def tool_create_lead_ticket(
    name: str,
    products: str,
    phone: str = "",
    email: str = "",
    city: str = "",
    language_dialect: str = "",
    goal: str = "",
    level: str = "",
    temperature: str = "دافئ",
    buying_signals: str = "",
    objections: str = "",
    conversation_summary: str = "",
    next_action: str = "",
    preferred_contact: str = "واتساب",
) -> Dict[str, Any]:
    """Create a rich Arabic lead ticket in MongoDB."""
    log_tool_usage("create_lead_ticket", {
        "name": name,
        "products": products,
        "phone": phone,
        "email": email,
    })

    lead_doc = {
        "ticket_id": _generate_ticket_id(),
        "name": name,
        "phone": phone,
        "email": email,
        "city": city,
        "language_dialect": language_dialect,
        "products": products,
        "goal": goal,
        "level": level,
        "temperature": temperature,
        "buying_signals": buying_signals,
        "objections": objections,
        "conversation_summary": conversation_summary,
        "next_action": next_action,
        "preferred_contact": preferred_contact,
        "status": "new",  # new → contacted → qualified → closed
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "source": "chat_agent",
    }

    try:
        coll = get_leads_collection()
        result = coll.insert_one(lead_doc)
        return {
            "status": "success",
            "lead_id": str(result.inserted_id),
            "message": (
                f"Thank you {name}! I've created a lead ticket for your interest in {products}. "
                f"A Kayfa advisor will contact you soon."
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create lead ticket: {str(e)}",
        }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

TOOL_MAP = {
    "search_kb": tool_search_kb,
    "get_roadmap": tool_get_roadmap,
    "create_lead_ticket": tool_create_lead_ticket,
}


def dispatch_tool(tool_name: str, arguments: dict) -> Dict[str, Any]:
    """Dispatch a tool call to the appropriate implementation."""
    if tool_name not in TOOL_MAP:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    tool_func = TOOL_MAP[tool_name]
    try:
        return tool_func(**arguments)
    except Exception as e:
        return {"status": "error", "message": f"Tool execution error: {str(e)}"}
