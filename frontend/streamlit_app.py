import datetime
from contextlib import contextmanager
import streamlit as st
from pathlib import Path
import sys

# Ensure root directory in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, Base, engine

# Ensure db_context is always available even if Streamlit cached an older app.database module in memory
try:
    from app.database import db_context
except ImportError:
    @contextmanager
    def db_context():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

from app.rag.seed_kb import seed_database
from app.rag.retriever import get_retriever
from app.services import case_service
from app.services.issue_service import classify_civic_issue, needs_clarification, CLARIFYING_QUESTIONS

# Ensure DB & KB are initialized
Base.metadata.create_all(bind=engine)
try:
    seed_database()
except Exception:
    pass

st.set_page_config(
    page_title="Civic RTI & First Appeal Drafter",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# 🎨 LUXURY CIVIC DESIGN SYSTEM (Adaptive Light & Dark Contrast)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    :root {
        --font-sans: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --bg-canvas: #F8FAFC;
        --bg-surface: #FFFFFF;
        --text-primary: #0F172A;
        --text-secondary: #475569;
        --text-muted: #64748B;
        --border-subtle: #E2E8F0;
        --border-focus: #2563EB;
        --brand-blue: #2563EB;
        --brand-blue-hover: #1D4ED8;
    }

    html, body, [class*="css"] {
        font-family: var(--font-sans) !important;
        -webkit-font-smoothing: antialiased;
    }
    
    /* Main Canvas Background */
    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #0B132B 0%, #1C2541 55%, #1E3A8A 100%);
        border-radius: 16px;
        padding: 2.2rem 2.4rem;
        margin-bottom: 1.8rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25), 0 8px 10px -6px rgba(15, 23, 42, 0.15);
        position: relative;
        overflow: hidden;
    }
    .hero-container::after {
        content: "";
        position: absolute;
        top: -40%;
        right: -15%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(255,255,255,0) 70%);
        pointer-events: none;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(37, 99, 235, 0.2);
        color: #93C5FD !important;
        border: 1px solid rgba(147, 197, 253, 0.35);
        backdrop-filter: blur(8px);
        border-radius: 9999px;
        padding: 0.28rem 0.85rem;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.85rem;
    }
    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 0.45rem;
        letter-spacing: -0.025em;
        line-height: 1.2;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .hero-subtitle {
        font-size: 1.02rem;
        color: #94A3B8 !important;
        line-height: 1.55;
        max-width: 840px;
        margin-bottom: 0;
    }

    /* Executive Stat Card */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.2rem 1.35rem;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 18px -4px rgba(15, 23, 42, 0.08);
        border-color: #CBD5E1;
    }
    .stat-label {
        font-size: 0.76rem;
        font-weight: 700;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .stat-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A !important;
        line-height: 1.1;
        letter-spacing: -0.025em;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.32rem 0.8rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        transition: all 0.15s ease;
    }
    .badge-classified { background-color: #EFF6FF !important; color: #1D4ED8 !important; border: 1px solid #BFDBFE !important; }
    .badge-clarification { background-color: #FFFBEB !important; color: #B45309 !important; border: 1px solid #FDE68A !important; }
    .badge-ready { background-color: #EEF2FF !important; color: #4338CA !important; border: 1px solid #C7D2FE !important; }
    .badge-approved { background-color: #ECFDF5 !important; color: #047857 !important; border: 1px solid #A7F3D0 !important; }
    .badge-submitted { background-color: #F0F9FF !important; color: #0284C7 !important; border: 1px solid #BAE6FD !important; }
    .badge-overdue { background-color: #FEF2F2 !important; color: #DC2626 !important; border: 1px solid #FECACA !important; animation: pulse 2s infinite; }
    .badge-appeal { background-color: #F5F3FF !important; color: #7C3AED !important; border: 1px solid #DDD6FE !important; }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.78; }
    }

    /* Modern Minimal Civic Card */
    .civic-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1.25rem 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        transition: border-color 0.2s ease;
    }
    .civic-card:hover {
        border-color: #CBD5E1 !important;
    }
    .civic-card h4 {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 1.08rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.01em;
    }
    .civic-card p, .civic-card li {
        color: #334155 !important;
        font-size: 0.94rem !important;
        line-height: 1.55 !important;
    }

    /* Citation Card */
    .citation-card {
        background: #F0FDF4 !important;
        border: 1px solid #BBF7D0 !important;
        border-left: 4px solid #10B981 !important;
        border-radius: 10px !important;
        padding: 0.95rem 1.2rem !important;
        margin-top: 0.6rem !important;
        color: #14532D !important;
        font-size: 0.92rem !important;
    }
    .citation-card strong {
        color: #166534 !important;
        font-weight: 700;
    }
    .citation-card em {
        color: #15803D !important;
    }

    /* Timeline Nodes */
    .timeline-node {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 3.5px solid #2563EB !important;
        padding: 0.8rem 1.1rem !important;
        margin-bottom: 0.5rem !important;
        border-radius: 0 8px 8px 0 !important;
        color: #1E293B !important;
        font-size: 0.92rem !important;
    }
    .timeline-node strong {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    .timeline-node code {
        background: #F1F5F9 !important;
        color: #0F172A !important;
        padding: 0.15rem 0.45rem !important;
        border-radius: 4px !important;
        font-family: var(--font-mono) !important;
        font-size: 0.82rem !important;
        border: 1px solid #E2E8F0 !important;
    }

    /* Document Viewer Container */
    .document-preview-box {
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 2.2rem 2.5rem !important;
        color: #0F172A !important;
        line-height: 1.7 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.02) !important;
        margin: 1.2rem 0 !important;
    }
    .document-ribbon {
        display: inline-block;
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        color: #475569;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        margin-bottom: 1.2rem;
    }
    .document-preview-box h1, .document-preview-box h2, .document-preview-box h3, .document-preview-box h4 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }
    .document-preview-box hr {
        border-color: #E2E8F0 !important;
        margin: 1.2rem 0 !important;
    }
    .document-preview-box blockquote {
        background: #F8FAFC !important;
        border-left: 4px solid #64748B !important;
        margin: 0.8rem 0 !important;
        padding: 0.6rem 1.1rem !important;
        color: #1E293B !important;
        border-radius: 0 6px 6px 0 !important;
    }

    /* Disclaimer Card */
    .disclaimer-card {
        background: #FFFBEB !important;
        border: 1px solid #FDE68A !important;
        border-left: 4px solid #D97706 !important;
        padding: 1.05rem 1.25rem !important;
        font-size: 0.9rem !important;
        color: #78350F !important;
        border-radius: 10px !important;
        margin-top: 2rem !important;
    }
    .disclaimer-card strong {
        color: #92400E !important;
    }

    /* Streamlit Tab Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 9px 16px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #64748B;
        border: none;
        background-color: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        background-color: #EFF6FF !important;
        border-bottom: 2.5px solid #2563EB !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #1D4ED8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.25) !important;
        transform: translateY(-1px) !important;
    }

    /* Sidebar Polish */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    .sidebar-ref-pill {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.42rem 0.7rem;
        margin-bottom: 0.4rem;
        border-radius: 6px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        font-size: 0.83rem;
        color: #1E293B;
        line-height: 1.4;
    }
    .sidebar-ref-pill strong {
        color: #2563EB;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "active_case_id" not in st.session_state:
    st.session_state.active_case_id = None


def render_status_badge(status: str) -> str:
    status_lower = (status or "").lower()
    if "clarification" in status_lower:
        cls = "badge-clarification"
        icon = "⚠️"
    elif "classified" in status_lower or "matched" in status_lower:
        cls = "badge-classified"
        icon = "🏷️"
    elif "draft_ready" in status_lower:
        cls = "badge-ready"
        icon = "📄"
    elif "approved" in status_lower:
        cls = "badge-approved"
        icon = "✅"
    elif "submitted" in status_lower or "awaiting" in status_lower:
        cls = "badge-submitted"
        icon = "📬"
    elif "overdue" in status_lower:
        cls = "badge-overdue"
        icon = "🚨"
    elif "appeal" in status_lower:
        cls = "badge-appeal"
        icon = "⚖️"
    else:
        cls = "badge-classified"
        icon = "📌"
    return f'<span class="status-badge {cls}">{icon} {status}</span>'


# Sidebar: Case Navigator & Legal Quick Reference
with st.sidebar:
    st.markdown("### 🏛️ Civic RTI Drafter")
    st.caption("Deterministic & Local-First Civic Legal Engine")

    with db_context() as db:
        cases_list = case_service.list_cases(db)

    case_options = {c["id"]: f"{c['id'][:8]}... | {c['city'] or 'National'} | {c['issue_type']} ({c['status']})" for c in cases_list}

    st.markdown("#### 📁 Active Case Selector")
    if case_options:
        selected_id = st.selectbox(
            "Choose a case to inspect or progress:",
            options=list(case_options.keys()),
            format_func=lambda x: case_options[x],
            index=list(case_options.keys()).index(st.session_state.active_case_id) if st.session_state.active_case_id in case_options else 0,
        )
        st.session_state.active_case_id = selected_id
    else:
        st.info("No cases created yet. Begin in Tab 1!")

    st.divider()
    st.markdown("#### 📜 Statutory Quick Reference")
    st.markdown("""
    <div class="sidebar-ref-pill">📑 <div><strong>Sec 6(1):</strong> Right to request official records</div></div>
    <div class="sidebar-ref-pill">🚫 <div><strong>Sec 6(2):</strong> No reason required for seeking records</div></div>
    <div class="sidebar-ref-pill">🔄 <div><strong>Sec 6(3):</strong> Mandatory 5-day transfer to authority</div></div>
    <div class="sidebar-ref-pill">⏱️ <div><strong>Sec 7(1):</strong> Strict 30-day response mandate</div></div>
    <div class="sidebar-ref-pill">🎁 <div><strong>Sec 7(6):</strong> Information <b>FREE</b> after 30-day delay</div></div>
    <div class="sidebar-ref-pill">⚖️ <div><strong>Sec 19(1):</strong> Statutory First Appeal for non-response</div></div>
    <div class="sidebar-ref-pill">🏛️ <div><strong>Sec 19(3):</strong> Second Appeal to Information Commission</div></div>
    <div class="sidebar-ref-pill">🔨 <div><strong>Sec 20(1):</strong> ₹250/day personal penalty on PIO</div></div>
    """, unsafe_allow_html=True)


# Hero Header Section
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">⚡ 100% Deterministic & Local-First Legal Engine</div>
    <div class="hero-title">🏛️ Civic RTI & First Appeal Drafter</div>
    <div class="hero-subtitle">
        Transform everyday civic grievances into legally binding Right to Information applications and First Appeals with strict statutory 30-day deadline countdowns.
    </div>
</div>
""", unsafe_allow_html=True)

# Top Metrics Row
with db_context() as db:
    stats = case_service.get_system_stats(db)

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">📁 Total Cases</div>
        <div class="stat-value">{stats['total_cases']}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    awaiting_count = stats["status_counts"].get("SUBMITTED", 0) + stats["status_counts"].get("AWAITING_RESPONSE", 0)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">⏳ Awaiting Response</div>
        <div class="stat-value">{awaiting_count}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    overdue_count = stats["status_counts"].get("OVERDUE", 0)
    st.markdown(f"""
    <div class="stat-card" style="border-left: 4px solid #EF4444;">
        <div class="stat-label" style="color: #DC2626 !important;">🚨 Overdue Cases</div>
        <div class="stat-value" style="color: #DC2626 !important;">{overdue_count}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    appeal_count = stats["status_counts"].get("FIRST_APPEAL_READY", 0)
    st.markdown(f"""
    <div class="stat-card" style="border-left: 4px solid #8B5CF6;">
        <div class="stat-label" style="color: #7C3AED !important;">⚖️ Appeals Prepared</div>
        <div class="stat-value" style="color: #7C3AED !important;">{appeal_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Main Workspace Tabs
tabs = st.tabs([
    "1. 📝 Intake & Classification",
    "2. 📄 RTI Draft & Fee",
    "3. 📅 Submission & Deadlines",
    "4. ⚖️ First Appeal (Overdue)",
    "5. 📊 Case Tracker & Audit Log",
    "6. 🔍 Legal Knowledge Base",
])

# ----------------- TAB 1: INTAKE & CLASSIFICATION -----------------
with tabs[0]:
    st.subheader("Step 1: Describe the Civic Grievance")
    st.caption("Enter details of the local municipal grievance. The engine deterministically classifies the issue, resolves the authority, and calculates prescribed fees.")

    col1, col2 = st.columns([2, 1])
    with col1:
        user_text = st.text_area(
            "Grievance Description (Location, problem, duration):",
            placeholder="e.g., Hazardous open potholes on main link road near station causing traffic jams and bike accidents for over two weeks.",
            height=130,
        )
        
        # Real-time keyword analysis preview
        if user_text.strip():
            preview_class = classify_civic_issue(user_text)
            preview_questions = needs_clarification(user_text)
            st.info(f"🔍 **Auto-Detected Category:** `{preview_class['issue_type']}` | Matched Keyword: `{preview_class['matched_keyword'] or 'None'}`")
            if preview_questions:
                st.warning(f"⚠️ Description is brief ({len(user_text.split())} words). Please consider adding landmark details.")

    with col2:
        city_option = st.selectbox(
            "Select City (for municipal routing & state fees):",
            ["Delhi", "Bengaluru", "Pune", "Hyderabad", "Other / Custom City"],
        )
        custom_city = ""
        if city_option == "Other / Custom City":
            custom_city = st.text_input("Enter custom city name:", placeholder="e.g., Mumbai, Kolkata, Chennai")
        
        final_city = custom_city.strip() if city_option == "Other / Custom City" else city_option

    if st.button("🚀 Create Case & Classify", type="primary", key="btn_create_case"):
        if not user_text.strip():
            st.error("Please enter a description of the civic grievance.")
        else:
            with db_context() as db:
                new_case, questions = case_service.create_case(db, user_text=user_text.strip(), city=final_city)
                st.session_state.active_case_id = new_case.id
            st.success(f"Case `{new_case.id}` successfully initialized and classified!")
            st.rerun()

    # Active Case Summary Card
    if st.session_state.active_case_id:
        with db_context() as db:
            case_data = case_service.get_case_detail(db, st.session_state.active_case_id)

        if case_data:
            st.divider()
            st.markdown(f"### 📋 Active Case Overview: `{case_data['id'][:8]}...`")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Current Status:**<br>{render_status_badge(case_data['status'])}", unsafe_allow_html=True)
            c2.markdown(f"**Issue Category:**<br>`{case_data['issue_type']}`", unsafe_allow_html=True)
            c3.markdown(f"**Department:**<br>`{case_data['department']}`", unsafe_allow_html=True)
            c4.markdown(f"**Public Authority:**<br>`{case_data['municipal_body']}`", unsafe_allow_html=True)

            if case_data["status"] == "NEEDS_CLARIFICATION":
                st.warning("⚠️ Description is brief. For maximum legal effectiveness, consider clarifying:")
                for q in CLARIFYING_QUESTIONS:
                    st.markdown(f"- ❓ {q}")

# ----------------- TAB 2: RTI DRAFT & FEE -----------------
with tabs[1]:
    st.subheader("Step 2: Generate & Review RTI Application")
    st.caption("Generate a structured, legally grounded RTI application under Section 6(1) with mandatory Section 6(3) transfer demands.")

    if not st.session_state.active_case_id:
        st.info("Please create or select a case first from Tab 1 or the sidebar.")
    else:
        with db_context() as db:
            case_data = case_service.get_case_detail(db, st.session_state.active_case_id)

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.button("⚡ Generate / Regenerate RTI Draft", key="btn_gen_draft", type="primary"):
                with db_context() as db:
                    case, draft_res = case_service.generate_and_save_draft(db, st.session_state.active_case_id)
                st.success("RTI Draft generated with statutory citations!")
                st.rerun()

        with col_act2:
            if case_data and case_data["status"] in ("DRAFT_READY", "USER_APPROVED"):
                if st.button("✅ Approve Draft for Filing", key="btn_app_draft"):
                    with db_context() as db:
                        case_service.approve_draft(db, st.session_state.active_case_id)
                    st.success("Draft approved! Proceed to Step 3 after filing.")
                    st.rerun()

        if case_data and case_data.get("draft_markdown"):
            st.divider()
            
            # Fee & Legal Citations Cards
            col_fee, col_cite = st.columns([1, 1])
            with col_fee:
                fee_info = case_data.get("fee_json") or {}
                st.markdown(f"""
                <div class="civic-card">
                    <h4>💰 Prescribed Application Fee: ₹{fee_info.get('amount', 10)} ({fee_info.get('currency', 'INR')})</h4>
                    <p>{fee_info.get('notes', 'Standard statutory application fee.')}</p>
                </div>
                """, unsafe_allow_html=True)
                if fee_info.get("citation"):
                    c = fee_info["citation"]
                    st.markdown(f"""
                    <div class="citation-card">
                        <strong>📌 Fee Rule:</strong> {c.get('source')} — <em>{c.get('section')}</em>: {c.get('title')}
                    </div>
                    """, unsafe_allow_html=True)

            with col_cite:
                st.markdown("""
                <div class="civic-card">
                    <h4>📜 Legal Provisions Grounding this Draft</h4>
                    <ul>
                        <li><strong>Section 6(1):</strong> Right of citizen to request certified official records</li>
                        <li><strong>Section 6(3):</strong> Mandatory 5-day transfer if filed with wrong department</li>
                        <li><strong>Section 7(1):</strong> 30-day statutory response mandate on PIO</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 📄 Generated RTI Application Document")
            st.markdown('<div class="document-ribbon">🏛️ Official Statutory RTI Draft • Section 6(1)</div>', unsafe_allow_html=True)
            st.markdown(case_data["draft_markdown"])
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📥 Download RTI Draft (.md)",
                    data=case_data["draft_markdown"],
                    file_name=f"RTI_Application_{case_data['id'][:8]}.md",
                    mime="text/markdown",
                    key="dl_rti_md",
                )
            with col_d2:
                st.download_button(
                    label="📥 Download Plain Text (.txt)",
                    data=case_data["draft_markdown"],
                    file_name=f"RTI_Application_{case_data['id'][:8]}.txt",
                    mime="text/plain",
                    key="dl_rti_txt",
                )

# ----------------- TAB 3: SUBMISSION & DEADLINES -----------------
with tabs[2]:
    st.subheader("Step 3: Record Submission & Track Statutory Deadlines")
    st.caption("Track the exact 30-day response window under Section 7(1) computed with pure calendar date arithmetic.")

    if not st.session_state.active_case_id:
        st.info("Please select a case first.")
    else:
        with db_context() as db:
            case_data = case_service.get_case_detail(db, st.session_state.active_case_id)

        col_sub1, col_sub2 = st.columns([1, 1])
        with col_sub1:
            sub_date = st.date_input("Actual Date of RTI Submission / Post:", value=datetime.date.today())
            if st.button("📬 Record Submission & Start 30-Day Clock", type="primary", key="btn_submit_case"):
                with db_context() as db:
                    case = case_service.submit_case(db, st.session_state.active_case_id, submitted_on=sub_date.isoformat())
                st.success("Submission recorded! Statutory deadlines calculated.")
                st.rerun()

        if case_data and case_data.get("submission_date"):
            st.divider()
            st.markdown("### ⏱️ Statutory Countdown Matrix")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">📬 Submitted On</div>
                    <div class="stat-value" style="font-size: 1.3rem;">{case_data['submission_date']}</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="stat-card" style="border-left: 4px solid #3B82F6;">
                    <div class="stat-label">⏱️ Response Due Date</div>
                    <div class="stat-value" style="font-size: 1.3rem; color:#1D4ED8 !important;">{case_data['response_due_date']}</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="stat-card" style="border-left: 4px solid #EF4444;">
                    <div class="stat-label">⚠️ Overdue From</div>
                    <div class="stat-value" style="font-size: 1.3rem; color:#B91C1C !important;">{case_data['overdue_from']}</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="stat-card" style="border-left: 4px solid #8B5CF6;">
                    <div class="stat-label">⚖️ Appeal File By</div>
                    <div class="stat-value" style="font-size: 1.3rem; color:#6D28D9 !important;">{case_data['appeal_file_by']}</div>
                </div>
                """, unsafe_allow_html=True)

            # Calculation & Overdue Banner
            today = datetime.date.today()
            due_d = datetime.date.fromisoformat(case_data["response_due_date"])
            
            st.write("")
            if today > due_d:
                overdue_days = (today - due_d).days
                st.error(f"🚨 **CASE IS OVERDUE BY {overdue_days} DAYS!** The Public Authority failed to respond within the statutory 30 days under Section 7(1). You are legally entitled to file a First Appeal in Step 4.")
            else:
                remaining = (due_d - today).days
                st.info(f"⏳ **Awaiting Response:** {remaining} days remaining before statutory deadline of `{case_data['response_due_date']}`.")

            # Timeline Breakdown
            st.markdown("#### ⏳ Statutory Milestone Sequence")
            st.markdown(f"""
            - 📬 **Submission:** `{case_data['submission_date']}` — RTI Application filed with PIO
            - ⏱️ **30-Day Mandatory Window:** Under Section 7(1), PIO must respond by `{case_data['response_due_date']}`
            - ⚠️ **Statutory Overdue Date:** Non-compliance begins on `{case_data['overdue_from']}`
            - ⚖️ **First Appeal Filing Window:** Section 19(1) First Appeal valid until `{case_data['appeal_file_by']}`
            """)

# ----------------- TAB 4: FIRST APPEAL (OVERDUE) -----------------
with tabs[3]:
    st.subheader("Step 4: Statutory First Appeal Drafting")
    st.caption("When the PIO fails to respond within 30 days, generate a First Appeal under Section 19(1) demanding records FREE OF COST under Section 7(6).")

    if not st.session_state.active_case_id:
        st.info("Please select a case first.")
    else:
        with db_context() as db:
            case_data = case_service.get_case_detail(db, st.session_state.active_case_id)

        if not case_data.get("submission_date"):
            st.warning("⚠️ This case has not been marked as submitted yet. Please record the submission date in Step 3.")
        else:
            col_eval1, col_eval2 = st.columns([1, 1])
            with col_eval1:
                as_of_date = st.date_input("Evaluation Date (as of):", value=datetime.date.today(), key="appeal_as_of")
            
            with col_eval2:
                st.write("")
                st.write("")
                if st.button("⚖️ Generate First Appeal", type="primary", key="btn_gen_appeal"):
                    try:
                        with db_context() as db:
                            case, appeal_res = case_service.generate_and_save_appeal(
                                db, st.session_state.active_case_id, as_of=as_of_date.isoformat()
                            )
                        st.success(f"First Appeal generated! Overdue by {appeal_res['days_overdue']} days.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

            if case_data.get("appeal_markdown"):
                st.divider()
                st.markdown("### ⚖️ Generated First Appeal Document")
                st.markdown('<div class="document-ribbon" style="background:#F5F3FF; border-color:#DDD6FE; color:#7C3AED;">⚖️ Statutory First Appeal • Section 19(1) RTI Act</div>', unsafe_allow_html=True)
                st.markdown(case_data["appeal_markdown"])
                
                col_ap1, col_ap2 = st.columns(2)
                with col_ap1:
                    st.download_button(
                        label="📥 Download First Appeal (.md)",
                        data=case_data["appeal_markdown"],
                        file_name=f"First_Appeal_{case_data['id'][:8]}.md",
                        mime="text/markdown",
                        key="dl_appeal_md",
                    )
                with col_ap2:
                    st.download_button(
                        label="📥 Download Plain Text (.txt)",
                        data=case_data["appeal_markdown"],
                        file_name=f"First_Appeal_{case_data['id'][:8]}.txt",
                        mime="text/plain",
                        key="dl_appeal_txt",
                    )

# ----------------- TAB 5: CASE TRACKER & AUDIT LOG -----------------
with tabs[4]:
    st.subheader("Step 5: Case Tracker & Audit Timeline")
    st.caption("Monitor all recorded civic cases and inspect chronological audit event logs.")

    with db_context() as db:
        all_cases = case_service.list_cases(db)

    # Filter controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All Statuses", "ISSUE_CLASSIFIED", "NEEDS_CLARIFICATION", "DRAFT_READY", "USER_APPROVED", "SUBMITTED", "OVERDUE", "FIRST_APPEAL_READY"],
        )
    with col_f2:
        search_query = st.text_input("Search cases by text or city:", placeholder="e.g., Delhi, pothole, garbage")

    filtered_cases = all_cases
    if status_filter != "All Statuses":
        filtered_cases = [c for c in filtered_cases if c["status"] == status_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_cases = [c for c in filtered_cases if q in c["user_text"].lower() or q in (c.get("city") or "").lower()]

    if not filtered_cases:
        st.info("No matching cases found.")
    else:
        for c in filtered_cases:
            with st.expander(f"📁 Case `{c['id'][:8]}...` | {c['city'] or 'National'} | {c['department']} ({c['status']})"):
                col_c1, col_c2, col_c3 = st.columns(3)
                col_c1.write(f"**Category:** `{c['issue_type']}`")
                col_c2.write(f"**Authority:** `{c['municipal_body']}`")
                col_c3.markdown(f"**Status:** {render_status_badge(c['status'])}", unsafe_allow_html=True)
                
                st.write(f"**Grievance:** {c['user_text']}")
                if c.get("submission_date"):
                    st.write(f"**Submitted:** `{c['submission_date']}` | **Due:** `{c['response_due_date']}`")
                
                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    if st.button(f"👉 Select Case `{c['id'][:8]}`", key=f"sel_btn_{c['id']}"):
                        st.session_state.active_case_id = c["id"]
                        st.rerun()
                with col_b2:
                    if st.button(f"🗑️ Delete Case `{c['id'][:8]}`", key=f"del_btn_{c['id']}"):
                        with db_context() as db:
                            case_service.delete_case(db, c["id"])
                        if st.session_state.active_case_id == c["id"]:
                            st.session_state.active_case_id = None
                        st.success(f"Case `{c['id'][:8]}` deleted.")
                        st.rerun()

                # Audit Events Timeline (extracted safely inside active session)
                with db_context() as db:
                    raw_events = case_service.get_case_events(db, c["id"])
                    events_data = []
                    for ev in raw_events:
                        ev_type = str(ev.get("event_type", "EVENT")) if isinstance(ev, dict) else str(getattr(ev, "event_type", "EVENT"))
                        ev_time = str(ev.get("created_at", "")) if isinstance(ev, dict) else str(getattr(ev, "created_at", ""))
                        events_data.append({"event_type": ev_type, "created_at": ev_time})

                if events_data:
                    st.markdown("**Chronological Event Audit Trail:**")
                    for item in events_data:
                        st.markdown(f"""
                        <div class="timeline-node">
                            <strong>{item['event_type']}</strong> — <code>{item['created_at']}</code>
                        </div>
                        """, unsafe_allow_html=True)

# ----------------- TAB 6: LEGAL KNOWLEDGE BASE -----------------
with tabs[5]:
    st.subheader("Step 6: Legal Knowledge Base & Citations Explorer")
    st.caption("Search and explore the indexed statutory provisions of the RTI Act, 2005 and State Rules using BM25 lexical search.")

    retriever = get_retriever()
    
    col_q1, col_q2 = st.columns([2, 1])
    with col_q1:
        search_kw = st.text_input("Search legal chunks via BM25:", placeholder="e.g., fee exemption, first appeal, transfer to authority, penalty")
    with col_q2:
        topic_filter = st.selectbox(
            "Filter by Topic:",
            ["All Topics", "request", "deadline", "transfer", "appeal", "fee", "water", "penalty", "rejection"],
        )

    selected_topic = None if topic_filter == "All Topics" else topic_filter
    if search_kw.strip():
        search_results = retriever.search(query=search_kw.strip(), topic=selected_topic, top_k=10)
    else:
        search_results = retriever.chunks_list
        if selected_topic:
            search_results = [c for c in search_results if c.get("topic", "").lower() == selected_topic.lower()]

    st.markdown(f"**Found {len(search_results)} statutory chunk(s):**")
    for chunk in search_results:
        with st.expander(f"📜 {chunk['act']} — {chunk['section']} ({chunk['title']})"):
            st.markdown(f"**Jurisdiction:** `{chunk['jurisdiction']}` | **Topic:** `{chunk['topic']}` | **ID:** `{chunk['id']}`")
            st.info(chunk["text"])
            st.caption(f"Source: {chunk['source']}")

# Global Statutory Disclaimer Footer
st.markdown("""
<div class="disclaimer-card">
    <strong>⚖️ Statutory Disclaimer:</strong> This application is an automated civic drafting assistant and does not provide formal legal advice. Officer names, designations, and public authority office addresses must be verified independently before physical submission.
</div>
""", unsafe_allow_html=True)
