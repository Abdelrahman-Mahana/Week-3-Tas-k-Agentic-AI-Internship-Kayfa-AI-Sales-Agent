"""
Page 1 — Chat Agent (Part 1)

The main visitor-facing page. Any authenticated user can chat with the sales agent.
The agent uses RAG + tool-calling to answer questions about Kayfa and can create lead tickets.
"""

import streamlit as st

st.set_page_config(
    page_title="Chat Agent — Kayfa",
    page_icon="💬",
    layout="wide",
)

from pathlib import Path
import streamlit.components.v1 as components
from core.auth import require_auth, get_current_user
from agent.graph import run_agent
from sidebar_helper import render_sidebar

LOGO_PATH = Path(__file__).resolve().parent.parent / "logo.png"

require_auth()

user = get_current_user()
username = user["username"]

# ---------------------------------------------------------------------------
# Custom UI Styling and Dynamic RTL/LTR Script Injection
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ============================================================
       1. FONTS — Arabic (Cairo 300–700) + English (Plus Jakarta Sans 300–700)
       ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    :root {
        /* Font stacks */
        --font-stack: 'Plus Jakarta Sans', 'Cairo', 'Segoe UI', Tahoma, sans-serif;
        --font-ar: 'Cairo', 'Plus Jakarta Sans', 'Segoe UI', Tahoma, sans-serif;
        --font-en: 'Plus Jakarta Sans', 'Cairo', 'Segoe UI', Tahoma, sans-serif;

        /* Primary palette — royal blue & indigo */
        --color-primary: #2563eb;
        --color-primary-light: #60a5fa;
        --color-primary-dark: #1d4ed8;
        --color-primary-glow: rgba(37, 99, 235, 0.12);
        --color-primary-glow-strong: rgba(37, 99, 235, 0.22);

        /* User bubble — soft blue tint */
        --color-user-bg: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        --color-user-bg-solid: #eff6ff;
        --color-user-border: #bfdbfe;
        --color-user-accent: #2563eb;

        /* Assistant bubble — warm neutral */
        --color-assistant-bg: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        --color-assistant-bg-solid: #f8fafc;
        --color-assistant-border: #e2e8f0;
        --color-assistant-accent: #3b82f6;

        /* Text & surface */
        --color-text-primary: #0f172a;
        --color-text-secondary: #334155;
        --color-text-muted: #64748b;
        --color-text-on-primary: #ffffff;
        --color-surface: #ffffff;
        --color-surface-hover: #f8fafc;
        --color-divider: rgba(0, 0, 0, 0.05);
        --color-page-bg: #f8fafc;

        /* Radii */
        --radius-bubble: 16px;
        --radius-input: 12px;
        --radius-card: 14px;

        /* Shadows */
        --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.02);
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.01);
        --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.04), 0 2px 4px rgba(0, 0, 0, 0.02);
        --shadow-lg: 0 12px 28px rgba(0, 0, 0, 0.06), 0 4px 8px rgba(0, 0, 0, 0.03);
        --shadow-glow: 0 0 20px var(--color-primary-glow);

        /* Transitions */
        --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-smooth: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-spring: 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    /* Page-level font baseline */
    .stApp, .stApp [data-testid="stHeader"] {
        font-family: var(--font-stack) !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        background-color: #f8fafc !important;
    }

    /* ============================================================
       2. CHAT BUBBLES — Premium, distinct styling
       ============================================================ */
    [data-testid="stChatMessage"] {
        border-radius: var(--radius-bubble) !important;
        margin-bottom: 16px !important;
        padding: 16px 20px !important;
        box-shadow: var(--shadow-sm) !important;
        transition: box-shadow var(--transition-fast),
                    border-color var(--transition-fast),
                    transform var(--transition-fast) !important;
        max-width: 82% !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        position: relative !important;
        animation: bubbleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both !important;
    }

    @keyframes bubbleIn {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.97);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    [data-testid="stChatMessage"]:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }

    /* ---- User bubbles ---- */
    [data-testid="stChatMessage"][data-testid-type="user"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: var(--color-user-bg) !important;
        border: 1px solid var(--color-user-border) !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        border-bottom-right-radius: 4px !important;
    }

    [data-testid="stChatMessage"][data-testid-type="user"]:hover,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]):hover {
        border-color: var(--color-user-accent) !important;
        box-shadow: var(--shadow-md), 0 0 0 1px var(--color-primary-glow) !important;
    }

    /* ---- Assistant bubbles ---- */
    [data-testid="stChatMessage"][data-testid-type="assistant"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: var(--color-assistant-bg) !important;
        border: 1px solid var(--color-assistant-border) !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        border-bottom-left-radius: 4px !important;
    }

    [data-testid="stChatMessage"][data-testid-type="assistant"]:hover,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]):hover {
        border-color: var(--color-assistant-accent) !important;
    }

    /* Avatar styling */
    [data-testid="stChatMessage"] [data-testid*="chatAvatarIcon"] {
        border-radius: 50% !important;
        box-shadow: var(--shadow-xs) !important;
    }

    /* ============================================================
       3. BIDI TEXT — Automatic direction per paragraph
       ============================================================ */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h5,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h6,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div {
        unicode-bidi: plaintext !important;
        direction: inherit !important;
        text-align: start !important;
        font-family: var(--font-stack) !important;
        line-height: 1.8 !important;
        letter-spacing: 0.01em !important;
        color: var(--color-text-primary) !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        hyphens: none !important;
        -webkit-hyphens: none !important;
        -ms-hyphens: none !important;
        white-space: pre-wrap !important;
    }

    /* Markdown container itself */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        unicode-bidi: plaintext !important;
        text-align: start !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    /* BDI Isolation elements styling for inline language switches */
    [data-testid="stChatMessage"] bdi {
        font-family: inherit;
        line-height: inherit;
        unicode-bidi: isolate !important;
    }
    [data-testid="stChatMessage"] bdi[lang="ar"] {
        font-family: var(--font-ar) !important;
    }
    [data-testid="stChatMessage"] bdi[lang="en"] {
        font-family: var(--font-en) !important;
    }

    /* ── Arabic-specific tuning (RTL context) ── */
    [data-testid="stChatMessage"] [dir="rtl"] p,
    [data-testid="stChatMessage"] [dir="rtl"] li,
    [data-testid="stChatMessage"] [dir="rtl"] span,
    [data-testid="stChatMessage"] [dir="rtl"] h1,
    [data-testid="stChatMessage"] [dir="rtl"] h2,
    [data-testid="stChatMessage"] [dir="rtl"] h3,
    [data-testid="stChatMessage"] [dir="rtl"] h4 {
        font-family: var(--font-ar) !important;
        letter-spacing: 0 !important;
        word-spacing: 0.04em !important;
        font-size: 1.02rem !important;
        line-height: 1.85 !important;
    }

    /* ── English-specific tuning (LTR context) ── */
    [data-testid="stChatMessage"] [dir="ltr"] p,
    [data-testid="stChatMessage"] [dir="ltr"] li,
    [data-testid="stChatMessage"] [dir="ltr"] span,
    [data-testid="stChatMessage"] [dir="ltr"] h1,
    [data-testid="stChatMessage"] [dir="ltr"] h2,
    [data-testid="stChatMessage"] [dir="ltr"] h3,
    [data-testid="stChatMessage"] [dir="ltr"] h4 {
        font-family: var(--font-en) !important;
        letter-spacing: 0.01em !important;
        word-spacing: normal !important;
        font-size: 0.96rem !important;
        line-height: 1.7 !important;
    }

    /* Paragraph spacing within messages */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        margin-bottom: 10px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child {
        margin-bottom: 0 !important;
    }

    /* List styling with proper bidi */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol {
        unicode-bidi: plaintext !important;
        padding-inline-start: 22px !important;
        margin-bottom: 10px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
        margin-bottom: 5px !important;
    }

    /* Bold / strong text */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
        font-weight: 700 !important;
        color: var(--color-text-primary) !important;
    }

    /* Code blocks — always LTR, left-aligned, and horizontally scrollable */
    [data-testid="stChatMessage"] pre,
    [data-testid="stChatMessage"] code,
    [data-testid="stChatMessage"] .stCodeBlock {
        direction: ltr !important;
        text-align: left !important;
        unicode-bidi: isolate !important;
    }

    [data-testid="stChatMessage"] pre,
    [data-testid="stChatMessage"] .stCodeBlock {
        overflow-x: auto !important;
        max-width: 100% !important;
        white-space: pre !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        font-size: 0.88em !important;
        background-color: rgba(37, 99, 235, 0.06) !important;
        color: var(--color-primary-dark) !important;
        padding: 3px 6px !important;
        border-radius: 6px !important;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
    }

    /* Images — Responsive and undistorted */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] img {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 8px !important;
        display: block !important;
        margin: 10px 0 !important;
    }

    /* Tables — Styled and responsive horizontal scroll */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] table {
        display: block !important;
        width: 100% !important;
        overflow-x: auto !important;
        max-width: 100% !important;
        border-collapse: collapse !important;
        margin: 12px 0 !important;
        unicode-bidi: plaintext !important;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] td {
        border: 1px solid var(--color-divider) !important;
        padding: 8px 12px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th {
        background-color: var(--color-surface-hover) !important;
        font-weight: 600 !important;
    }

    /* ============================================================
       4. CHAT INPUT — Dynamic direction + polished styling
       ============================================================ */
    [data-testid="stChatInput"] {
        border-radius: var(--radius-input) !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: var(--shadow-sm) !important;
        transition: border-color var(--transition-smooth),
                    box-shadow var(--transition-smooth) !important;
        background-color: var(--color-surface) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--color-primary) !important;
        box-shadow: 0 0 0 4px var(--color-primary-glow),
                    var(--shadow-sm) !important;
    }

    [data-testid="stChatInput"] textarea {
        unicode-bidi: plaintext !important;
        text-align: start !important;
        font-family: var(--font-stack) !important;
        font-size: 0.98rem !important;
        line-height: 1.6 !important;
        color: var(--color-text-primary) !important;
        white-space: pre-wrap !important;
        word-break: normal !important;
        overflow-wrap: anywhere !important;
        word-wrap: break-word !important;
        overflow-x: hidden !important;
        padding: 10px 14px !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--color-text-muted) !important;
        opacity: 0.65 !important;
        font-family: var(--font-stack) !important;
    }

    /* Submit button styling in chat input */
    [data-testid="stChatInput"] button {
        color: var(--color-primary) !important;
        transition: color var(--transition-fast),
                    transform var(--transition-fast) !important;
    }

    [data-testid="stChatInput"] button:hover {
        color: var(--color-primary-dark) !important;
        transform: scale(1.1) !important;
    }

    /* ============================================================
       5. EXAMPLE QUESTION CARDS — Glassmorphism + hover effects
       ============================================================ */
    /* Target large example buttons specifically using marker selector */
    div:has(#example-questions-marker) + div [data-testid="column"] button {
        height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        border-radius: var(--radius-card) !important;
        border: 1px solid rgba(37, 99, 235, 0.15) !important;
        background: #ffffff !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 18px 16px !important;
        white-space: normal !important;
        font-family: var(--font-stack) !important;
        font-size: 0.93rem !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        transition: all var(--transition-spring) !important;
        cursor: pointer !important;
        unicode-bidi: plaintext !important;
        line-height: 1.55 !important;
        position: relative !important;
        overflow: hidden !important;
    }

    /* Subtle shimmer on hover for large cards */
    div:has(#example-questions-marker) + div [data-testid="column"] button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(37, 99, 235, 0.04) 50%,
            transparent 100%) !important;
        transition: left 0.5s ease !important;
    }

    div:has(#example-questions-marker) + div [data-testid="column"] button:hover::before {
        left: 100% !important;
    }

    div:has(#example-questions-marker) + div [data-testid="column"] button:hover {
        transform: translateY(-4px) !important;
        box-shadow: var(--shadow-lg), 0 0 0 1px rgba(37, 99, 235, 0.1) !important;
        border-color: var(--color-primary-light) !important;
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
        color: var(--color-primary-dark) !important;
    }

    div:has(#example-questions-marker) + div [data-testid="column"] button:focus {
        outline: none !important;
        border-color: var(--color-primary) !important;
        box-shadow: 0 0 0 3px var(--color-primary-glow) !important;
    }

    div:has(#example-questions-marker) + div [data-testid="column"] button:active {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* Style normal secondary buttons inside columns (like suggestion chips) */
    div[data-testid="column"] button {
        height: 38px !important;
        border-radius: 20px !important;
        font-size: 0.84rem !important;
        padding: 6px 14px !important;
        background-color: #ffffff !important;
        color: #475569 !important;
        border: 1px solid #cbd5e1 !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        font-family: var(--font-stack) !important;
    }
    div[data-testid="column"] button:hover {
        background-color: #eff6ff !important;
        color: #2563eb !important;
        border-color: #bfdbfe !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.08) !important;
    }

    .example-grid-title {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: var(--color-text-muted) !important;
        margin-bottom: 20px !important;
        text-align: center !important;
        font-family: var(--font-ar) !important;
        unicode-bidi: plaintext !important;
        letter-spacing: 0.01em !important;
    }

    /* ============================================================
       6. PAGE HEADER — Gradient accent
       ============================================================ */
    h1 {
        font-family: var(--font-stack) !important;
        color: var(--color-text-primary) !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        font-family: var(--font-stack) !important;
        color: var(--color-text-muted) !important;
        font-size: 0.9rem !important;
    }

    /* Expander inside assistant messages */
    [data-testid="stChatMessage"] details {
        border-radius: 12px !important;
        border: 1px solid var(--color-divider) !important;
        margin-top: 10px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(248, 250, 252, 0.8) 100%) !important;
        backdrop-filter: blur(8px) !important;
        overflow: hidden !important;
    }

    [data-testid="stChatMessage"] details summary {
        font-family: var(--font-stack) !important;
        font-weight: 500 !important;
        color: var(--color-text-secondary) !important;
        font-size: 0.88rem !important;
        padding: 8px 12px !important;
        transition: color var(--transition-fast) !important;
        cursor: pointer !important;
    }

    [data-testid="stChatMessage"] details summary:hover {
        color: var(--color-primary) !important;
    }

    [data-testid="stChatMessage"] details[open] summary {
        border-bottom: 1px solid var(--color-divider) !important;
        color: var(--color-primary-dark) !important;
    }

    /* ============================================================
       7. RESPONSIVE — Mobile / Tablet / Desktop
       ============================================================ */

    /* ── Mobile (≤ 576px) ── */
    @media (max-width: 576px) {
        [data-testid="stChatMessage"] {
            padding: 12px 14px !important;
            margin-bottom: 10px !important;
            max-width: 96% !important;
            border-radius: 12px !important;
        }

        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
            font-size: 0.93rem !important;
            line-height: 1.7 !important;
        }

        [data-testid="stChatMessage"] [dir="rtl"] p,
        [data-testid="stChatMessage"] [dir="rtl"] li {
            font-size: 0.96rem !important;
            line-height: 1.8 !important;
        }

        div[data-testid="column"] button {
            height: auto !important;
            min-height: 80px !important;
            padding: 12px !important;
            font-size: 0.86rem !important;
            border-radius: 10px !important;
        }

        h1 {
            font-size: 1.35rem !important;
        }

        [data-testid="stChatInput"] textarea {
            font-size: 0.93rem !important;
            padding: 10px 12px !important;
        }
    }

    /* ── Tablet (577px – 768px) ── */
    @media (min-width: 577px) and (max-width: 768px) {
        [data-testid="stChatMessage"] {
            padding: 14px 18px !important;
            margin-bottom: 14px !important;
            max-width: 90% !important;
        }

        div[data-testid="column"] button {
            height: auto !important;
            min-height: 100px !important;
            padding: 14px !important;
            font-size: 0.9rem !important;
        }

        h1 {
            font-size: 1.55rem !important;
        }
    }

    /* ── Small desktop (769px – 1199px) ── */
    @media (min-width: 769px) and (max-width: 1199px) {
        [data-testid="stChatMessage"] {
            max-width: 82% !important;
        }
    }

    /* ── Large desktop (≥ 1200px) ── */
    @media (min-width: 1200px) {
        [data-testid="stChatMessage"] {
            max-width: 75% !important;
        }
    }

    /* ============================================================
       8. SCROLLBAR POLISH
       ============================================================ */
    [data-testid="stChatMessageContent"]::-webkit-scrollbar {
        width: 5px;
    }

    [data-testid="stChatMessageContent"]::-webkit-scrollbar-track {
        background: transparent;
    }

    [data-testid="stChatMessageContent"]::-webkit-scrollbar-thumb {
        background-color: rgba(37, 99, 235, 0.15);
        border-radius: 10px;
    }

    [data-testid="stChatMessageContent"]::-webkit-scrollbar-thumb:hover {
        background-color: rgba(37, 99, 235, 0.3);
    }

    /* ============================================================
       9. SPINNER / LOADING STATE — Branded
       ============================================================ */
    .stSpinner > div {
        border-color: var(--color-primary) transparent transparent transparent !important;
    }

    /* ============================================================
       10. DIVIDER — Subtle gradient
       ============================================================ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg,
            transparent 0%,
            var(--color-divider) 20%,
            var(--color-divider) 80%,
            transparent 100%) !important;
        margin: 20px 0 !important;
    }

    /* ============================================================
       11. COST CAPTION — Polished
       ============================================================ */
    [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] {
        font-size: 0.78rem !important;
        color: var(--color-text-muted) !important;
        opacity: 0.8 !important;
        margin-top: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# JavaScript — Dynamic dir="auto" + live direction detection on input
# ---------------------------------------------------------------------------
# This script does:
#   1. Determines dominant text direction based on Arabic vs LTR character count.
#   2. Wraps inline mixed-language segments inside `<bdi>` tags to prevent punctuation
#      flipping and alignment distortion.
#   3. Dynamically overrides text input and textareas for live, fluid LTR/RTL responsiveness.
components.html(
    """
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // ── Character class regexes ──
        const RTL_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
        const LTR_RE = /[A-Za-z]/;

        /**
         * Detect the dominant direction of a text string by counting
         * Arabic (RTL) vs Latin (LTR) characters.
         */
        function detectDominantDirection(text) {
            if (!text) return 'ltr';
            let rtlCount = 0;
            let ltrCount = 0;
            for (let i = 0; i < text.length; i++) {
                const ch = text[i];
                if (RTL_RE.test(ch)) {
                    rtlCount++;
                } else if (LTR_RE.test(ch)) {
                    ltrCount++;
                }
            }
            if (rtlCount === 0 && ltrCount === 0) return 'ltr';
            return rtlCount > ltrCount ? 'rtl' : 'ltr';
        }

        /**
         * Segment a text string into alternating blocks of LTR and RTL content.
         */
        function splitMixedText(text) {
            if (!text) return [];
            let segments = [];
            let currentSegment = "";
            let currentIsArabic = null;

            for (let i = 0; i < text.length; i++) {
                const char = text[i];
                const isArabic = RTL_RE.test(char);
                const isNeutral = !isArabic && !LTR_RE.test(char);

                if (currentIsArabic === null) {
                    currentIsArabic = isArabic;
                    currentSegment += char;
                } else if (isArabic === currentIsArabic) {
                    currentSegment += char;
                } else if (isNeutral) {
                    // Peek ahead for the next strong directional character
                    let nextStrongIsArabic = currentIsArabic;
                    for (let j = i + 1; j < text.length; j++) {
                        const nextChar = text[j];
                        if (RTL_RE.test(nextChar)) {
                            nextStrongIsArabic = true;
                            break;
                        } else if (LTR_RE.test(nextChar)) {
                            nextStrongIsArabic = false;
                            break;
                        }
                    }
                    if (nextStrongIsArabic === currentIsArabic) {
                        currentSegment += char;
                    } else {
                        segments.push({ text: currentSegment, isArabic: currentIsArabic });
                        currentSegment = char;
                        currentIsArabic = nextStrongIsArabic;
                    }
                } else {
                    segments.push({ text: currentSegment, isArabic: currentIsArabic });
                    currentSegment = char;
                    currentIsArabic = isArabic;
                }
            }
            if (currentSegment) {
                segments.push({ text: currentSegment, isArabic: currentIsArabic });
            }
            return segments;
        }

        /**
         * Process a DOM text node, wrapping mixed-language segments in isolated <bdi> tags.
         */
        function processTextNode(textNode) {
            const text = textNode.nodeValue;
            if (!text || !text.trim()) return;

            // Skip if already inside a BDI tag we created
            if (textNode.parentNode && textNode.parentNode.tagName === 'BDI') {
                return;
            }

            const hasArabic = RTL_RE.test(text);
            const hasEnglish = LTR_RE.test(text);

            if (hasArabic && hasEnglish) {
                const segments = splitMixedText(text);
                if (segments.length > 1) {
                    const fragment = parentDoc.createDocumentFragment();
                    segments.forEach(seg => {
                        const bdi = parentDoc.createElement('bdi');
                        bdi.textContent = seg.text;
                        bdi.setAttribute('dir', seg.isArabic ? 'rtl' : 'ltr');
                        bdi.setAttribute('lang', seg.isArabic ? 'ar' : 'en');
                        bdi.style.fontFamily = seg.isArabic ? 'var(--font-ar)' : 'var(--font-en)';
                        fragment.appendChild(bdi);
                    });
                    if (textNode.parentNode) {
                        textNode.parentNode.replaceChild(fragment, textNode);
                    }
                }
            }
        }

        /**
         * Walk the children of a DOM node, ignoring styles, scripts, inputs, and code.
         */
        function processElement(element) {
            const ignoreTags = ['CODE', 'PRE', 'STYLE', 'SCRIPT', 'TEXTAREA', 'INPUT', 'BDI'];
            if (ignoreTags.includes(element.tagName)) return;

            const children = Array.from(element.childNodes);
            children.forEach(node => {
                if (node.nodeType === 3) { // TEXT_NODE
                    processTextNode(node);
                } else if (node.nodeType === 1) { // ELEMENT_NODE
                    processElement(node);
                }
            });
        }

        /**
         * Detect overall dominant direction of markdown containers and list/paragraph items,
         * then segment their text contents.
         */
        function setupMessageContainers() {
            const containers = parentDoc.querySelectorAll(
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]'
            );
            containers.forEach(c => {
                if (c.dataset.bidiSetup === 'v3') return;

                const text = c.textContent || '';
                const dir = detectDominantDirection(text);
                const lang = dir === 'rtl' ? 'ar' : 'en';

                c.setAttribute('dir', dir);
                c.setAttribute('lang', lang);
                c.style.textAlign = dir === 'rtl' ? 'right' : 'left';
                c.dataset.bidiSetup = 'v3';
            });

            const blocks = parentDoc.querySelectorAll(
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h4, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h5, ' +
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h6'
            );
            blocks.forEach(el => {
                if (el.dataset.bidiBlock === 'v3') return;

                const text = el.textContent || '';
                const dir = detectDominantDirection(text);
                const lang = dir === 'rtl' ? 'ar' : 'en';

                el.setAttribute('dir', dir);
                el.setAttribute('lang', lang);
                el.style.textAlign = dir === 'rtl' ? 'right' : 'left';
                el.style.unicodeBidi = 'plaintext';
                el.style.whiteSpace = 'pre-wrap';
                el.style.overflowWrap = 'anywhere';

                processElement(el);

                el.dataset.bidiBlock = 'v3';
            });
        }

        /**
         * Set up inputs and textareas with live dominant direction alignment.
         */
        function setupTextareas() {
            const textareas = parentDoc.querySelectorAll('[data-testid="stChatInput"] textarea');
            textareas.forEach(ta => {
                if (ta.dataset.bidiInit === 'v3') return;

                ta.setAttribute('dir', 'auto');
                ta.setAttribute('lang', 'auto');
                ta.style.textAlign = 'start';
                ta.style.unicodeBidi = 'plaintext';

                const handleInput = function() {
                    const dir = detectDominantDirection(this.value);
                    const lang = dir === 'rtl' ? 'ar' : 'en';
                    this.setAttribute('dir', dir);
                    this.setAttribute('lang', lang);
                    this.style.textAlign = dir === 'rtl' ? 'right' : 'left';
                    this.style.direction = dir;
                };

                ta.addEventListener('input', handleInput);
                ta.addEventListener('paste', function() {
                    setTimeout(() => handleInput.call(this), 10);
                });
                ta.addEventListener('focus', function() {
                    if (this.value && this.value.trim().length > 0) {
                        handleInput.call(this);
                    }
                });

                ta.dataset.bidiInit = 'v3';

                if (ta.value && ta.value.trim().length > 0) {
                    handleInput.call(ta);
                }
            });

            const inputs = parentDoc.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                if (input.dataset.bidiInit === 'v3') return;

                input.setAttribute('dir', 'auto');
                input.style.textAlign = 'start';
                input.style.unicodeBidi = 'plaintext';

                const handleInput = function() {
                    const dir = detectDominantDirection(this.value);
                    this.setAttribute('dir', dir);
                    this.style.textAlign = dir === 'rtl' ? 'right' : 'left';
                    this.style.direction = dir;
                };

                input.addEventListener('input', handleInput);
                input.addEventListener('paste', function() {
                    setTimeout(() => handleInput.call(this), 10);
                });

                input.dataset.bidiInit = 'v3';

                if (input.value && input.value.trim().length > 0) {
                    handleInput.call(input);
                }
            });
        }

        setupTextareas();
        setupMessageContainers();

        // Observe dynamic Streamlit mutations
        let mutationTimeout = null;
        const observer = new MutationObserver(() => {
            if (mutationTimeout) clearTimeout(mutationTimeout);
            mutationTimeout = setTimeout(() => {
                setupTextareas();
                setupMessageContainers();
            }, 50);
        });
        observer.observe(parentDoc.body, {
            childList: true,
            subtree: true,
            characterData: true
        });

        // Periodic sweep for safety
        setInterval(() => {
            setupTextareas();
            setupMessageContainers();
        }, 1000);
    })();
    </script>
    """,
    height=0,
)

# ---------------------------------------------------------------------------
# Initialize chat state
# ---------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "agent_run_id" not in st.session_state:
    st.session_state["agent_run_id"] = None

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="background: #ffffff; padding: 26px 30px; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.03); border: 1px solid #e2e8f0;">
        <div style="display: flex; align-items: center; gap: 18px;">
            <div style="font-size: 2rem; background: rgba(37, 99, 235, 0.08); color: #2563eb; padding: 10px; border-radius: 12px; line-height: 1;">💬</div>
            <div>
                <h1 style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; font-size: 1.55rem; font-weight: 800; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif; letter-spacing: -0.015em; line-height: 1.2;">Kayfa Sales Advisor</h1>
                <p style="color: #475569 !important; margin: 4px 0 0 0; font-size: 0.88rem; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif; font-weight: 600; line-height: 1.3;">Interactive AI Guide for Courses, Diplomas, and Pricing / مرشدك الذكي للدورات والمسارات</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Chat display
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Show cost if available
        if msg.get("role") == "assistant":
            if msg.get("cost", 0.0) > 0:
                st.caption(f"Cost: ${msg['cost']:.6f}")





# Input
user_input = st.chat_input("Type your message here… / اكتب رسالتك هنا…")

# Detect user input from chat input and append to history
if user_input:
    st.session_state["chat_history"].append({"role": "user", "content": user_input})
    st.rerun()

# Check if there is a pending user message to process
if (st.session_state["chat_history"] and 
    st.session_state["chat_history"][-1]["role"] == "user"):
    
    last_msg = st.session_state["chat_history"][-1]["content"]
    
    with st.spinner("Thinking..."):
        result = run_agent(
            user_message=last_msg,
            conversation_history=st.session_state["chat_history"][:-1],  # exclude just-added user msg
            username=username,
            run_id=st.session_state["agent_run_id"],
        )

    # Save run_id for continuity
    st.session_state["agent_run_id"] = result["run_id"]

    # Append assistant response with metadata
    st.session_state["chat_history"].append({
        "role": "assistant",
        "content": result["response"],
        "tool_calls": result.get("tool_calls"),
        "cost": result.get("cost", 0.0)
    })
    st.rerun()

# Render Sidebar navigation
render_sidebar()

with st.sidebar:
    from core.config import get_settings
    from datetime import datetime
    settings = get_settings()
    
    # 1. AI Status Indicator (pulsing green dot)
    model_display = settings.llm_model.split("/")[-1] if settings.llm_model else "AI Model"
    st.markdown(
        """
        <div style="background: #ffffff; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);">
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: #1e293b; font-size: 0.88rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                <span class="status-dot"></span>
                AI Advisor Status
            </div>
            <div style="font-size: 0.76rem; color: #64748b; margin-top: 4px; font-family: 'Plus Jakarta Sans', sans-serif; line-height: 1.4;">
                Model: {model_display}<br>
                Sync: Active (RAG Online)
            </div>
        </div>
        <style>
        .status-dot {
            height: 9px;
            width: 9px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6);
            animation: pulse 2.2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
            70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        </style>
        """.replace("{model_display}", model_display),
        unsafe_allow_html=True
    )
    
    # 2. Session Summary Card (real-time cost & turns)
    turns = len(st.session_state["chat_history"]) // 2
    total_cost = sum(msg.get("cost", 0.0) for msg in st.session_state["chat_history"] if msg.get("cost"))
    
    st.markdown(
        f"""
        <div style="background: #ffffff; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);">
            <div style="font-weight: 700; color: #1e293b; font-size: 0.88rem; font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 6px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
                📊 Session Summary
            </div>
            <div style="font-size: 0.82rem; color: #475569; font-family: 'Plus Jakarta Sans', sans-serif; line-height: 1.5;">
                <b>Conversation Turns:</b> {turns}<br>
                <b>Accumulated Cost:</b> ${total_cost:.5f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Export Chat History Button (if messages exist)
    if st.session_state["chat_history"]:
        history_text = ""
        for msg in st.session_state["chat_history"]:
            role_label = "Visitor" if msg["role"] == "user" else "Kayfa AI Advisor"
            history_text += f"=== {role_label} ===\n{msg['content']}\n\n"
            
        st.download_button(
            label="📥 Save Conversation",
            data=history_text,
            file_name=f"kayfa_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_chat_btn"
        )
        st.write("") # spacing

    # 4. Clear Chat button
    if st.button("Clear Chat", use_container_width=True, key="clear_chat_agent_btn"):
        st.session_state["chat_history"] = []
        st.session_state["agent_run_id"] = None
        st.rerun()
