"""
app.py — SupportAI Pro
Real-time query capture — every chat message appears in dashboard.
"""

import time
import io
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="SupportAI Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0f1117;
        padding: 12px 24px;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    .topbar-brand { font-size: 20px; font-weight: 700; color: white; }
    .topbar-sub   { font-size: 12px; color: #9ca3af; margin-top: 2px; }
    .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; margin-right:4px; }
    .badge-faq      { background:#d1fae5; color:#065f46; }
    .badge-ticket   { background:#dbeafe; color:#1e40af; }
    .badge-escalate { background:#fee2e2; color:#991b1b; }
    .badge-chitchat { background:#f3f4f6; color:#374151; }
    .app-header {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        padding: 16px 24px; border-radius: 12px;
        margin-bottom: 20px; color: white;
    }
    .app-header h1 { margin:0; font-size:22px; font-weight:700; }
    .app-header p  { margin:4px 0 0; font-size:13px; opacity:0.85; }
    .dash-header {
        background: linear-gradient(90deg, #0f172a, #1e3a5f);
        padding: 16px 24px; border-radius: 12px;
        margin-bottom: 20px; color: white;
    }
    .dash-header h1 { margin:0; font-size:22px; font-weight:700; }
    .dash-header p  { margin:4px 0 0; font-size:13px; opacity:0.85; }
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    groq_api_key = None

# ── Session state init ────────────────────────────────────────────
if "page"         not in st.session_state: st.session_state["page"]         = "chat"
if "messages"     not in st.session_state: st.session_state["messages"]     = []
if "chat_log"     not in st.session_state: st.session_state["chat_log"]     = []
if "bot"          not in st.session_state: st.session_state["bot"]          = None

# ── Top bar ───────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div>
        <div class="topbar-brand">🤖 SupportAI Pro</div>
        <div class="topbar-sub">LLM-Powered Customer Support Automation</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation ────────────────────────────────────────────────────
col_n1, col_n2, col_n3, col_n4 = st.columns([2, 2, 2, 4])
with col_n1:
    if st.button("💬 Chatbot",
                 use_container_width=True,
                 type="primary" if st.session_state["page"] == "chat" else "secondary"):
        st.session_state["page"] = "chat"
        st.rerun()
with col_n2:
    log_count = len(st.session_state["chat_log"])
    if st.button(f"📊 Dashboard ({log_count} queries)",
                 use_container_width=True,
                 type="primary" if st.session_state["page"] == "dashboard" else "secondary"):
        st.session_state["page"] = "dashboard"
        st.rerun()
with col_n3:
    if not groq_api_key:
        groq_api_key = st.text_input("API Key", type="password",
                                     placeholder="gsk_...",
                                     label_visibility="collapsed")

st.markdown("---")

if not groq_api_key:
    st.warning("⚠️ Please enter your Groq API key above to get started.")
    st.stop()

# ── Initialize bot ────────────────────────────────────────────────
if st.session_state.bot is None:
    from agents import CustomerSupportOrchestrator
    with st.spinner("Initializing AI agent..."):
        st.session_state.bot = CustomerSupportOrchestrator(api_key=groq_api_key)

# ════════════════════════════════════════════════════════════════
#  PAGE 1 — CHATBOT
# ════════════════════════════════════════════════════════════════
if st.session_state["page"] == "chat":

    st.markdown("""
    <div class="app-header">
        <h1>💬 AI Customer Support</h1>
        <p>Powered by LLaMA 3.3 · FAQ answering · Ticket routing · Escalation detection</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick suggestions
    cols = st.columns(5)
    suggestions = [
        ("Cancel subscription", "How do I cancel my subscription?"),
        ("Reset password",      "How do I reset my password?"),
        ("Charged twice!",      "I was charged twice last month."),
        ("App crashing",        "The app keeps crashing on my phone."),
        ("Need manager!",       "I need to speak to a manager NOW!"),
    ]
    for col, (label, full) in zip(cols, suggestions):
        if col.button(label, use_container_width=True, key=f"sug_{label}"):
            st.session_state["pending"] = full

    col_clr1, col_clr2 = st.columns([8, 2])
    with col_clr2:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.bot = None
            st.rerun()

    st.markdown("---")

    # Init welcome message
    if len(st.session_state.messages) == 0:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm your AI support assistant. I can help with **billing**, **technical issues**, **account management**, and more. How can I help you today?",
            "meta": {}
        })

    # Render chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                badge_map = {"FAQ":"badge-faq","TICKET":"badge-ticket","ESCALATE":"badge-escalate","CHITCHAT":"badge-chitchat"}
                badges = "".join([f'<span class="badge {badge_map.get(v,"badge-chitchat")}">{k}: {v}</span>' for k,v in list(msg["meta"].items())[:4]])
                if badges:
                    st.markdown(badges, unsafe_allow_html=True)

    # Handle input
    pending    = st.session_state.pop("pending", None)
    user_input = st.chat_input("Type your message...") or pending

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role":"user","content":user_input,"meta":{}})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                start  = time.time()
                result = st.session_state.bot.respond(user_input)
                elapsed = round(time.time() - start, 3)
            st.markdown(result["reply"])

            meta = {}
            if result.get("intent"):     meta["intent"]   = result["intent"]
            if result.get("ticket_id"):  meta["ticket"]   = result["ticket_id"]
            if result.get("priority"):   meta["priority"] = result["priority"]
            if result.get("department"): meta["dept"]     = result["department"]
            if result.get("ref_id"):     meta["ref"]      = result["ref_id"]

            if meta:
                badge_map = {"FAQ":"badge-faq","TICKET":"badge-ticket","ESCALATE":"badge-escalate","CHITCHAT":"badge-chitchat"}
                badges = "".join([f'<span class="badge {badge_map.get(v,"badge-chitchat")}">{k}: {v}</span>' for k,v in list(meta.items())[:4]])
                st.markdown(badges, unsafe_allow_html=True)

        st.session_state.messages.append({"role":"assistant","content":result["reply"],"meta":meta})

        # ── Save to real-time chat log for dashboard ──────────
        st.session_state["chat_log"].append({
            "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query":       user_input,
            "intent":      result.get("intent", "-"),
            "reply":       result["reply"][:80] + "..." if len(result["reply"]) > 80 else result["reply"],
            "ticket_id":   result.get("ticket_id", "-"),
            "ref_id":      result.get("ref_id", "-"),
            "priority":    result.get("priority", "-"),
            "urgency":     result.get("urgency", "-"),
            "department":  result.get("department", "-"),
            "issue_type":  result.get("issue_type", "-"),
            "summary":     result.get("summary", "-"),
            "resolution":  result.get("estimated_resolution", "-"),
            "action":      result.get("suggested_action", "-"),
            "time_sec":    elapsed,
        })

# ════════════════════════════════════════════════════════════════
#  PAGE 2 — DASHBOARD (real-time from chat log)
# ════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "dashboard":

    st.markdown("""
    <div class="dash-header">
        <h1>📊 Real-Time Analytics Dashboard</h1>
        <p>Live data from actual chat sessions · Updates every time a user sends a message</p>
    </div>
    """, unsafe_allow_html=True)

    log = st.session_state["chat_log"]

    if not log:
        st.info("💬 No chat data yet! Go to the **Chatbot** tab, send some messages, then come back here to see real-time analytics.")
        st.stop()

    COLORS = {
        "FAQ":"#1D9E75","TICKET":"#378ADD","ESCALATE":"#D85A30","CHITCHAT":"#888780",
        "HIGH":"#E24B4A","MEDIUM":"#EF9F27","LOW":"#1D9E75",
        "BILLING":"#534AB7","TECHNICAL":"#378ADD","ACCOUNT":"#1D9E75","GENERAL":"#888780",
    }

    # ── Metric cards ──────────────────────────────────────────
    total         = len(log)
    intent_counts = Counter(r["intent"] for r in log)
    dept_counts   = Counter(r["department"] for r in log if r["department"] not in ["-", None])
    prio_counts   = Counter(r["priority"] for r in log if r["priority"] not in ["-", None])
    avg_time      = round(sum(r["time_sec"] for r in log) / total, 2)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total queries",   total)
    m2.metric("FAQ resolved",    intent_counts.get("FAQ", 0),
              f"{round(intent_counts.get('FAQ',0)/total*100)}% auto")
    m3.metric("Tickets raised",  intent_counts.get("TICKET", 0))
    m4.metric("Escalations",     intent_counts.get("ESCALATE", 0))
    m5.metric("Avg response",    f"{avg_time}s")

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Intent distribution","Ticket priority breakdown","Department routing","Response time per query (sec)"),
        specs=[[{"type":"pie"},{"type":"bar"}],[{"type":"pie"},{"type":"bar"}]],
        vertical_spacing=0.22, horizontal_spacing=0.1
    )

    i_labels = list(intent_counts.keys())
    fig.add_trace(go.Pie(
        labels=i_labels, values=[intent_counts[l] for l in i_labels],
        marker_colors=[COLORS.get(l,"#aaa") for l in i_labels],
        hole=0.45, textinfo="label+percent", showlegend=False
    ), row=1, col=1)

    p_order = ["HIGH","MEDIUM","LOW"]
    fig.add_trace(go.Bar(
        x=p_order, y=[prio_counts.get(p,0) for p in p_order],
        marker_color=[COLORS[p] for p in p_order],
        marker_line_width=0, showlegend=False,
        text=[prio_counts.get(p,0) for p in p_order], textposition="outside"
    ), row=1, col=2)

    d_labels = list(dept_counts.keys())
    fig.add_trace(go.Pie(
        labels=d_labels if d_labels else ["No tickets"],
        values=[dept_counts[l] for l in d_labels] if d_labels else [1],
        marker_colors=[COLORS.get(l,"#aaa") for l in d_labels] if d_labels else ["#aaa"],
        hole=0.45, textinfo="label+percent", showlegend=False
    ), row=2, col=1)

    fig.add_trace(go.Bar(
        x=[r["query"][:20]+"..." for r in log],
        y=[r["time_sec"] for r in log],
        marker_color="#534AB7", marker_line_width=0, showlegend=False,
        text=[f"{r['time_sec']}s" for r in log], textposition="outside"
    ), row=2, col=2)

    fig.update_layout(height=580, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font={"family":"sans-serif","size":13},
        margin=dict(t=60,b=20,l=20,r=20))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Real-time query log table ─────────────────────────────
    st.markdown("### 📋 Live query log")

    df = pd.DataFrame([{
        "Time":        r["timestamp"],
        "Query":       r["query"],
        "Intent":      r["intent"],
        "Department":  r["department"],
        "Priority":    r["priority"],
        "Urgency":     r["urgency"],
        "Issue Type":  r["issue_type"],
        "Summary":     r["summary"],
        "Ticket ID":   r["ticket_id"],
        "Ref ID":      r["ref_id"],
        "Resolution":  r["resolution"],
        "Action":      r["action"],
        "Time (s)":    r["time_sec"],
        "Reply":       r["reply"],
    } for r in log])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📥 Download reports")

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("📥 Query log (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "live_query_log.csv", "text/csv",
            use_container_width=True)
    with dl2:
        summary_df = pd.DataFrame([
            {"Metric":"Total Queries",       "Value":total},
            {"Metric":"FAQ Resolved",        "Value":intent_counts.get("FAQ",0)},
            {"Metric":"Tickets Raised",      "Value":intent_counts.get("TICKET",0)},
            {"Metric":"Escalations",         "Value":intent_counts.get("ESCALATE",0)},
            {"Metric":"Avg Response (s)",    "Value":avg_time},
        ])
        st.download_button("📥 Summary (CSV)",
            summary_df.to_csv(index=False).encode("utf-8"),
            "summary.csv", "text/csv",
            use_container_width=True)
    with dl3:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer,         sheet_name="Live Query Log", index=False)
            summary_df.to_excel(writer, sheet_name="Summary",        index=False)
        buf.seek(0)
        st.download_button("📥 Full report (Excel)", buf,
            "live_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    if st.button("🗑️ Clear all data", type="secondary"):
        st.session_state["chat_log"] = []
        st.rerun()
