"""
Usage logger: records LLM calls, tool usage, and token consumption.

Used by:
- agent/graph.py      → log each LLM completion
- agent/tools.py      → log each tool call
- pages/3_Cost_Monitor.py  → read and aggregate usage_logs

This module is Part 2.A infrastructure — the cost monitor reads from MongoDB
independently without importing agent internals.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.db import get_usage_logs_collection


def log_llm_usage(
    run_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: float,
    user_message: str = "",
    response_summary: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Log a single LLM completion to usage_logs collection.

    Returns the log document ID.
    """
    coll = get_usage_logs_collection()
    doc = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost,
        "user_message_preview": user_message[:200] if user_message else "",
        "response_preview": response_summary[:200] if response_summary else "",
        "metadata": metadata or {},
    }
    result = coll.insert_one(doc)
    return str(result.inserted_id)


def log_tool_usage(
    tool_name: str,
    arguments: Dict[str, Any],
    run_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Log a tool invocation to usage_logs collection.

    Returns the log document ID.
    """
    coll = get_usage_logs_collection()
    doc = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "tool_call",
        "run_id": run_id or "unknown",
        "tool_name": tool_name,
        "arguments": arguments,
        "metadata": metadata or {},
    }
    result = coll.insert_one(doc)
    return str(result.inserted_id)


def log_behaviour(
    run_id: str,
    step_type: str,  # "llm_call", "tool_call", "user_input", "final_response"
    detail: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Log an agent behaviour/decision trace to behaviour_logs collection.

    Used by Part 2.B — Behaviour Trace.
    """
    from core.db import get_behaviour_logs_collection

    coll = get_behaviour_logs_collection()
    doc = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step_type": step_type,
        "detail": detail,
        "metadata": metadata or {},
    }
    result = coll.insert_one(doc)
    return str(result.inserted_id)


def generate_run_id() -> str:
    """Generate a unique run ID for a conversation session."""
    return str(uuid.uuid4())
