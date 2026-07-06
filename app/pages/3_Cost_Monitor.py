"""
Page 3 — Cost Monitor (Part 2.A, Admin Only)

Tracks and visualizes LLM API usage and estimated costs.
Reads from usage_logs collection independently — no dependency on agent internals.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

st.set_page_config(
    page_title="Cost Monitor — Kayfa",
    page_icon="💰",
    layout="wide",
)

from datetime import datetime, timedelta
from collections import defaultdict

import sys
from pathlib import Path
repo_root = str(Path(__file__).resolve().parent.parent.parent)
if repo_root not in sys.path:
    sys.path.append(repo_root)

from core.auth import require_auth, require_admin
from core.db import get_usage_logs_collection
from sidebar_helper import render_sidebar

LOGO_PATH = Path(__file__).resolve().parent.parent / "logo.png"

require_auth()
require_admin()

render_sidebar()

st.title("💰 Cost Monitor")
st.caption("This tool helps us keep an eye on our API costs and token usage in real-time. You can filter by date to review daily trends and check how much we are spending per model.")
st.markdown("---")

# Date range filter
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start date",
        value=datetime.now() - timedelta(days=7),
        max_value=datetime.now(),
    )
with col2:
    end_date = st.date_input(
        "End date",
        value=datetime.now(),
        max_value=datetime.now(),
    )

coll = get_usage_logs_collection()

# Build date filter for MongoDB (ISO strings)
start_iso = f"{start_date.isoformat()}T00:00:00"
end_iso = f"{end_date.isoformat()}T23:59:59"

date_query = {
    "timestamp": {
        "$gte": start_iso,
        "$lte": end_iso,
    }
}

# Fetch logs
logs = list(coll.find(date_query).sort("timestamp", -1))

if not logs:
    st.info("No usage logs found for the selected date range.")
    st.stop()

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
total_cost = sum(log.get("estimated_cost_usd", 0) for log in logs)
total_input_tokens = sum(log.get("input_tokens", 0) for log in logs)
total_output_tokens = sum(log.get("output_tokens", 0) for log in logs)
total_calls = len([l for l in logs if l.get("type") != "tool_call"])
total_tool_calls = len([l for l in logs if l.get("type") == "tool_call"])

mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
with mcol1:
    st.metric("Total Cost", f"${total_cost:.4f}")
with mcol2:
    st.metric("Input Tokens", f"{total_input_tokens:,}")
with mcol3:
    st.metric("Output Tokens", f"{total_output_tokens:,}")
with mcol4:
    st.metric("LLM Calls", total_calls)
with mcol5:
    st.metric("Tool Calls", total_tool_calls)

st.markdown("---")

# ---------------------------------------------------------------------------
# Cost by provider/model
# ---------------------------------------------------------------------------
model_costs = defaultdict(lambda: {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0})
for log in logs:
    if log.get("type") == "tool_call":
        continue
    key = f"{log.get('provider', 'unknown')} / {log.get('model', 'unknown')}"
    model_costs[key]["cost"] += log.get("estimated_cost_usd", 0)
    model_costs[key]["input_tokens"] += log.get("input_tokens", 0)
    model_costs[key]["output_tokens"] += log.get("output_tokens", 0)
    model_costs[key]["calls"] += 1

st.subheader("Cost by Provider / Model")
model_data = []
for model_key, data in sorted(model_costs.items(), key=lambda x: -x[1]["cost"]):
    model_data.append({
        "Provider / Model": model_key,
        "Cost ($)": round(data["cost"], 6),
        "Input Tokens": data["input_tokens"],
        "Output Tokens": data["output_tokens"],
        "Calls": data["calls"],
    })

if model_data:
    st.dataframe(model_data, use_container_width=True, hide_index=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Daily cost trend
# ---------------------------------------------------------------------------
st.subheader("Daily Cost Trend")
daily_costs = defaultdict(float)
daily_calls = defaultdict(int)
for log in logs:
    day = log["timestamp"][:10]  # YYYY-MM-DD
    daily_costs[day] += log.get("estimated_cost_usd", 0)
    if log.get("type") != "tool_call":
        daily_calls[day] += 1

# Fill in missing days
days_list = []
current = start_date
while current <= end_date:
    day_str = current.isoformat()
    days_list.append(day_str)
    current += timedelta(days=1)

chart_data = {
    "Date": days_list,
    "Cost ($)": [round(daily_costs.get(d, 0), 6) for d in days_list],
    "Calls": [daily_calls.get(d, 0) for d in days_list],
}

st.line_chart(chart_data, x="Date", y="Cost ($)")
st.bar_chart(chart_data, x="Date", y="Calls")

st.markdown("---")

# ---------------------------------------------------------------------------
# Recent logs table
# ---------------------------------------------------------------------------
st.subheader("Recent Logs")
log_data = []
for log in logs[:100]:  # limit to last 100 for performance
    log_data.append({
        "Timestamp": log.get("timestamp", "")[:19],
        "Provider": log.get("provider", ""),
        "Model": log.get("model", ""),
        "Input": log.get("input_tokens", 0),
        "Output": log.get("output_tokens", 0),
        "Cost ($)": round(log.get("estimated_cost_usd", 0), 6),
        "Type": log.get("type", "llm_call"),
    })

st.dataframe(log_data, use_container_width=True, hide_index=True)
