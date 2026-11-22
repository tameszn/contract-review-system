import base64
from pathlib import Path

import streamlit as st

HERO_IMAGE = Path(__file__).resolve().parent.parent / "assets" / "hero.png"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&display=swap');

:root {
    --paper: #FAF9F6;
    --paper-deep: #F1EEE7;
    --ink: #2B2722;
    --muted: #6B645A;
    --accent: #B4532A;
}

html, [data-testid="stMain"] { scroll-behavior: smooth; }

.stApp { background: var(--paper); color: var(--ink); }

[data-testid="stHeader"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: transparent !important; }

[data-testid="stMain"] { overflow-x: hidden; }
.block-container { padding-top: 0 !important; }

/* Uniform, very soft grain over everything (including the hero image) */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 9999;
    pointer-events: none;
    opacity: 0.35;
    mix-blend-mode: multiply;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.25  0 0 0 0 0.21  0 0 0 0 0.14  0 0 0 0.8 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}

/* ---------- Hero ---------- */
.ciq-hero {
    position: relative;
    width: 100vw;
    left: 50%;
    transform: translateX(-50%);
    min-height: 88vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: center;
}
.ciq-hero-text { padding: 0 2rem 0 max(5vw, 2rem); }

.ciq-title {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: clamp(2.4rem, 5.2vw, 4.6rem);
    letter-spacing: -0.04em;
    line-height: 1.05;
    margin: 0;
    color: var(--ink);
}
.ciq-sub {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    font-size: clamp(0.95rem, 1.4vw, 1.2rem);
    color: var(--muted);
    margin: 1.1rem 0 2.2rem;
}
a.ciq-cta {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.85rem 1.8rem;
    border-radius: 8px;
    background: var(--ink);
    color: var(--paper) !important;
    text-decoration: none !important;
    transition: background 0.2s ease, transform 0.2s ease;
}
a.ciq-cta:hover { background: var(--accent); transform: translateY(-2px); }

.ciq-hero-img { height: 100%; display: flex; align-items: center; justify-content: flex-end; }
.ciq-hero-img img {
    width: 100%;
    height: auto;
    display: block;
    /* white card dissolves into the paper colour */
    mix-blend-mode: multiply;
    /* soft fade on the left and bottom edges */
    -webkit-mask-image:
        linear-gradient(to right, transparent 0%, #000 22%),
        linear-gradient(to bottom, #000 70%, transparent 100%);
    -webkit-mask-composite: source-in;
            mask-image:
        linear-gradient(to right, transparent 0%, #000 22%),
        linear-gradient(to bottom, #000 70%, transparent 100%);
            mask-composite: intersect;
}

@media (max-width: 900px) {
    .ciq-hero { grid-template-columns: 1fr; min-height: auto; padding: 3rem 0; }
    .ciq-hero-text { padding: 0 1.5rem; }
    .ciq-hero-img { margin-top: 2rem; }
}

/* ---------- Main content ---------- */
#main-content { scroll-margin-top: 1rem; }
h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.01em; }
hr { border-color: rgba(43,39,34,0.15) !important; }

[data-testid="stFileUploader"] section,
[data-testid="stExpander"] {
    background: rgba(241,238,231,0.7);
    border: 1px solid rgba(43,39,34,0.12);
    border-radius: 10px;
}
[data-testid="stMetric"] {
    background: rgba(241,238,231,0.6);
    border: 1px solid rgba(43,39,34,0.10);
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
.stButton > button[kind="primary"] { background: var(--ink); border: none; color: var(--paper); }
.stButton > button[kind="primary"]:hover { background: var(--accent); }
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero() -> None:
    img_html = ""
    if HERO_IMAGE.exists():
        b64 = base64.b64encode(HERO_IMAGE.read_bytes()).decode()
        img_html = f'<div class="ciq-hero-img"><img src="data:image/png;base64,{b64}" alt="Contract iQ preview"/></div>'

    # No indentation / blank lines: markdown would treat them as a code block.
    html = (
        '<section class="ciq-hero">'
        '<div class="ciq-hero-text">'
        '<h1 class="ciq-title">ContractIQ</h1>'
        '<p class="ciq-sub">AI-contract intelligence and review system</p>'
        '<a class="ciq-cta" href="#main-content" target="_self">Try now !</a>'
        '</div>'
        f'{img_html}'
        '</section>'
    )
    st.markdown(html, unsafe_allow_html=True)
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)