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
# Comprehensive CSS for bilingual (Arabic + English) chat interface:
#   - Google Fonts: Cairo (Arabic) + Inter (English)
#   - unicode-bidi: plaintext for automatic per-paragraph direction
#   - Distinct bubble colors for user vs assistant
#   - Responsive layout for mobile / tablet / desktop
#   - Proper word-break and overflow-wrap to avoid mid-word breaks
st.markdown(
    """
    <style>
    /* ============================================================
       1. FONTS — Arabic (Cairo 300–700) + English (Inter 300–700)
       ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        /* Font stacks */
        --font-stack: 'Inter', 'Cairo', 'Segoe UI', Tahoma, sans-serif;
        --font-ar: 'Cairo', 'Inter', 'Segoe UI', Tahoma, sans-serif;
        --font-en: 'Inter', 'Cairo', 'Segoe UI', Tahoma, sans-serif;

        /* Primary palette — vibrant blue gradient */
        --color-primary: #6366f1;
        --color-primary-light: #818cf8;
        --color-primary-dark: #4f46e5;
        --color-primary-glow: rgba(99, 102, 241, 0.15);
        --color-primary-glow-strong: rgba(99, 102, 241, 0.25);

        /* User bubble — soft indigo tint */
        --color-user-bg: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
        --color-user-bg-solid: #eef2ff;
        --color-user-border: #c7d2fe;
        --color-user-accent: #6366f1;

        /* Assistant bubble — warm neutral */
        --color-assistant-bg: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        --color-assistant-bg-solid: #f8fafc;
        --color-assistant-border: #e2e8f0;
        --color-assistant-accent: #0ea5e9;

        /* Text & surface */
        --color-text-primary: #0f172a;
        --color-text-secondary: #334155;
        --color-text-muted: #64748b;
        --color-text-on-primary: #ffffff;
        --color-surface: #ffffff;
        --color-surface-hover: #f8fafc;
        --color-divider: rgba(0, 0, 0, 0.06);
        --color-page-bg: #fafbfe;

        /* Radii */
        --radius-bubble: 18px;
        --radius-input: 14px;
        --radius-card: 16px;

        /* Shadows */
        --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.03);
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.03);
        --shadow-lg: 0 12px 28px rgba(0, 0, 0, 0.08), 0 4px 8px rgba(0, 0, 0, 0.04);
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
    }

    /* ============================================================
       2. CHAT BUBBLES — Premium, distinct styling
       ============================================================ */
    [data-testid="stChatMessage"] {
        border-radius: var(--radius-bubble) !important;
        margin-bottom: 16px !important;
        padding: 18px 22px !important;
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
        border-bottom-right-radius: 6px !important;
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
        border-bottom-left-radius: 6px !important;
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
    /* All text elements inside chat messages get plaintext bidi */
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
        /* Prevent mid-word breaks — critical for mixed-language text */
        word-break: normal !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        hyphens: none !important;
        -webkit-hyphens: none !important;
        -ms-hyphens: none !important;
        /* Ensure white-space is handled properly for mixed content */
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
        font-size: 1.04rem !important;
        line-height: 1.9 !important;
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
        letter-spacing: 0.012em !important;
        word-spacing: normal !important;
        font-size: 0.98rem !important;
        line-height: 1.75 !important;
    }

    /* ── Mixed-content isolation: wrap inline language switches ── */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] [dir="auto"] {
        unicode-bidi: plaintext !important;
        word-break: normal !important;
    }

    /* Paragraph spacing within messages */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        margin-bottom: 12px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child {
        margin-bottom: 0 !important;
    }

    /* List styling with proper bidi */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol {
        unicode-bidi: plaintext !important;
        padding-inline-start: 22px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
        margin-bottom: 6px !important;
    }

    /* Bold / strong text */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
        font-weight: 700 !important;
        color: var(--color-text-primary) !important;
    }

    /* Code blocks — always LTR and left-aligned regardless of container direction */
    [data-testid="stChatMessage"] pre,
    [data-testid="stChatMessage"] code,
    [data-testid="stChatMessage"] .stCodeBlock {
        direction: ltr !important;
        text-align: left !important;
        unicode-bidi: isolate !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        font-size: 0.88em !important;
        background-color: rgba(99, 102, 241, 0.08) !important;
        color: var(--color-primary-dark) !important;
        padding: 3px 7px !important;
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

    /* Tables */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] table {
        border-collapse: collapse !important;
        margin: 12px 0 !important;
        unicode-bidi: plaintext !important;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] td {
        border: 1px solid var(--color-divider) !important;
        padding: 8px 12px !important;
    }

    /* ============================================================
       4. CHAT INPUT — Dynamic direction + polished styling
       ============================================================ */
    [data-testid="stChatInput"] {
        border-radius: var(--radius-input) !important;
        border: 1.5px solid var(--color-divider) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: border-color var(--transition-smooth),
                    box-shadow var(--transition-smooth) !important;
        background-color: var(--color-surface) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--color-primary) !important;
        box-shadow: 0 0 0 3px var(--color-primary-glow),
                    var(--shadow-sm) !important;
    }

    [data-testid="stChatInput"] textarea {
        unicode-bidi: plaintext !important;
        text-align: start !important;
        font-family: var(--font-stack) !important;
        font-size: 1rem !important;
        line-height: 1.65 !important;
        color: var(--color-text-primary) !important;
        white-space: pre-wrap !important;
        word-break: normal !important;
        overflow-wrap: anywhere !important;
        word-wrap: break-word !important;
        overflow-x: hidden !important;
        padding: 12px 16px !important;
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
    div[data-testid="column"] button {
        height: 128px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        border-radius: var(--radius-card) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        background: linear-gradient(135deg,
            rgba(255, 255, 255, 0.9) 0%,
            rgba(248, 250, 252, 0.95) 100%) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 18px 16px !important;
        white-space: normal !important;
        font-family: var(--font-stack) !important;
        font-size: 0.93rem !important;
        font-weight: 500 !important;
        color: var(--color-text-secondary) !important;
        transition: all var(--transition-spring) !important;
        cursor: pointer !important;
        unicode-bidi: plaintext !important;
        line-height: 1.55 !important;
        position: relative !important;
        overflow: hidden !important;
    }

    /* Subtle shimmer on hover */
    div[data-testid="column"] button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(99, 102, 241, 0.04) 50%,
            transparent 100%) !important;
        transition: left 0.5s ease !important;
    }

    div[data-testid="column"] button:hover::before {
        left: 100% !important;
    }

    div[data-testid="column"] button:hover {
        transform: translateY(-4px) !important;
        box-shadow: var(--shadow-lg), 0 0 0 1px rgba(99, 102, 241, 0.12) !important;
        border-color: var(--color-primary-light) !important;
        background: linear-gradient(135deg,
            rgba(238, 242, 255, 0.95) 0%,
            rgba(224, 231, 255, 0.9) 100%) !important;
        color: var(--color-primary-dark) !important;
    }

    div[data-testid="column"] button:focus {
        outline: none !important;
        border-color: var(--color-primary) !important;
        box-shadow: 0 0 0 3px var(--color-primary-glow) !important;
    }

    div[data-testid="column"] button:active {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .example-grid-title {
        font-size: 1.12rem !important;
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
            border-radius: 14px !important;
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
            border-radius: 12px !important;
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
        background-color: rgba(99, 102, 241, 0.15);
        border-radius: 10px;
    }

    [data-testid="stChatMessageContent"]::-webkit-scrollbar-thumb:hover {
        background-color: rgba(99, 102, 241, 0.3);
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
# This script does two things:
#   1. Sets dir="auto" on all textareas so the browser's bidi algorithm
#      detects the first strong character and sets direction accordingly.
#   2. Adds a live 'input' event listener that inspects the first strong
#      character typed, and explicitly sets dir/textAlign for immediate
#      visual feedback — so the cursor and alignment respond instantly
#      when switching between Arabic and English mid-message.
#   3. Sets dir="auto" on all chat message markdown containers so each
#      paragraph auto-aligns based on its own content.
components.html(
    """
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // ── Character class regexes ──
        // Comprehensive RTL: Arabic (all blocks), Hebrew, Thaana, Syriac, NKo
        const RTL_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0590-\u05FF\u0780-\u07BF\u0700-\u074F\u07C0-\u07FF]/;
        // Latin + extended Latin
        const LTR_RE = /[A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0370-\u03FF]/;
        // Numbers and neutral symbols (not directional)
        const NEUTRAL_RE = /[\d\s\p{P}\p{S}]/u;

        /**
         * Detect the dominant direction of a text string by finding
         * the first strong directional character.
         */
        function detectDirection(text) {
            if (!text) return 'auto';
            for (let i = 0; i < text.length; i++) {
                const ch = text[i];
                if (RTL_RE.test(ch)) return 'rtl';
                if (LTR_RE.test(ch)) return 'ltr';
            }
            return 'auto';
        }

        function detectLanguage(text) {
            if (!text) return 'auto';
            const trimmed = text.trim();
            if (!trimmed) return 'auto';
            if (RTL_RE.test(trimmed)) return 'ar';
            if (LTR_RE.test(trimmed)) return 'en';
            return 'auto';
        }

        /**
         * Apply direction and text alignment to an element.
         * Preserves cursor position for input elements.
         */
        function applyDirection(el, dir) {
            const currentDir = el.getAttribute('dir');
            if (currentDir === dir) return; // No change needed

            if (dir === 'rtl') {
                el.setAttribute('dir', 'rtl');
                el.setAttribute('lang', 'ar');
                el.style.textAlign = 'right';
                el.style.direction = 'rtl';
            } else if (dir === 'ltr') {
                el.setAttribute('dir', 'ltr');
                el.setAttribute('lang', 'en');
                el.style.textAlign = 'left';
                el.style.direction = 'ltr';
            } else {
                el.setAttribute('dir', 'auto');
                el.setAttribute('lang', 'auto');
                el.style.textAlign = 'start';
                el.style.direction = '';
            }

            el.style.whiteSpace = 'pre-wrap';
            el.style.overflowWrap = 'anywhere';
            el.style.wordBreak = 'normal';
            el.style.wordWrap = 'break-word';
        }

        /**
         * Set up all textarea and text input elements with bidi detection.
         */
        function setupTextareas() {
            const textareas = parentDoc.querySelectorAll('[data-testid="stChatInput"] textarea');
            textareas.forEach(ta => {
                if (ta.dataset.bidiInit === 'v2') return;

                // Initial setup
                ta.setAttribute('dir', 'auto');
                ta.setAttribute('lang', 'auto');
                ta.style.textAlign = 'start';
                ta.style.unicodeBidi = 'plaintext';

                // Live detection on every keystroke
                ta.addEventListener('input', function() {
                    const dir = detectDirection(this.value);
                    const lang = detectLanguage(this.value);
                    this.setAttribute('lang', lang);
                    applyDirection(this, dir);
                });

                // Handle paste with slight delay for content to populate
                ta.addEventListener('paste', function() {
                    const self = this;
                    setTimeout(() => {
                        const dir = detectDirection(self.value);
                        applyDirection(self, dir);
                    }, 10);
                });

                // Handle focus — re-detect on focus in case value changed externally
                ta.addEventListener('focus', function() {
                    if (this.value && this.value.trim().length > 0) {
                        const dir = detectDirection(this.value);
                        applyDirection(this, dir);
                    }
                });

                ta.dataset.bidiInit = 'v2';

                // Apply direction to existing content
                if (ta.value && ta.value.trim().length > 0) {
                    const dir = detectDirection(ta.value);
                    const lang = detectLanguage(ta.value);
                    ta.setAttribute('lang', lang);
                    applyDirection(ta, dir);
                }
            });

            // Also handle text inputs (search, form fields, etc.)
            const inputs = parentDoc.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                if (input.dataset.bidiInit === 'v2') return;

                input.setAttribute('dir', 'auto');
                input.style.textAlign = 'start';
                input.style.unicodeBidi = 'plaintext';

                input.addEventListener('input', function() {
                    const dir = detectDirection(this.value);
                    applyDirection(this, dir);
                });

                input.addEventListener('paste', function() {
                    const self = this;
                    setTimeout(() => {
                        const dir = detectDirection(self.value);
                        applyDirection(self, dir);
                    }, 10);
                });

                input.dataset.bidiInit = 'v2';

                if (input.value && input.value.trim().length > 0) {
                    const dir = detectDirection(input.value);
                    applyDirection(input, dir);
                }
            });
        }

        /**
         * Set dir="auto" + per-paragraph direction on all chat message content.
         * Each paragraph, heading, and list item gets its own direction so
         * mixed-language messages render each block correctly.
         */
        function setupMessageContainers() {
            // Markdown containers get dir="auto"
            const containers = parentDoc.querySelectorAll(
                '[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]'
            );
            containers.forEach(c => {
                if (c.dataset.bidiSetup === 'v2') return;
                c.setAttribute('dir', 'auto');
                c.style.textAlign = 'start';
                c.dataset.bidiSetup = 'v2';
            });

            // Per-paragraph direction detection
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
                if (el.dataset.bidiBlock === 'v2') return;

                // Detect the direction from the element's text content
                const text = el.textContent || '';
                const dir = detectDirection(text);
                const lang = detectLanguage(text);

                if (dir !== 'auto') {
                    el.setAttribute('dir', dir);
                    el.setAttribute('lang', lang);
                    el.style.textAlign = dir === 'rtl' ? 'right' : 'left';
                } else {
                    el.setAttribute('dir', 'auto');
                    el.setAttribute('lang', lang);
                    el.style.textAlign = 'start';
                }

                el.style.unicodeBidi = 'plaintext';
                el.style.whiteSpace = 'pre-wrap';
                el.style.overflowWrap = 'anywhere';
                el.dataset.bidiBlock = 'v2';
            });
        }

        // ── Initial execution ──
        setupTextareas();
        setupMessageContainers();

        // ── MutationObserver: catch Streamlit's dynamic DOM changes ──
        let mutationTimeout = null;
        const observer = new MutationObserver(() => {
            // Debounce to avoid excessive processing
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

        // ── Fallback interval (safety net for edge cases) ──
        setInterval(() => {
            setupTextareas();
            setupMessageContainers();
        }, 1500);
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
st.title("💬 Kayfa Sales Agent")
st.caption("Ask me about courses, tracks, diplomas, pricing, or anything about Kayfa!")
st.markdown("---")

# Chat display
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Show tool call details and cost if available
        if msg.get("role") == "assistant":
            if msg.get("tool_calls"):
                with st.expander("🛠️ Tool calls", expanded=False):
                    for tc in msg["tool_calls"]:
                        st.markdown(f"**{tc['tool']}** — `{tc['arguments']}`")
                        st.json(tc["result"])
            if msg.get("cost", 0.0) > 0:
                st.caption(f"Cost: ${msg['cost']:.6f}")

# Example Questions (Only show when chat history is empty)
if not st.session_state["chat_history"]:
    st.markdown('<div class="example-grid-title">💡 Select a question to start / اختر سؤالاً للبدء</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Data Science Courses / دورات علم البيانات\n\nWhat courses do you offer in Data Science?", use_container_width=True, key="ex_ds"):
            st.session_state["chat_history"].append({"role": "user", "content": "What courses do you offer in Data Science?"})
            st.rerun()
            
        if st.button("🛡️ SOC Cybersecurity / الأمن السيبراني\n\nHow much does the SOC track cost?", use_container_width=True, key="ex_soc"):
            st.session_state["chat_history"].append({"role": "user", "content": "How much does the SOC track cost?"})
            st.rerun()
            
    with col2:
        if st.button("🤖 AI Diploma / دبلوم الذكاء الاصطناعي\n\nTell me about the AI Diploma", use_container_width=True, key="ex_ai"):
            st.session_state["chat_history"].append({"role": "user", "content": "Tell me about the AI Diploma"})
            st.rerun()
            
        if st.button("📋 Refund Policies / سياسات الاسترداد\n\nWhat are the refund policies?", use_container_width=True, key="ex_refund"):
            st.session_state["chat_history"].append({"role": "user", "content": "What are the refund policies?"})
            st.rerun()

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

# In-page Clear Chat button (we can keep or let the sidebar logout/clear handle it, but wait! The user had a Clear Chat button in the sidebar.
# If we call render_sidebar(), it doesn't have a "Clear Chat" button, it has a "Logout" button.
# Let's add the "Clear Chat" button inside the sidebar render_sidebar() helper or let's place a small button in the main page, or inside st.sidebar before/after render_sidebar()?
# Wait! In render_sidebar(), it doesn't have a Clear Chat button. But we can add the Clear Chat button directly inside the sidebar by rendering it inside st.sidebar *after* calling render_sidebar()!
# Yes! We can write:
# with st.sidebar:
#     if st.button("Clear Chat", use_container_width=True):
#         st.session_state["chat_history"] = []
#         st.session_state["agent_run_id"] = None
#         st.rerun()
# This is perfect! It adds the page-specific Clear Chat button at the very bottom of the sidebar, exactly where it belongs!
with st.sidebar:
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state["agent_run_id"] = None
        st.rerun()
