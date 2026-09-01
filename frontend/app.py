"""GuidelineCheck — RAG-Based Public Health Guidance Assistant (Streamlit UI).

Educational demonstration using synthetic guidance only. Not for clinical,
patient-specific, or real-world operational decisions.
"""
from __future__ import annotations

import html

import streamlit as st

from api_client import APIClientError, GuidelineCheckAPIClient, DEFAULT_BACKEND_URL
from motion_panel import MOTION_PANEL_AVAILABLE, render_motion_panel
from styles import confidence_text, inject_base_css, status_badge_html

st.set_page_config(
    page_title="GuidelineCheck",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css(st)

EXAMPLE_QUESTIONS = [
    "What is the current measles outbreak vaccination protocol?",
    "Which document supersedes the previous measles protocol?",
    "What is the current mpox field guidance?",
]

DISCLAIMER_TEXT = (
    "Educational demonstration using synthetic guidance only. Not for clinical, "
    "patient-specific, or real-world operational decisions."
)


# ----------------------------------------------------------------------------
# Session state setup
# ----------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {question, response} or {question, error}
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "show_documents" not in st.session_state:
    st.session_state.show_documents = False

client = GuidelineCheckAPIClient(base_url=st.session_state.backend_url)


# ----------------------------------------------------------------------------
# Rendering helpers
# ----------------------------------------------------------------------------
def status_filter_value(sel: str) -> str | None:
    return None if sel == "Any" else sel


def render_guidance_banner(response: dict) -> None:
    if response["is_abstention"]:
        st.markdown(
            '<div class="gc-guidance-banner gc-banner-insufficient">'
            '🚫 No sufficient supporting guidance found</div>',
            unsafe_allow_html=True,
        )
    elif response["current_guidance_found"]:
        st.markdown(
            '<div class="gc-guidance-banner gc-banner-current">'
            '✅ Current guidance identified</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="gc-guidance-banner gc-banner-superseded">'
            '⚠️ No current guidance found; showing superseded or historical material</div>',
            unsafe_allow_html=True,
        )


def render_answer_card(response: dict) -> None:
    mode_label = "LLM-generated" if response["generation_mode"] == "llm" else "Extractive (no LLM configured)"
    st.markdown(
        f"""
        <div class="gc-answer-card">
            <div class="gc-answer-text">{html.escape(response['answer_text'])}</div>
            <div class="gc-safety-note">
                {confidence_text(response['confidence_label'])} · Mode: {mode_label}<br/>
                🛈 {html.escape(response['safety_notice'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources(response: dict) -> None:
    citations = response.get("citations", [])
    if not citations:
        return
    st.markdown("**Sources**")
    for c in citations:
        with st.container(border=True):
            top_cols = st.columns([3, 1])
            with top_cols[0]:
                st.markdown(f"**{c['title']}** — v{c['version']} ({c['document_type']})")
                section_suffix = f" · Section: {c['section']}" if c.get("section") else ""
                st.caption(f"Effective: {c['effective_date']}{section_suffix}")
            with top_cols[1]:
                st.markdown(status_badge_html(c["status"]), unsafe_allow_html=True)

            st.caption(f"Why this source: {c['relevance_explanation']}")

            if c["status"] in ("Superseded", "Historical"):
                st.markdown(
                    f'<div class="gc-superseded-warning">⚠️ This source is {c["status"].lower()} '
                    f'and is shown because historical guidance was requested or relevant.</div>',
                    unsafe_allow_html=True,
                )

            with st.expander("Show supporting excerpt", expanded=False):
                st.caption(f"chunk_id: `{c['chunk_id']}`")
                if c.get("source_url"):
                    st.caption(f"Source URL: {c['source_url']}")


def render_diagnostics(response: dict) -> None:
    diag = response.get("retrieval_diagnostics", {})
    with st.expander("Retrieval diagnostics", expanded=False):
        st.json(diag)


def render_response(response: dict, turn_key: str) -> None:
    if MOTION_PANEL_AVAILABLE:
        try:
            render_motion_panel(response, key=f"motion_{turn_key}")
            return
        except Exception:
            # Any failure in the custom component must not break the app —
            # fall through to the plain static Streamlit rendering below.
            pass

    render_guidance_banner(response)
    render_answer_card(response)
    render_sources(response)


def run_query(question: str) -> None:
    try:
        response = client.query(
            question=question,
            top_k=6,
            topic=status_filter_value(st.session_state.get("filter_topic", "Any")),
            document_type=status_filter_value(st.session_state.get("filter_type", "Any")),
            region=status_filter_value(st.session_state.get("filter_region", "Any")),
            status=status_filter_value(st.session_state.get("filter_status", "Any")),
            include_historical=st.session_state.get("include_historical", False),
        )
        st.session_state.chat_history.append({"question": question, "response": response})
    except APIClientError as exc:
        st.session_state.chat_history.append({"question": question, "error": str(exc)})


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
health = None
backend_ok = False
try:
    health = client.health()
    backend_ok = True
except APIClientError:
    backend_ok = False

header_col1, header_col2 = st.columns([3, 2])
with header_col1:
    st.markdown(
        """
        <div class="gc-header">
            <div>
                <span class="gc-wordmark">GuidelineCheck</span>
                <span class="gc-badge">Synthetic Educational Demo</span>
                <div class="gc-subtitle">Current public-health guidance, with traceable sources</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_col2:
    if backend_ok and health:
        chunk_count = health.get("chunk_count", 0)
        doc_count = health.get("document_count", 0)
        st.markdown(
            f'<div style="text-align:right; padding-top:0.75rem;">'
            f'<span class="gc-conn-indicator gc-conn-ok">● Backend connected</span><br/>'
            f'<span style="font-size:0.78rem; color:#5b6570;">Indexed: {doc_count} documents, '
            f'{chunk_count} chunks</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:right; padding-top:0.75rem;">'
            '<span class="gc-conn-indicator gc-conn-bad">● Backend unreachable</span><br/>'
            f'<span style="font-size:0.78rem; color:#5b6570;">Expected at {st.session_state.backend_url}</span>'
            '</div>',
            unsafe_allow_html=True,
        )

st.markdown(f'<div class="gc-disclaimer">⚠️ {DISCLAIMER_TEXT}</div>', unsafe_allow_html=True)

if not MOTION_PANEL_AVAILABLE:
    st.caption(
        "ℹ️ Enhanced motion UI component not built — using standard Streamlit UI. "
        "See frontend_components/guideline_motion_panel/README.md for optional setup."
    )

if not backend_ok:
    st.error(
        "Cannot reach the GuidelineCheck API. Make sure the backend is running "
        "(see README) and, if needed, set the GUIDELINECHECK_API_URL environment variable."
    )
    st.stop()


# ----------------------------------------------------------------------------
# Sidebar: filters, actions, examples
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Search Filters")

    try:
        topics_data = client.get_topics()
    except APIClientError:
        topics_data = {"topics": [], "document_types": [], "regions": [], "statuses": []}

    topic_options = ["Any"] + topics_data.get("topics", [])
    type_options = ["Any"] + topics_data.get("document_types", [])
    region_options = ["Any"] + topics_data.get("regions", [])
    status_options = ["Any"] + topics_data.get("statuses", [])

    st.selectbox("Topic", topic_options, key="filter_topic")
    st.selectbox("Document type", type_options, key="filter_type")
    st.selectbox("Region", region_options, key="filter_region")
    st.selectbox("Guidance status", status_options, key="filter_status")
    st.toggle("Include superseded/historical guidance", value=False, key="include_historical")

    st.markdown("---")

    if st.button("📚 View indexed documents", use_container_width=True):
        st.session_state.show_documents = True
        st.rerun()

    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    with st.expander("⚙️ Admin: (re)run ingestion"):
        st.caption("Development/demo use only.")
        reset_flag = st.checkbox("Reset vector store before ingesting", value=False)
        if st.button("Run ingestion now"):
            with st.spinner("Ingesting documents..."):
                try:
                    summary = client.ingest(reset=reset_flag)
                    st.success(
                        f"Ingested {summary['documents_ingested']} documents, "
                        f"{summary['chunks_created']} chunks created."
                    )
                except APIClientError as exc:
                    st.error(str(exc))

    st.markdown("---")
    st.markdown("### Example Questions")
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if st.button(q, key=f"sidebar_example_{i}", use_container_width=True):
            st.session_state.pending_question = q
            st.session_state.show_documents = False
            st.rerun()


# ----------------------------------------------------------------------------
# Document library view
# ----------------------------------------------------------------------------
if st.session_state.show_documents:
    st.markdown("## 📚 Document Library")
    if st.button("← Back to chat"):
        st.session_state.show_documents = False
        st.rerun()

    try:
        docs_response = client.list_documents()
        documents = docs_response.get("documents", [])
    except APIClientError as exc:
        st.error(str(exc))
        documents = []

    if not documents:
        st.info("No documents indexed yet. Run ingestion from the sidebar (Admin panel).")
    else:
        by_id = {d["document_id"]: d for d in documents}
        for doc in sorted(documents, key=lambda d: (d["topic"], d["title"], d["version"])):
            with st.container(border=True):
                cols = st.columns([3, 1, 1, 1])
                with cols[0]:
                    st.markdown(f"**{doc['title']}** — v{doc['version']}")
                    st.caption(f"{doc['document_type']} · {doc['topic']} · {doc['region']}")
                with cols[1]:
                    st.markdown(status_badge_html(doc["status"]), unsafe_allow_html=True)
                with cols[2]:
                    st.caption(f"Effective: {doc['effective_date']}")
                with cols[3]:
                    st.caption(f"{doc['chunk_count']} chunks")

                if doc.get("supersedes"):
                    prev = by_id.get(doc["supersedes"])
                    prev_title = f"{prev['title']} v{prev['version']}" if prev else doc["supersedes"]
                    st.caption(f"↳ Supersedes: {prev_title}")
                if doc.get("superseded_by"):
                    nxt = by_id.get(doc["superseded_by"])
                    nxt_title = f"{nxt['title']} v{nxt['version']}" if nxt else doc["superseded_by"]
                    st.caption(f"↳ Superseded by: {nxt_title}")
    st.stop()


# ----------------------------------------------------------------------------
# Main content: chat
# ----------------------------------------------------------------------------
st.markdown("## Ask a guidance question")

if not st.session_state.chat_history:
    st.markdown(
        "Ask about current outbreak protocols, vaccination guidance, or operational "
        "procedures. Try one of these to get started:"
    )
    chip_cols = st.columns(len(EXAMPLE_QUESTIONS))
    for i, (col, q) in enumerate(zip(chip_cols, EXAMPLE_QUESTIONS)):
        with col:
            if st.button(q, key=f"main_example_{i}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

# Handle a newly submitted question before rendering history, so it appears
# in the same pass.
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = None
    with st.spinner("Checking current guidance..."):
        run_query(q)

question_input = st.chat_input("Ask about current public-health guidance...")
if question_input:
    with st.spinner("Checking current guidance..."):
        run_query(question_input)

# Render full chat history, oldest first.
for idx, turn in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        if "error" in turn:
            st.error(turn["error"])
        else:
            render_response(turn["response"], turn_key=f"turn_{idx}")
            render_diagnostics(turn["response"])
