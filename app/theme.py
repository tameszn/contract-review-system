import streamlit as st

_CSS = """
<style>
:root {
    --paper: #FAF9F6;
    --paper-deep: #F1EEE7;
    --ink: #2B2722;
}

/* Base paper colour + subtle warm gradient that deepens toward the bottom */
.stApp {
    background:
        linear-gradient(to bottom,
            rgba(250,249,246,0) 0%,
            rgba(250,249,246,0) 65%,
            rgba(190,170,135,0.14) 100%),
        var(--paper);
    color: var(--ink);
}

/* Let the paper show through Streamlit's own chrome */
[data-testid="stHeader"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: transparent !important;
}

/* Keep real content above the texture layers */
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    position: relative;
    z-index: 1;
}

/* Layer 1: fine grain across the whole viewport */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    opacity: 0.30;
    mix-blend-mode: multiply;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.25  0 0 0 0 0.20  0 0 0 0 0.12  0 0 0 0.9 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}

/* Layer 2: grunge blotches + heavier grain, strongest in the bottom 30% */
.stApp::after {
    content: "";
    position: fixed;
    left: 0; right: 0; bottom: 0;
    height: 30vh;
    z-index: 0;
    pointer-events: none;
    opacity: 0.45;
    mix-blend-mode: multiply;
    background-image:
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='5' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.30  0 0 0 0 0.23  0 0 0 0 0.14  0 0 0 1.3 -0.1'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>"),
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='900' height='600'><filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.012 0.02' numOctaves='3' seed='7' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.45  0 0 0 0 0.36  0 0 0 0 0.22  0 0 0 1.6 -0.45'/></filter><rect width='100%' height='100%' filter='url(%23g)'/></svg>");
    -webkit-mask-image: linear-gradient(to top, #000 15%, transparent 100%);
            mask-image: linear-gradient(to top, #000 15%, transparent 100%);
}

/* Readability tweaks for light mode */
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
.stButton > button[kind="primary"] {
    background: #2B2722;
    border: none;
    color: var(--paper);
}
.stButton > button[kind="primary"]:hover { background: #B4532A; }
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)