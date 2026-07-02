"""
Page 4 — Behaviour Trace (Part 2.B, Admin Only)

Inspect the agent's decision-making process step by step.
Shows the ReAct loop: user input → LLM calls → tool calls → final response.
Useful for debugging, auditing, and improving the agent.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

st.set_page_config(
    page_title="Behaviour Trace — Kayfa",
    page_icon="🔍",
    layout="wide",
)

from datetime import datetime, timedelta

from pathlib import Path
from core.auth import require_auth, require_admin
from core.db import get_behaviour_logs_collection
from sidebar_helper import render_sidebar

LOGO_PATH = Path(__file__).resolve().parent.parent / "logo.png"

require_auth()
require_admin()

render_sidebar()

st.title("🔍 Behaviour Trace")
st.caption("Inspect the agent's step-by-step decision process.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start date",
        value=datetime.now() - timedelta(days=1),
        max_value=datetime.now(),
    )
with col2:
    end_date = st.date_input(
        "End date",
        value=datetime.now(),
        max_value=datetime.now(),
    )

# Search by run_id
run_id_filter = st.text_input("Filter by Run ID (optional)", placeholder="e.g., abc-123...")

step_type_filter = st.selectbox(
    "Filter by step type",
    options=["All", "llm_call", "tool_call", "user_input", "final_response"],
    index=0,
)

# ---------------------------------------------------------------------------
# Fetch behaviour logs
# ---------------------------------------------------------------------------
coll = get_behaviour_logs_collection()

query = {
    "timestamp": {
        "$gte": f"{start_date.isoformat()}T00:00:00",
        "$lte": f"{end_date.isoformat()}T23:59:59",
    }
}
if run_id_filter.strip():
    query["run_id"] = run_id_filter.strip()
if step_type_filter != "All":
    query["step_type"] = step_type_filter

logs = list(coll.find(query).sort("timestamp", -1).limit(500))

st.write(f"**{len(logs)}** behaviour steps found")

if not logs:
    st.info("No behaviour logs match the selected filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Group by run_id for timeline view
# ---------------------------------------------------------------------------
from collections import defaultdict
runs = defaultdict(list)
for log in logs:
    runs[log["run_id"]].append(log)

st.subheader(f"Conversation Runs ({len(runs)} runs)")

for run_id, run_logs in sorted(runs.items(), key=lambda x: x[1][0]["timestamp"], reverse=True):
    run_logs_sorted = sorted(run_logs, key=lambda x: x["timestamp"])

    with st.expander(
        f"🔄 Run: `{run_id[:8]}...` — {run_logs_sorted[0]['timestamp'][:19]} "
        f"({len(run_logs_sorted)} steps)",
        expanded=False,
    ):
        for i, log in enumerate(run_logs_sorted):
            step_type = log.get("step_type", "unknown")
            detail = log.get("detail", {})

            if step_type == "llm_call":
                st.markdown(
                    f"**Step {i+1}:** 🤖 LLM Call — "
                    f"input_tokens={detail.get('input_tokens', '?')}, "
                    f"output_tokens={detail.get('output_tokens', '?')}, "
                    f"cost=${detail.get('cost_usd', 0):.6f}"
                )
                if detail.get("has_tool_calls"):
                    st.markdown("↳ *Decided to call tools*")

            elif step_type == "tool_call":
                st.markdown(
                    f"**Step {i+1}:** 🛠️ Tool Call — `{detail.get('tool_name', '?')}`"
                )
                with st.container():
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Arguments")
                        st.json(detail.get("arguments", {}))
                    with c2:
                        st.caption("Result")
                        st.json(detail.get("result_status", "unknown"))

            elif step_type == "final_response":
                st.markdown(
                    f"**Step {i+1}:** ✅ Final Response — "
                    f"length={detail.get('response_length', '?')}, "
                    f"iterations={detail.get('total_iterations', '?')}, "
                    f"total_cost=${detail.get('total_cost_usd', 0):.6f}"
                )

            elif step_type == "user_input":
                st.markdown(f"**Step {i+1}:** 👤 User Input")
                st.caption(detail.get("message", "")[:200])

            else:
                st.markdown(f"**Step {i+1}:** {step_type}")
                st.json(detail)

            st.divider()

# ---------------------------------------------------------------------------
# Raw logs table (optional)
# ---------------------------------------------------------------------------
st.markdown("---")
if st.checkbox("Show raw logs table"):
    st.subheader("Raw Behaviour Logs")
    log_data = []
    for log in logs[:200]:
        log_data.append({
            "Timestamp": log.get("timestamp", "")[:19],
            "Run ID": log.get("run_id", "")[:8] + "...",
            "Step Type": log.get("step_type", ""),
        })
    st.dataframe(log_data, use_container_width=True, hide_index=True)
