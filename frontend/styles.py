"""Custom Streamlit theme CSS and small style helper functions for GuidelineCheck."""
from __future__ import annotations

STATUS_COLORS = {
    "Current": {"bg": "#e6f4ea", "fg": "#1e7a34", "border": "#1e7a34", "icon": "●"},
    "Superseded": {"bg": "#fff4e5", "fg": "#9a6300", "border": "#c68400", "icon": "!"},
    "Historical": {"bg": "#eef0f2", "fg": "#54606b", "border": "#8a97a3", "icon": "◷"},
    "Draft": {"bg": "#eef2ff", "fg": "#3949ab", "border": "#3949ab", "icon": "✎"},
}

CONFIDENCE_COLORS = {
    "High": "#1e7a34",
    "Medium": "#9a6300",
    "Low": "#b3261e",
}

BASE_CSS = """
<style>
:root {
    --gc-bg: #f7f8fa;
    --gc-surface: #ffffff;
    --gc-primary: #0b3d5c;
    --gc-primary-light: #12557e;
    --gc-border: #e1e4e8;
    --gc-text: #1c2530;
    --gc-text-muted: #5b6570;
}

.stApp {
    background-color: var(--gc-bg);
    color: var(--gc-text);
}

.stApp [data-testid="stMarkdownContainer"] {
    color: var(--gc-text);
}
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] span {
    color: var(--gc-text) !important;
}
.stApp [data-testid="stCaptionContainer"] {
    color: var(--gc-text-muted);
}
.stApp [data-testid="stCaptionContainer"] p,
.stApp [data-testid="stCaptionContainer"] span {
    color: var(--gc-text-muted) !important;
}

/* Header / brand */
.gc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0 1.25rem 0;
    border-bottom: 1px solid var(--gc-border);
    margin-bottom: 1.25rem;
}
.gc-wordmark {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--gc-primary);
    letter-spacing: -0.02em;
}
.gc-subtitle {
    font-size: 0.95rem;
    color: var(--gc-text-muted);
    margin-top: -0.15rem;
}
.gc-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #fef3ea;
    color: #b35c00;
    border: 1px solid #f0c797;
    margin-left: 0.5rem;
}
.gc-conn-indicator {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
}
.gc-conn-ok { background: #e6f4ea; color: #1e7a34; border: 1px solid #bfe3c8; }
.gc-conn-bad { background: #fdeaea; color: #b3261e; border: 1px solid #f3bcbc; }

/* Disclaimer banner */
.gc-disclaimer {
    background: #fef8e7;
    border: 1px solid #f2d98a;
    color: #6b5300;
    padding: 0.6rem 0.9rem;
    border-radius: 8px;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}

/* Guidance banner */
.gc-guidance-banner {
    padding: 0.75rem 1rem;
    border-radius: 10px;
    font-weight: 600;
    margin: 0.75rem 0 1rem 0;
    border: 1px solid transparent;
}
.gc-banner-current { background: #e6f4ea; color: #1e7a34; border-color: #bfe3c8; }
.gc-banner-superseded { background: #fff4e5; color: #9a6300; border-color: #f2d190; }
.gc-banner-insufficient { background: #fdeaea; color: #b3261e; border-color: #f3bcbc; }

/* Answer card */
.gc-answer-card {
    background: var(--gc-surface);
    border: 1px solid var(--gc-border);
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.gc-answer-text {
    font-size: 1.02rem;
    line-height: 1.55;
    color: var(--gc-text);
    white-space: pre-wrap;
}
.gc-safety-note {
    margin-top: 0.85rem;
    font-size: 0.8rem;
    color: var(--gc-text-muted);
    border-top: 1px dashed var(--gc-border);
    padding-top: 0.6rem;
}

/* Status badge */
.gc-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    border: 1px solid;
}

/* Source card */
.gc-source-card {
    background: var(--gc-surface);
    border: 1px solid var(--gc-border);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
}
.gc-source-title {
    font-weight: 700;
    color: var(--gc-text);
    font-size: 0.98rem;
}
.gc-source-meta {
    font-size: 0.8rem;
    color: var(--gc-text-muted);
    margin-top: 0.15rem;
}
.gc-source-why {
    font-size: 0.82rem;
    color: var(--gc-text-muted);
    margin-top: 0.4rem;
    font-style: italic;
}
.gc-superseded-warning {
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: #9a6300;
    background: #fff4e5;
    border: 1px solid #f2d190;
    border-radius: 6px;
    padding: 0.4rem 0.6rem;
}

/* Indexed document cards */
.gc-document-card {
    background: var(--gc-surface);
    border: 1px solid var(--gc-border);
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin: 0 0 0.75rem 0;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.gc-document-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
}
.gc-document-title {
    color: var(--gc-text);
    font-size: 1rem;
    font-weight: 750;
    line-height: 1.35;
}
.gc-document-version {
    color: var(--gc-text-muted);
    font-weight: 600;
}
.gc-document-meta {
    color: var(--gc-text-muted);
    font-size: 0.82rem;
    line-height: 1.45;
    margin-top: 0.25rem;
}
.gc-document-details {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.55rem 1rem;
    border-top: 1px solid var(--gc-border);
    margin-top: 0.85rem;
    padding-top: 0.75rem;
}
.gc-document-detail-label {
    color: var(--gc-text-muted);
    display: block;
    font-size: 0.72rem;
    font-weight: 650;
    text-transform: uppercase;
}
.gc-document-detail-value {
    color: var(--gc-text);
    display: block;
    font-size: 0.85rem;
    margin-top: 0.1rem;
}
.gc-document-relation {
    border-top: 1px dashed var(--gc-border);
    color: var(--gc-text-muted);
    font-size: 0.8rem;
    margin-top: 0.7rem;
    padding-top: 0.55rem;
}
@media (max-width: 640px) {
    .gc-document-card-header {
        align-items: flex-start;
        flex-direction: column;
        gap: 0.55rem;
    }
}

/* Example chips */
.gc-chip-btn button {
    border-radius: 999px !important;
}

/* Reduce default streamlit top padding a bit */
.block-container {
    padding-top: 1.4rem;
}
</style>
"""


def inject_base_css(st) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    colors = STATUS_COLORS.get(status, STATUS_COLORS["Historical"])
    return (
        f'<span class="gc-status-badge" style="background:{colors["bg"]};'
        f'color:{colors["fg"]};border-color:{colors["border"]};">'
        f'{colors["icon"]} {status}</span>'
    )


def confidence_text(label: str) -> str:
    color = CONFIDENCE_COLORS.get(label, "#5b6570")
    return f'<span style="color:{color}; font-weight:700;">{label} confidence</span>'
