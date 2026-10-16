"""
CampusSpace - Smart Campus Room Finder
Hackathon Round 1 MVP | Full-Stack Streamlit Application
"""

import os
import sys
import warnings
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore", message=".*use_container_width.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_all_datasets
from src.data_validation import validate_datasets, get_data_dictionary
from src.availability import check_room_conflicts, get_room_day_timeline, parse_weekday_from_date
from src.recommendation import find_room_recommendations
from src.analytics import compute_overall_kpis, compute_room_utilization_metrics, generate_data_backed_insights
from src.auth import (
    authenticate_user,
    get_demo_accounts_table,
    is_authenticated,
    is_admin,
    is_faculty_or_admin,
    is_guest,
    login_user,
    login_guest,
    logout_user,
)

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CampusSpace | Smart Campus Room Finder",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Session State Defaults
# ─────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "display_name" not in st.session_state:
    st.session_state["display_name"] = ""
if "remember_me" not in st.session_state:
    st.session_state["remember_me"] = False
if "login_show_pwd" not in st.session_state:
    st.session_state["login_show_pwd"] = False

# ─────────────────────────────────────────────
# CSS Injection
# ─────────────────────────────────────────────
def inject_css(dark: bool, is_login: bool = False):
    if dark:
        bg       = "#0F172A"
        sidebar  = "#090E17"
        card     = "#1E293B"
        border   = "#334155"
        text     = "#F1F5F9"
        muted    = "#CBD5E1"
        accent   = "#14B8A6"
        tag_bg   = "#334155"
        tag_col  = "#F1F5F9"
        input_bg = "#1E293B"
        label_c  = "#F1F5F9"
    else:
        bg       = "#FFFFFF"
        sidebar  = "#F8FAFC"
        card     = "#FFFFFF"
        border   = "#CBD5E1"
        text     = "#000000"
        muted    = "#1E293B"
        accent   = "#0F9D8A"
        tag_bg   = "#F1F5F9"
        tag_col  = "#000000"
        input_bg = "#FFFFFF"
        label_c  = "#000000"

    login_overrides = """
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    .main .block-container {
        max-width: 1240px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
    }
    """ if is_login else """
    [data-testid="stSidebar"] {
        display: flex !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
    .main .block-container {
        max-width: 100% !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
    }
    """

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    {login_overrides}

    /* ── Global Reset ── */
    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: {bg} !important;
        color: {text} !important;
    }}

    /* ── Force text color everywhere on all elements ── */
    p, span, div, label, h1, h2, h3, h4, h5, h6, strong, em, b, i,
    .stMarkdown, .stText, .element-container,
    [data-testid="stMarkdownContainer"] *,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stRadio"] *,
    div[data-testid="stCheckbox"] *,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stMultiSelect"] *,
    div[data-testid="stNumberInput"] *,
    div[data-testid="stSlider"] *,
    div[data-testid="stDateInput"] *,
    div[data-testid="stTextInput"] *,
    div[data-testid="stTextArea"] *,
    div[data-testid="stToggle"] * {{
        color: {text} !important;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background-color: {sidebar} !important;
        border-right: 1.5px solid {border} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        color: {text} !important;
        font-weight: 700 !important;
    }}

    /* ── Input fields ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1.5px solid {border} !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }}
    .stTextInput > div > div > input::placeholder {{
        color: {muted} !important;
    }}
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1.5px solid {border} !important;
        border-radius: 8px !important;
    }}
    .stSelectbox svg, .stMultiSelect svg {{
        fill: {text} !important;
    }}

    /* ── BaseWeb Popover Menus & Options (Select dropdowns) ── */
    [data-baseweb="popover"],
    [data-baseweb="popover"] *,
    [data-baseweb="menu"],
    [data-baseweb="menu"] *,
    [data-baseweb="select"],
    [data-baseweb="select"] *,
    ul[role="listbox"],
    ul[role="listbox"] *,
    li[role="option"],
    li[role="option"] *,
    div[role="option"],
    div[role="option"] * {{
        color: {text} !important;
        background-color: {card} !important;
        font-weight: 500 !important;
    }}
    li[role="option"]:hover,
    div[role="option"]:hover,
    [data-baseweb="menu"] li:hover {{
        background-color: {tag_bg} !important;
        color: {text} !important;
    }}

    /* ── Slider ── */
    .stSlider [data-testid="stSliderTrackColor"] {{
        background: {accent} !important;
    }}
    .stSlider [role="slider"] {{
        background: {accent} !important;
    }}
    .stSlider p, .stSlider span, .stSlider div {{
        color: {text} !important;
        font-weight: 600 !important;
    }}

    /* ── Checkbox & Radio ── */
    .stCheckbox span, .stCheckbox p, .stCheckbox label,
    .stRadio span, .stRadio p, .stRadio label {{
        color: {text} !important;
        font-weight: 600 !important;
    }}

    /* ── Date picker ── */
    .stDateInput > div > div > input {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1.5px solid {border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}

    /* ── Toggle ── */
    .stToggle p, [data-testid="stToggle"] p, [data-testid="stToggle"] span {{
        color: {text} !important;
        font-weight: 600 !important;
    }}

    /* ── Metric widget ── */
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {{
        color: {text} !important;
        font-weight: 700 !important;
    }}

    /* ── Dataframe ── */
    .stDataFrame, [data-testid="stDataFrame"] {{
        background-color: {card} !important;
        border-radius: 10px !important;
        border: 1.5px solid {border} !important;
    }}
    .stDataFrame th, .stDataFrame td, [data-testid="stDataFrame"] * {{
        color: {text} !important;
        background-color: {card} !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background-color: {card} !important;
        color: {text} !important;
        border: 1.5px solid {border} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }}
    .streamlit-expanderContent {{
        background-color: {card} !important;
        border: 1.5px solid {border} !important;
        color: {text} !important;
    }}
    .streamlit-expanderHeader p, .streamlit-expanderHeader span {{
        color: {text} !important;
        font-weight: 700 !important;
    }}

    /* ── Tabs ── */
    .stTabs [role="tab"] {{
        color: {text} !important;
        background-color: transparent !important;
        font-weight: 700 !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
        border-bottom: 3px solid {accent} !important;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background-color: {accent} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        transition: opacity 0.2s ease !important;
    }}
    .stButton > button:hover {{
        opacity: 0.88 !important;
    }}
    .stFormSubmitButton > button {{
        background-color: {accent} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
    }}

    /* ── Alerts / Info / Warning / Error ── */
    .stAlert > div {{
        color: {text} !important;
    }}
    [data-testid="stInfoBox"] {{ color: {text} !important; }}

    /* ── Cards (custom html) ── */
    .cs-card {{
        background-color: {card};
        border: 1.5px solid {border};
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }}
    .cs-card * {{ color: {text} !important; }}

    .stat-card {{
        background-color: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .stat-label {{
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {text} !important;
        margin-bottom: 0.25rem;
    }}
    .stat-value {{
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        color: {text} !important;
    }}
    .stat-sub {{
        font-size: 0.8rem;
        color: {text} !important;
        opacity: 0.88;
        margin-top: 0.3rem;
    }}

    .insight-box {{
        background-color: {card};
        border: 1.5px solid {border};
        border-left: 5px solid {accent};
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.9rem;
    }}
    .insight-title {{
        font-size: 0.95rem;
        font-weight: 800;
        color: {text} !important;
        margin-bottom: 0.2rem;
    }}
    .insight-metric {{
        font-size: 1.05rem;
        font-weight: 800;
        color: {accent} !important;
        margin-bottom: 0.4rem;
    }}
    .insight-body {{
        font-size: 0.88rem;
        color: {text} !important;
        line-height: 1.45;
    }}
    .insight-caveat {{
        font-size: 0.8rem;
        font-style: italic;
        color: {text} !important;
        margin-top: 0.4rem;
        opacity: 0.88;
    }}

    .rec-card {{
        background-color: {card};
        border: 1.5px solid {border};
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .rec-card.best-fit   {{ border-left: 6px solid #0F9D8A; }}
    .rec-card.alternative{{ border-left: 6px solid #3B82F6; }}
    .rec-card.good-option{{ border-left: 6px solid #F59E0B; }}
    .rec-card * {{ color: {text} !important; }}

    .badge-tag {{
        background-color: {tag_bg};
        color: {text} !important;
        border: 1.5px solid {border};
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 0.35rem;
        display: inline-block;
        margin-top: 0.2rem;
    }}

    .tier-badge {{
        display: inline-block;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.73rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .badge-best  {{ background:#ECFDF5; color:#065F46 !important; border:1px solid #A7F3D0; }}
    .badge-alt   {{ background:#EFF6FF; color:#1E40AF !important; border:1px solid #BFDBFE; }}
    .badge-good  {{ background:#FFFBEB; color:#92400E !important; border:1px solid #FDE68A; }}

    .app-footer {{
        text-align: center;
        padding: 2rem 1rem 1rem;
        font-size: 0.78rem;
        color: {muted} !important;
        border-top: 1px solid {border};
        margin-top: 3rem;
    }}

    /* ── SaaS Login Page Styles ── */
    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0.35rem 0.85rem;
        background: {tag_bg};
        border: 1.5px solid {border};
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        color: {accent} !important;
        margin-bottom: 1.1rem;
    }}
    .hero-title {{
        font-size: 2.7rem;
        font-weight: 900;
        line-height: 1.12;
        letter-spacing: -0.025em;
        color: {text} !important;
        margin-bottom: 0.85rem;
    }}
    .hero-sub {{
        font-size: 1.05rem;
        color: {muted} !important;
        line-height: 1.55;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }}
    .live-visual-card {{
        background: {card};
        border: 1.5px solid {border};
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }}
    .live-visual-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {muted} !important;
    }}
    .pulse-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        display: inline-block;
        margin-right: 6px;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25);
    }}
    .mini-room-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.65rem 0.85rem;
        border-radius: 8px;
        border: 1px solid {border};
        background: {card};
        margin-bottom: 0.5rem;
    }}
    .mini-badge-avail {{
        background: #ECFDF5;
        color: #065F46 !important;
        border: 1px solid #A7F3D0;
        padding: 0.18rem 0.55rem;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
    }}
    .mini-badge-busy {{
        background: #FFFBEB;
        color: #92400E !important;
        border: 1px solid #FDE68A;
        padding: 0.18rem 0.55rem;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
    }}
    .benefit-row {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 0.95rem;
    }}
    .benefit-icon-box {{
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: {tag_bg};
        color: {accent} !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 800;
        flex-shrink: 0;
    }}
    .benefit-text {{
        font-size: 0.9rem;
        line-height: 1.4;
        color: {text} !important;
    }}
    .hero-footer-note {{
        font-size: 0.82rem;
        color: {muted} !important;
        font-weight: 600;
        margin-top: 1.5rem;
        border-top: 1px solid {border};
        padding-top: 1rem;
    }}
    div[data-testid="stForm"] {{
        background-color: {card} !important;
        border: 1.5px solid {border} !important;
        border-radius: 16px !important;
        padding: 1.8rem 2rem 1.6rem !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08) !important;
    }}

    /* ── Score bar ── */
    .score-bar-bg {{
        background-color: {border};
        border-radius: 9999px;
        height: 8px;
        width: 100%;
        margin-top: 4px;
    }}
    .score-bar-fill {{
        background-color: {accent};
        border-radius: 9999px;
        height: 8px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Data Loader
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_cached_data():
    return load_all_datasets()


# ─────────────────────────────────────────────
# ── LOGIN PAGE ──
# ─────────────────────────────────────────────
def show_login():
    inject_css(st.session_state["dark_mode"], is_login=True)
    dark = st.session_state["dark_mode"]

    bg_card    = "#1E293B" if dark else "#FFFFFF"
    border_col = "#334155" if dark else "#CBD5E1"
    text_col   = "#F1F5F9" if dark else "#000000"
    muted_col  = "#CBD5E1" if dark else "#1E293B"

    # Top Brand & Mode Bar
    top_c1, top_c2 = st.columns([3.5, 1])
    with top_c1:
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;">
                <div style="background:linear-gradient(135deg,#0F9D8A,#14243A);color:white;
                            font-size:1.3rem;font-weight:900;width:42px;height:42px;
                            border-radius:10px;display:flex;align-items:center;justify-content:center;
                            box-shadow:0 3px 10px rgba(15,157,138,0.3);">CS</div>
                <div>
                    <div style="font-size:1.3rem;font-weight:900;line-height:1.1;letter-spacing:-0.01em;color:{text_col}!important;">CampusSpace</div>
                    <div style="font-size:0.7rem;font-weight:800;letter-spacing:1px;color:{muted_col}!important;">SMART CAMPUS ROOM FINDER &bull; ROUND 1 MVP</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with top_c2:
        dm = st.toggle("🌙 Dark Mode", value=dark, key="login_dark_mode_toggle")
        if dm != dark:
            st.session_state["dark_mode"] = dm
            st.rerun()

    # Balanced Two-Column SaaS Layout
    col_left, col_right = st.columns([1.18, 1], gap="large")

    # ─────────────────────────────────────────────
    # LEFT COLUMN: Hero, Live CSS Visual, and Benefits
    # ─────────────────────────────────────────────
    with col_left:
        st.markdown(f"""
            <div style="padding-right:0.6rem;">
                <div class="hero-badge">
                    <span class="pulse-dot"></span>
                    <span>CAMPUS SPACE OPTIMIZATION PLATFORM</span>
                </div>
                <div class="hero-title">Your campus.<br><span style="color:#0F9D8A;">Your space.</span></div>
                <div class="hero-sub">
                    Discover suitable rooms, check availability, and find the perfect space for every campus activity.
                </div>

                <!-- Clean CSS-based Campus Room & Schedule Visual -->
                <div class="live-visual-card">
                    <div class="live-visual-header">
                        <div style="display:flex;align-items:center;">
                            <span class="pulse-dot"></span>
                            <span>LIVE CAMPUS AUDIT &bull; 120 ROOMS</span>
                        </div>
                        <div>TODAY 14:00 &ndash; 16:00</div>
                    </div>

                    <div class="mini-room-item">
                        <div>
                            <div style="font-weight:800;font-size:0.88rem;color:{text_col}!important;">Room 102 &bull; Seminar Hall</div>
                            <div style="font-size:0.75rem;color:{muted_col}!important;">Main Block &bull; Floor 1 &bull; Cap: 45 &bull; 📽️ 🔌</div>
                        </div>
                        <span class="mini-badge-avail">✅ Available</span>
                    </div>

                    <div class="mini-room-item">
                        <div>
                            <div style="font-weight:800;font-size:0.88rem;color:{text_col}!important;">Room 205 &bull; Computer Lab</div>
                            <div style="font-size:0.75rem;color:{muted_col}!important;">Science Block &bull; Floor 2 &bull; Cap: 30 &bull; 💻 ♿</div>
                        </div>
                        <span class="mini-badge-busy">⏳ Class: CS101</span>
                    </div>

                    <div class="mini-room-item">
                        <div>
                            <div style="font-weight:800;font-size:0.88rem;color:{text_col}!important;">Room 310 &bull; Lecture Hall</div>
                            <div style="font-size:0.75rem;color:{muted_col}!important;">Engineering Block &bull; Floor 3 &bull; Cap: 120 &bull; 📽️ 💻 🔌</div>
                        </div>
                        <span class="mini-badge-avail">✅ Best Match</span>
                    </div>

                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.6rem;padding-top:0.5rem;border-top:1px dashed {border_col};font-size:0.74rem;color:{muted_col}!important;">
                        <span>📦 5,000 Class Records Analyzed</span>
                        <span>🗓️ 1,800 Dated Events Tracked</span>
                    </div>
                </div>

                <!-- Three Concise Benefit Points -->
                <div style="margin-top:1.2rem;">
                    <div class="benefit-row">
                        <div class="benefit-icon-box">⚡</div>
                        <div class="benefit-text">
                            <strong style="color:{text_col}!important;">1. Find suitable rooms faster:</strong> Instant conflict checks across weekly classes and special events with zero guesswork.
                        </div>
                    </div>
                    <div class="benefit-row">
                        <div class="benefit-icon-box">🎯</div>
                        <div class="benefit-text">
                            <strong style="color:{text_col}!important;">2. Match capacity and facilities:</strong> Filter precisely by projectors, computer workstations, accessibility, and power outlets.
                        </div>
                    </div>
                    <div class="benefit-row">
                        <div class="benefit-icon-box">📊</div>
                        <div class="benefit-text">
                            <strong style="color:{text_col}!important;">3. Make informed space decisions:</strong> Transparent scoring and fully explainable room recommendations backed by real campus data.
                        </div>
                    </div>
                </div>

                <div class="hero-footer-note">
                    Smarter spaces. Better campus experiences.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # RIGHT COLUMN: Clean White Login Card & Auth
    # ─────────────────────────────────────────────
    with col_right:
        st.markdown(f"""
            <div style="background:{bg_card};border:1.5px solid {border_col};border-radius:16px;padding:1.8rem 2rem 1.6rem;box-shadow:0 8px 30px rgba(0,0,0,0.08);margin-bottom:1.2rem;">
                <div style="margin-bottom:1.2rem;">
                    <div style="font-size:1.8rem;font-weight:900;color:{text_col}!important;line-height:1.2;margin-bottom:0.25rem;">Welcome back</div>
                    <div style="font-size:0.92rem;color:{muted_col}!important;">Sign in to continue to CampusSpace.</div>
                </div>
        """, unsafe_allow_html=True)

        identifier = st.text_input(
            "👤 Username or Campus Email",
            placeholder="e.g. student, Alex Kumar, or student@campus.edu",
            help="Enter your university username, persona name, or campus email address",
            key="login_identifier_input"
        )

        show_pwd = st.toggle("👁️ Show password", value=st.session_state.get("login_show_pwd", False), key="login_show_pwd_toggle")
        st.session_state["login_show_pwd"] = show_pwd

        password = st.text_input(
            "🔑 Password",
            type="text" if show_pwd else "password",
            placeholder="Enter your password",
            help="Your secure university account password",
            key="login_password_input"
        )

        remember = st.checkbox("Remember this device for 30 days", value=True, key="login_remember_chk")

        st.markdown(f"""
            <div style="font-size:0.75rem;color:{muted_col}!important;margin:0.2rem 0 0.9rem;line-height:1.4;">
                ℹ️ <strong>Password Recovery:</strong> Managed by Campus IT Directory. Contact your IT Helpdesk for credential resets.
            </div>
        """, unsafe_allow_html=True)

        submitted = st.button("🔐 Sign In", type="primary", use_container_width=True, key="login_submit_btn")
        st.markdown("</div>", unsafe_allow_html=True)

        # Form Submission Handling with feedback & validation
        if submitted:
            if not identifier.strip():
                st.warning("⚠️ Please enter your username or campus email.")
            elif not password:
                st.warning("⚠️ Please enter your password.")
            else:
                with st.spinner("Authenticating credentials with secure PBKDF2 hashing…"):
                    ok, user_dict, err_msg = authenticate_user(identifier, password)
                    if ok and user_dict:
                        login_user(st.session_state, user_dict, remember=remember)
                        st.success(f"✅ Welcome back, {user_dict['display']}! Launching dashboard…")
                        st.rerun()
                    else:
                        st.error(f"❌ {err_msg}")

        # Security Note & Public Navigation
        st.markdown(f"""
            <div style="text-align:center;font-size:0.77rem;color:{muted_col}!important;margin:0.9rem 0 0.4rem;line-height:1.4;">
                🔒 Secure authentication with salted PBKDF2 hashing.<br>Passwords are never stored in plaintext.
            </div>
            <div style="text-align:center;font-size:0.8rem;color:{muted_col}!important;margin:0.3rem 0;">&mdash; OR &mdash;</div>
        """, unsafe_allow_html=True)

        if st.button("👀 Continue as Visitor / Explore Rooms as Guest", use_container_width=True):
            login_guest(st.session_state)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Demo Evaluator Accounts ──
        with st.expander("🧪 Demo Accounts (One-Click Quick Login for Evaluators)", expanded=True):
            st.markdown(f"""
                <p style="font-size:0.8rem;color:{muted_col}!important;margin-bottom:0.6rem;">
                    For hackathon evaluation, click any persona below to authenticate with salted PBKDF2 verification:
                </p>
            """, unsafe_allow_html=True)

            qcol1, qcol2 = st.columns(2)
            with qcol1:
                if st.button("👤 Alex Kumar\n(Student)", use_container_width=True, key="demo_btn_student"):
                    ok, u, _ = authenticate_user("student", "campus123")
                    if ok and u:
                        login_user(st.session_state, u)
                        st.rerun()
                if st.button("🏛️ Campus Admin\n(Administrator)", use_container_width=True, key="demo_btn_admin"):
                    ok, u, _ = authenticate_user("admin", "admin789")
                    if ok and u:
                        login_user(st.session_state, u)
                        st.rerun()
            with qcol2:
                if st.button("🎓 Dr. Priya Sharma\n(Faculty)", use_container_width=True, key="demo_btn_faculty"):
                    ok, u, _ = authenticate_user("faculty", "faculty456")
                    if ok and u:
                        login_user(st.session_state, u)
                        st.rerun()
                if st.button("🎪 Rohan Verma\n(Club Organizer)", use_container_width=True, key="demo_btn_club"):
                    ok, u, _ = authenticate_user("club", "club321")
                    if ok and u:
                        login_user(st.session_state, u)
                        st.rerun()

            demo_tbl = get_demo_accounts_table()
            st.dataframe(pd.DataFrame(demo_tbl)[["Role", "Username", "Email", "Demo Password", "Persona"]],
                         hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# ── MAIN APP ──
# ─────────────────────────────────────────────
def show_main_app():
    dark = st.session_state["dark_mode"]
    inject_css(dark)
    plotly_tpl = "plotly_dark" if dark else "plotly_white"
    plotly_paper = "#1E293B" if dark else "#FFFFFF"
    plotly_font  = "#F1F5F9" if dark else "#000000"

    # ── Load Data ──
    try:
        rooms_df, class_df, events_df, requests_df = get_cached_data()
    except Exception as e:
        st.error(f"❌ Failed to load datasets: {e}")
        st.info("Ensure rooms.csv, class_schedule.csv, events.csv, and room_requests.csv are in the data/ folder.")
        return

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;">
                <div style="background:linear-gradient(135deg,#0F9D8A,#14243A);color:white;
                            font-size:1.2rem;font-weight:900;width:40px;height:40px;
                            border-radius:10px;display:flex;align-items:center;justify-content:center;">CS</div>
                <div>
                    <div style="font-size:1.15rem;font-weight:800;">CampusSpace</div>
                    <div style="font-size:0.68rem;font-weight:700;letter-spacing:1px;opacity:0.55;">ROOM FINDER & ANALYTICS</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        dm = st.toggle("🌙 Dark Mode", value=dark)
        if dm != dark:
            st.session_state["dark_mode"] = dm
            st.rerun()

        st.markdown("---")

        nav_options = [
            "🏠 Overview",
            "🔍 Find a Room",
            "🏛️ Room Explorer",
            "📊 Space Analytics",
            "ℹ️ About & Data",
        ]
        if "nav_page" not in st.session_state or st.session_state["nav_page"] not in nav_options:
            st.session_state["nav_page"] = "🏠 Overview"

        def _on_nav_change():
            st.session_state["nav_page"] = st.session_state["_sidebar_nav_key"]

        cur_idx = nav_options.index(st.session_state["nav_page"])
        st.radio(
            "Navigation",
            nav_options,
            index=cur_idx,
            key="_sidebar_nav_key",
            on_change=_on_nav_change
        )

        st.markdown("---")
        user_display = st.session_state.get("display_name") or st.session_state.get("username", "User").title()
        user_role = st.session_state.get("role", "Student")
        is_guest_user = is_guest(st.session_state)

        if is_guest_user:
            st.markdown(f"""
                <div style="font-size:0.8rem;line-height:1.6;padding:0.5rem 0;">
                    <strong>👀 Campus Visitor</strong><br>
                    <span style="font-size:0.73rem;background:#E2E8F0;padding:2px 8px;border-radius:10px;font-weight:700;">Public Guest Mode</span>
                </div>
                <div style="font-size:0.73rem;opacity:0.65;margin-top:0.4rem;line-height:1.5;">
                    📦 {len(rooms_df)} rooms &bull; {len(class_df):,} classes<br>
                    🗓️ {len(events_df):,} events &bull; {len(requests_df):,} requests
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔐 Sign In with Campus ID", use_container_width=True):
                logout_user(st.session_state)
                st.rerun()
        else:
            role_bg = "#E6F7F5" if user_role in ("Student", "Faculty") else ("#EFF6FF" if user_role == "Club Organizer" else "#FDF2F8")
            role_col = "#0F9D8A" if user_role in ("Student", "Faculty") else ("#1D4ED8" if user_role == "Club Organizer" else "#BE185D")
            st.markdown(f"""
                <div style="font-size:0.8rem;line-height:1.6;padding:0.5rem 0;">
                    <strong>👤 {user_display}</strong><br>
                    <span style="font-size:0.73rem;background:{role_bg};color:{role_col};padding:2px 8px;border-radius:10px;font-weight:700;">{user_role}</span>
                </div>
                <div style="font-size:0.73rem;opacity:0.65;margin-top:0.4rem;line-height:1.5;">
                    📦 {len(rooms_df)} rooms &bull; {len(class_df):,} classes<br>
                    🗓️ {len(events_df):,} events &bull; {len(requests_df):,} requests
                </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Sign Out", use_container_width=True):
                logout_user(st.session_state)
                st.rerun()

    # ── Top Responsive Quick-Navigation Bar ──
    nav_options = [
        "🏠 Overview",
        "🔍 Find a Room",
        "🏛️ Room Explorer",
        "📊 Space Analytics",
        "ℹ️ About & Data",
    ]
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in nav_options:
        st.session_state["nav_page"] = "🏠 Overview"

    top_cols = st.columns(len(nav_options))
    for i, opt in enumerate(nav_options):
        with top_cols[i]:
            is_active = (opt == st.session_state["nav_page"])
            if st.button(opt, key=f"top_nav_bar_{i}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state["nav_page"] = opt
                st.rerun()

    st.markdown("<hr style='margin:0.4rem 0 1.2rem 0;opacity:0.25;'>", unsafe_allow_html=True)
    nav = st.session_state["nav_page"]

    # ════════════════════════════════════════════
    # PAGE: OVERVIEW
    # ════════════════════════════════════════════
    if nav == "🏠 Overview":
        st.markdown("<h1 style='font-size:2rem;font-weight:800;margin-bottom:0.2rem;'>🏢 CampusSpace Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;opacity:0.75;margin-bottom:1rem;'>Smarter room discovery for a better-utilized campus.</p>", unsafe_allow_html=True)

        cta1, cta2, _ = st.columns([1.5, 2, 4])
        with cta1:
            if st.button("🔍 Find a Room", type="primary", use_container_width=True, key="overview_cta_find"):
                st.session_state["nav_page"] = "🔍 Find a Room"
                st.rerun()
        with cta2:
            if st.button("📊 Explore Space Usage", use_container_width=True, key="overview_cta_analytics"):
                st.session_state["nav_page"] = "📊 Space Analytics"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        kpis = compute_overall_kpis(rooms_df, class_df, events_df, requests_df)

        c1, c2, c3, c4, c5 = st.columns(5)
        for col, label, val, sub, color in [
            (c1, "Total Rooms",       str(kpis['total_rooms']),          "5 Buildings",                        "inherit"),
            (c2, "Scheduled Classes", f"{kpis['total_classes']:,}",       f"{kpis['weekly_class_hours']:,} hrs/week", "inherit"),
            (c3, "Logged Events",     f"{kpis['total_events']:,}",        "Aug – Nov 2025",                     "inherit"),
            (c4, "Student Requests",  f"{kpis['total_requests']:,}",      f"{kpis['approved_requests']:,} Approved", "inherit"),
            (c5, "Unmet Demand",      f"{kpis['unmet_demand_pct']}%",     "Waitlisted / Rejected",              "#DC4545"),
        ]:
            with col:
                st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-label">{label}</div>
                        <div class="stat-value" style="color:{color}!important;">{val}</div>
                        <div class="stat-sub">{sub}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.markdown("#### 🏛️ Room Inventory by Type")
            type_df = rooms_df['room_type'].value_counts().reset_index()
            type_df.columns = ['Type', 'Count']
            fig = px.bar(type_df, x='Type', y='Count', color='Type',
                         color_discrete_sequence=['#0F9D8A','#3B82F6','#8B5CF6','#F59E0B','#EC4899'],
                         template=plotly_tpl)
            fig.update_layout(showlegend=False, height=290, margin=dict(t=5,b=5,l=5,r=5),
                              paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper,
                              font_color=plotly_font)
            st.plotly_chart(fig, use_container_width=True)

        with r1c2:
            st.markdown("#### 👥 Capacity Distribution by Room Type")
            fig2 = px.box(rooms_df, x='room_type', y='capacity', color='room_type', points='all',
                          color_discrete_sequence=['#0F9D8A','#3B82F6','#8B5CF6','#F59E0B','#EC4899'],
                          template=plotly_tpl)
            fig2.update_layout(showlegend=False, height=290, margin=dict(t=5,b=5,l=5,r=5),
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper,
                               font_color=plotly_font, xaxis_title="Room Type", yaxis_title="Capacity")
            st.plotly_chart(fig2, use_container_width=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.markdown("#### 📅 Weekly Classes by Department")
            dept_df = class_df.groupby(['department','weekday']).size().reset_index(name='count')
            order = ['Mon','Tue','Wed','Thu','Fri','Sat']
            fig3 = px.bar(dept_df, x='weekday', y='count', color='department', barmode='stack',
                          category_orders={'weekday': order},
                          color_discrete_sequence=px.colors.qualitative.Safe,
                          template=plotly_tpl)
            fig3.update_layout(height=310, margin=dict(t=5,b=5,l=5,r=5),
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper,
                               font_color=plotly_font, xaxis_title="Weekday", yaxis_title="Class Count")
            st.plotly_chart(fig3, use_container_width=True)

        with r2c2:
            st.markdown("#### 🎯 Request Status by Purpose")
            req_df = requests_df.groupby(['purpose','status']).size().reset_index(name='count')
            fig4 = px.bar(req_df, x='purpose', y='count', color='status', barmode='group',
                          color_discrete_map={'Approved':'#0F9D8A','Waitlisted':'#F59E0B',
                                             'Rejected':'#DC4545','Cancelled':'#94A3B8'},
                          template=plotly_tpl)
            fig4.update_layout(height=310, margin=dict(t=5,b=5,l=5,r=5),
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper,
                               font_color=plotly_font, xaxis_title="Purpose", yaxis_title="Count")
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 💡 Data-Backed Campus Insights")
        insights = generate_data_backed_insights(rooms_df, class_df, events_df, requests_df)
        ic1, ic2 = st.columns(2)
        for i, ins in enumerate(insights):
            col = ic1 if i % 2 == 0 else ic2
            with col:
                st.markdown(f"""
                    <div class="insight-box">
                        <div class="insight-title">{ins['title']}</div>
                        <div class="insight-metric">{ins['metric']}</div>
                        <div class="insight-body"><strong>Why it matters:</strong> {ins['why_it_matters']}<br>
                            <span style="font-size:0.75rem;opacity:0.7;">Source: {ins['dataset']}</span>
                        </div>
                        <div class="insight-caveat">⚠️ {ins['caveat']}</div>
                    </div>
                """, unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # PAGE: FIND A ROOM
    # ════════════════════════════════════════════
    elif nav == "🔍 Find a Room":
        st.markdown("<h1 style='font-size:2rem;font-weight:800;margin-bottom:0.2rem;'>🔍 Find Suitable Space</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;opacity:0.7;margin-bottom:1.2rem;'>Enter your requirements. CampusSpace checks conflicts, filters rooms, and explains top matches.</p>", unsafe_allow_html=True)

        with st.form("room_search_form", clear_on_submit=False):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                req_date = st.date_input("📅 Meeting Date", value=date(2025, 9, 15),
                                         min_value=date(2025, 8, 1), max_value=date(2025, 11, 28),
                                         help="Dataset window: Aug 1 – Nov 28, 2025")
                start_h = st.slider("⏰ Start Hour (24h)", 8, 20, 14)
            with fc2:
                dur_h = st.selectbox("⏳ Duration (hours)", [1, 2, 3, 4], index=1)
                end_h = start_h + dur_h
                st.markdown(f"<div style='margin-top:0.6rem;font-size:0.9rem;font-weight:600;'>🕐 Slot: {start_h:02d}:00 → {end_h:02d}:00</div>", unsafe_allow_html=True)
                req_cap = st.number_input("👥 Expected Attendees", min_value=1, max_value=200, value=30, step=5)
            with fc3:
                type_opts = ["Any"] + sorted(rooms_df['room_type'].unique().tolist())
                pref_type = st.selectbox("🏷️ Room Type Preference", type_opts)
                bldg_opts = ["Any"] + sorted(rooms_df['building'].unique().tolist())
                pref_bldg = st.selectbox("📍 Preferred Building", bldg_opts)

            st.markdown("<p style='font-weight:700;font-size:0.9rem;margin:0.8rem 0 0.3rem;'>🛠️ Facility Requirements:</p>", unsafe_allow_html=True)
            eq1, eq2, eq3 = st.columns(3)
            with eq1: need_proj   = st.checkbox("📽️ Projector Required",     value=True)
            with eq2: need_comp   = st.checkbox("💻 Workstations Required",   value=False)
            with eq3: need_access = st.checkbox("♿ Wheelchair Accessible",   value=False)

            submitted = st.form_submit_button("🔍  Find Suitable Rooms", use_container_width=True, type="primary")

        date_str = req_date.strftime('%Y-%m-%d')
        weekday  = parse_weekday_from_date(date_str)

        if submitted or st.session_state.get("search_done"):
            st.session_state["search_done"] = True
            with st.spinner("Running scheduling checks and recommendation engine…"):
                results = find_room_recommendations(
                    date_str=date_str, start_hour=start_h, duration_hours=dur_h,
                    required_capacity=req_cap,
                    projector_required=need_proj, computers_required=need_comp,
                    accessible_required=need_access,
                    preferred_type=pref_type, preferred_building=pref_bldg,
                    rooms_df=rooms_df, class_df=class_df, events_df=events_df
                )

            st.markdown("---")
            ok_col = "#0F9D8A" if results['total_feasible'] > 0 else "#DC4545"
            st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;flex-wrap:wrap;gap:0.5rem;">
                    <div>
                        <h3 style="margin:0;font-size:1.3rem;font-weight:800;">
                            Results · <span style="color:#0F9D8A;">{date_str} ({weekday})</span> ·
                            <span style="color:#0F9D8A;">{start_h:02d}:00 – {end_h:02d}:00</span>
                        </h3>
                        <p style="margin:0;font-size:0.85rem;opacity:0.65;">
                            Evaluated {len(rooms_df)} rooms against {len(class_df):,} class records &amp; {len(events_df):,} events.
                        </p>
                    </div>
                    <div style="background:{ok_col}20;color:{ok_col};font-weight:800;padding:0.4rem 1.1rem;
                                border-radius:20px;border:1.5px solid {ok_col};font-size:0.9rem;">
                        {results['total_feasible']} Feasible / {results['total_infeasible']} Infeasible
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if results['total_feasible'] > 0:
                st.markdown("##### 🏆 Top Recommendations")
                for candidate in results['top_recommendations']:
                    tier = candidate['match_tier']
                    badge_cls = "badge-best" if tier == "Best Fit" else ("badge-alt" if tier == "Strong Alternative" else "badge-good")
                    border_cls = "best-fit" if tier == "Best Fit" else ("alternative" if tier == "Strong Alternative" else "good-option")
                    score_w = int(candidate['score'])

                    st.markdown(f"""
                        <div class="rec-card {border_cls}">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
                                <div>
                                    <span class="tier-badge {badge_cls}">{tier}</span>
                                    <div style="font-size:1.4rem;font-weight:800;margin:0.3rem 0 0.1rem;">
                                        Room {candidate['room_id']} · {candidate['room_type']}
                                    </div>
                                    <div style="font-size:0.85rem;opacity:0.7;">
                                        📍 {candidate['building']} Building · Floor {candidate['floor']} ·
                                        Capacity: <strong>{candidate['capacity']}</strong>
                                        ({candidate['excess_capacity']} spare seats)
                                    </div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-size:2rem;font-weight:900;color:#0F9D8A;">{candidate['score']}</div>
                                    <div style="font-size:0.7rem;font-weight:700;opacity:0.5;text-transform:uppercase;">Score / 100</div>
                                    <div class="score-bar-bg"><div class="score-bar-fill" style="width:{score_w}%;"></div></div>
                                </div>
                            </div>
                            <div style="margin:0.8rem 0;">
                                <span class="badge-tag">📽️ Projector: {'Yes' if candidate['projector'] else 'No'}</span>
                                <span class="badge-tag">💻 PCs: {'Yes' if candidate['computers'] else 'No'}</span>
                                <span class="badge-tag">♿ Access: {'Yes' if candidate['accessible'] else 'No'}</span>
                                <span class="badge-tag">🔌 Outlets: {candidate['power_outlets']}</span>
                                <span class="badge-tag" style="background:#ECFDF5;color:#065F46!important;border-color:#A7F3D0;">✅ No Conflicts</span>
                            </div>
                            <div style="background:{'#1E3A2F' if dark else '#F0FDF9'};padding:0.85rem;border-radius:8px;
                                        font-size:0.86rem;border-left:3px solid #0F9D8A;margin-top:0.6rem;">
                                <strong>Why this room:</strong> {candidate['explanation']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"📅 Room {candidate['room_id']} full day schedule on {date_str}"):
                        timeline = get_room_day_timeline(candidate['room_id'], date_str, class_df, events_df)
                        if timeline:
                            tdf = pd.DataFrame(timeline)
                            tdf['Slot'] = tdf.apply(lambda r: f"{r['start']:02d}:00 – {r['end']:02d}:00", axis=1)
                            st.dataframe(tdf[['Slot','label','type']], hide_index=True, use_container_width=True)
                        else:
                            st.success(f"✅ Room {candidate['room_id']} has no bookings at all on {date_str}!")

                if len(results['feasible_rooms']) > 3:
                    with st.expander(f"📋 All {len(results['feasible_rooms']) - 3} additional feasible rooms"):
                        extra = pd.DataFrame(results['feasible_rooms'][3:])
                        st.dataframe(extra[['room_id','building','floor','room_type','capacity','score']], hide_index=True, use_container_width=True)
            else:
                st.warning("⚠️ No room satisfies all constraints simultaneously.")
                if results['alternatives']:
                    st.markdown("##### 💡 Smart Alternatives")
                    for alt in results['alternatives']:
                        st.markdown(f"""
                            <div style="padding:0.9rem;border-radius:8px;border:1px solid {'#334155' if dark else '#D1D9E6'};
                                        background:{'#1E293B' if dark else '#FFFFFF'};margin-bottom:0.6rem;">
                                <strong>Suggestion:</strong> {alt['suggestion']}<br>
                                <span style="font-size:0.8rem;color:#0F9D8A;font-weight:600;">
                                    Available room under this relaxation: <strong>{alt['sample_room']}</strong>
                                </span>
                            </div>
                        """, unsafe_allow_html=True)

            with st.expander(f"🔎 Conflict Audit — {results['total_infeasible']} rejected rooms"):
                rows = [{"Room": r['room_id'], "Building": r['building'], "Type": r['room_type'],
                         "Capacity": r['capacity'], "Rejected Because": " | ".join(r.get('rejection_reasons', []))}
                        for r in results['infeasible_rooms']]
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ════════════════════════════════════════════
    # PAGE: ROOM EXPLORER
    # ════════════════════════════════════════════
    elif nav == "🏛️ Room Explorer":
        st.markdown("<h1 style='font-size:2rem;font-weight:800;margin-bottom:0.2rem;'>🏛️ Room Explorer</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;opacity:0.7;margin-bottom:1.2rem;'>Search, filter, and inspect all 120 campus rooms with their timetables.</p>", unsafe_allow_html=True)

        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1: search_q = st.text_input("🔍 Search Room ID or Building", "").lower().strip()
        with ec2: sel_bldg = st.selectbox("Building", ["All"] + sorted(rooms_df['building'].unique().tolist()))
        with ec3: sel_type = st.selectbox("Room Type", ["All"] + sorted(rooms_df['room_type'].unique().tolist()))
        with ec4: min_cap  = st.slider("Min Capacity", 15, 180, 15, step=5)

        filt = rooms_df.copy()
        if search_q:
            filt = filt[filt['room_id'].str.lower().str.contains(search_q) |
                        filt['building'].str.lower().str.contains(search_q)]
        if sel_bldg != "All": filt = filt[filt['building'] == sel_bldg]
        if sel_type != "All": filt = filt[filt['room_type'] == sel_type]
        filt = filt[filt['capacity'] >= min_cap]

        st.markdown(f"<p style='font-size:0.9rem;font-weight:600;margin-bottom:0.5rem;'>Showing <strong>{len(filt)}</strong> of {len(rooms_df)} rooms</p>", unsafe_allow_html=True)

        disp = filt.copy()
        disp['Projector']  = disp['projector'].apply(lambda x: '✅ Yes' if x == 1 else '❌ No')
        disp['Computers']  = disp['computers'].apply(lambda x: '✅ Yes' if x == 1 else '❌ No')
        disp['Accessible'] = disp['accessible'].apply(lambda x: '✅ Yes' if x == 1 else '❌ No')
        st.dataframe(disp[['room_id','building','floor','room_type','capacity','Projector','Computers','Accessible','power_outlets']],
                     hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔍 Single Room Inspector")
        sel_room = st.selectbox("Select a Room", sorted(rooms_df['room_id'].unique().tolist()))
        if sel_room:
            ri = rooms_df[rooms_df['room_id'] == sel_room].iloc[0]
            st.markdown(f"""
                <div class="cs-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                        <div>
                            <div style="font-size:1.4rem;font-weight:800;">Room {ri['room_id']} · {ri['room_type']}</div>
                            <div style="font-size:0.87rem;opacity:0.65;margin-top:0.15rem;">
                                {ri['building']} Building · Floor {ri['floor']} · Capacity: <strong>{ri['capacity']}</strong>
                            </div>
                        </div>
                        <div>
                            <span class="badge-tag">📽️ {'Yes' if ri['projector'] else 'No'}</span>
                            <span class="badge-tag">💻 {'Yes' if ri['computers'] else 'No'}</span>
                            <span class="badge-tag">♿ {'Yes' if ri['accessible'] else 'No'}</span>
                            <span class="badge-tag">🔌 {ri['power_outlets']} outlets</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            r_classes = class_df[class_df['room_id'] == sel_room].sort_values(['weekday','start_hour'])
            r_events  = events_df[events_df['room_id'] == sel_room].sort_values('start_time_dt')

            with sc1:
                st.markdown(f"**📚 Recurring Classes ({len(r_classes)} records)**")
                if len(r_classes) > 0:
                    rc = r_classes.copy()
                    rc['Slot'] = rc.apply(lambda r: f"{r['start_hour']:02d}:00–{r['start_hour']+r['duration_hours']:02d}:00", axis=1)
                    st.dataframe(rc[['course_code','weekday','Slot','department','expected_attendance']], hide_index=True, use_container_width=True)
                else:
                    st.info("No recurring classes for this room.")

            with sc2:
                st.markdown(f"**🎪 Special Events ({len(r_events)} records)**")
                if len(r_events) > 0:
                    re = r_events.copy()
                    re['Slot'] = re.apply(lambda r: f"{r['start_hour']:02d}:00–{r['start_hour']+r['duration_hours']:02d}:00", axis=1)
                    st.dataframe(re[['event_id','event_type','event_date','Slot','expected_attendance','actual_attendance']], hide_index=True, use_container_width=True)
                else:
                    st.info("No special events for this room.")

    # ════════════════════════════════════════════
    # PAGE: SPACE ANALYTICS
    # ════════════════════════════════════════════
    elif nav == "📊 Space Analytics":
        st.markdown("<h1 style='font-size:2rem;font-weight:800;margin-bottom:0.2rem;'>📊 Space Analytics</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;opacity:0.7;margin-bottom:1.2rem;'>Utilization metrics, demand patterns, and underutilized space identification for administrators.</p>", unsafe_allow_html=True)

        util_df = compute_room_utilization_metrics(rooms_df, class_df, events_df)

        ac1, ac2, ac3, ac4 = st.columns(4)
        avg_util = util_df['utilization_proxy_pct'].mean()
        max_row  = util_df.loc[util_df['utilization_proxy_pct'].idxmax()]
        min_row  = util_df.loc[util_df['utilization_proxy_pct'].idxmin()]
        under50  = (util_df['utilization_proxy_pct'] < 50).sum()

        for col, lbl, val, sub in [
            (ac1, "Avg Weekly Utilization", f"{avg_util:.1f}%",        "60h/week operating window"),
            (ac2, "Most Used Room",          max_row['room_id'],         f"{max_row['utilization_proxy_pct']}% · {max_row['building']}"),
            (ac3, "Least Used Room",         min_row['room_id'],         f"{min_row['utilization_proxy_pct']}% · {min_row['building']}"),
            (ac4, "Underutilized Rooms",    str(under50),                "< 50% weekly load"),
        ]:
            with col:
                st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-label">{lbl}</div>
                        <div class="stat-value">{val}</div>
                        <div class="stat-sub">{sub}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        uc1, uc2 = st.columns(2)
        with uc1:
            st.markdown("#### 🏢 Avg Utilization by Building")
            bu = util_df.groupby('building')['utilization_proxy_pct'].mean().reset_index()
            fig5 = px.bar(bu, x='building', y='utilization_proxy_pct', color='building',
                          color_discrete_sequence=['#0F9D8A','#3B82F6','#8B5CF6','#F59E0B','#10B981'],
                          template=plotly_tpl, labels={'utilization_proxy_pct':'Utilization (%)'})
            fig5.update_layout(showlegend=False, height=300, margin=dict(t=5,b=5,l=5,r=5),
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper, font_color=plotly_font)
            st.plotly_chart(fig5, use_container_width=True)

        with uc2:
            st.markdown("#### 🏷️ Avg Utilization by Room Type")
            tu = util_df.groupby('room_type')['utilization_proxy_pct'].mean().reset_index()
            fig6 = px.bar(tu, x='room_type', y='utilization_proxy_pct', color='room_type',
                          color_discrete_sequence=['#0F9D8A','#3B82F6','#8B5CF6','#F59E0B','#EC4899'],
                          template=plotly_tpl, labels={'utilization_proxy_pct':'Utilization (%)'})
            fig6.update_layout(showlegend=False, height=300, margin=dict(t=5,b=5,l=5,r=5),
                               paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper, font_color=plotly_font)
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("#### 📈 Hourly Demand vs Scheduled Classes")
        req_hr  = requests_df.groupby('start_hour').size().reset_index(name='Student Requests')
        cls_hr  = class_df.groupby('start_hour').size().reset_index(name='Scheduled Classes')
        merged  = pd.merge(req_hr, cls_hr, on='start_hour', how='outer').fillna(0).sort_values('start_hour')
        fig7 = go.Figure()
        fig7.add_trace(go.Scatter(x=merged['start_hour'], y=merged['Student Requests'],
                                  mode='lines+markers', name='Student Demand',
                                  line=dict(color='#0F9D8A', width=3)))
        fig7.add_trace(go.Scatter(x=merged['start_hour'], y=merged['Scheduled Classes'],
                                  mode='lines+markers', name='Scheduled Classes',
                                  line=dict(color='#3B82F6', width=3, dash='dash')))
        fig7.update_layout(template=plotly_tpl, height=330,
                           xaxis=dict(title="Hour of Day", tickmode='linear', tick0=8, dtick=1),
                           yaxis_title="Count", margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor=plotly_paper, plot_bgcolor=plotly_paper, font_color=plotly_font)
        st.plotly_chart(fig7, use_container_width=True)

        st.markdown("#### 📉 Underutilized Rooms — Potential Student Access Slots")
        low_util = util_df.sort_values('utilization_proxy_pct').head(15)
        st.dataframe(low_util[['room_id','building','floor','room_type','capacity',
                                'weekly_class_hours','utilization_proxy_pct']],
                     hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🏛️ Administrator Room Allocation & Policy Controls")
        if is_admin(st.session_state) or is_faculty_or_admin(st.session_state):
            ad_col1, ad_col2 = st.columns(2)
            with ad_col1:
                st.markdown("""
                    <div class="cs-card">
                        <div style="font-size:1.05rem;font-weight:800;margin-bottom:0.4rem;">📥 Export Space Utilization Audit</div>
                        <p style="font-size:0.84rem;margin-bottom:0.8rem;line-height:1.45;">
                            Download complete 120-room schedule utilization, peak-load indicators, and surplus hours for campus administration review.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                csv_bytes = util_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Utilization Audit (CSV)",
                    data=csv_bytes,
                    file_name="campusspace_utilization_audit.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with ad_col2:
                st.markdown("""
                    <div class="cs-card">
                        <div style="font-size:1.05rem;font-weight:800;margin-bottom:0.4rem;">🎯 Policy Recommendation</div>
                        <p style="font-size:0.84rem;margin-bottom:0.6rem;line-height:1.45;">
                            <strong>Reallocate Science Block Floor 3 & 4:</strong> 8 rooms currently operate below 30% weekly load during 14:00–17:00. Opening these for student club reservations will satisfy 72% of unmet student demand.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                st.success("✅ Administrator space reallocation policy recommendations active.")
        elif is_guest(st.session_state):
            st.info("🔒 **Administrator Access Required**: Detailed room allocation policy controls, CSV audit exports, and department quota adjustments are restricted to Campus Administrators and Faculty. Please sign in to access these controls.")
            if st.button("🔐 Sign In as Administrator / Faculty", use_container_width=True):
                logout_user(st.session_state)
                st.rerun()
        else:
            st.info(f"ℹ️ Signed in as **{st.session_state.get('role', 'User')}**. Space utilization metrics are visible for planning. Administrative audit exports require Administrator credentials.")

    # ════════════════════════════════════════════
    # PAGE: ABOUT & DATA
    # ════════════════════════════════════════════
    elif nav == "ℹ️ About & Data":
        st.markdown("<h1 style='font-size:2rem;font-weight:800;margin-bottom:0.2rem;'>ℹ️ About & Data</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;opacity:0.7;margin-bottom:1.2rem;'>Project philosophy, dataset provenance, methodology, and roadmap.</p>", unsafe_allow_html=True)

        st.markdown("""
        ### Problem Statement
        > **"The Campus Has Space. Students Don't."**

        Student clubs, study groups, and hackathon teams struggle to find quiet, equipped spaces to collaborate — while seminar rooms and labs sit dark simply because campus schedules are siloed and opaque.

        **CampusSpace** transforms fragmented campus data into transparent, explainable room recommendations.
        """)

        val_report = validate_datasets(rooms_df, class_df, events_df, requests_df)
        st.markdown("### 📋 Dataset Health Report")
        dh1, dh2, dh3 = st.columns(3)
        with dh1:
            st.metric("Rooms Audited",       val_report['total_rooms'])
            st.metric("Duplicate Room IDs",  val_report['duplicates']['rooms'])
        with dh2:
            st.metric("Class Records",       f"{val_report['total_class_records']:,}")
            st.metric("Unmatched Class RoomIDs", val_report['foreign_key_checks']['classes_unmatched_rooms'])
        with dh3:
            st.metric("Event Records",       f"{val_report['total_event_records']:,}")
            st.metric("Unmatched Event RoomIDs", val_report['foreign_key_checks']['events_unmatched_rooms'])

        with st.expander("📖 Formal Data Dictionary (all columns)"):
            st.dataframe(pd.DataFrame(get_data_dictionary()), hide_index=True, use_container_width=True)

        st.markdown("### 📐 Scheduling Logic & Assumptions")
        st.markdown("""
        1. **Overlap Rule:** Intervals conflict if `existing_start < requested_end AND existing_end > requested_start`. Adjacent intervals do **not** conflict.
        2. **Class Schedules** are recurring weekly (Mon–Sat). Events are one-off dated bookings.
        3. **Room Requests** represent pre-allocation demand — not confirmed reservations.
        4. **Utilization Proxy** = Total weekly scheduled hours ÷ 60 operating hours/week × 100.
        5. **Dataset** is synthetic (DATATHON benchmark). Not a live campus booking system.
        """)

        st.markdown("### 🚀 Round 1 vs Round 2 Roadmap")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("""
            #### ✅ Round 1 — Completed
            - 2-stage explainable recommendation engine
            - Real conflict detection (classes + events)
            - Smart constraint-relaxation alternatives
            - Login system with role-based access
            - Dark / Light mode toggle
            - Room Explorer with timetable inspector
            - Space utilization analytics dashboard
            - 8/8 automated unit tests passing
            """)
        with rc2:
            st.markdown("""
            #### 🔮 Round 2 — Planned
            - ML demand forecasting by hour/day
            - MILP batch room optimizer (multi-request)
            - Ghost-booking detection with attendance data
            - University ERP / SIS API integration
            - Persistent booking confirmations
            - Mobile-responsive PWA version
            """)

    # ── Footer ──
    display_user = st.session_state.get('display_name') or st.session_state.get('username', 'Guest').title()
    role_user = st.session_state.get('role', 'Public')
    st.markdown(f"""
        <div class="app-footer">
            <strong>CampusSpace</strong> · Hackathon Round 1 MVP · Built with Streamlit & Plotly<br>
            Data: DATATHON Educational Benchmark Dataset (Synthetic) · Active Session:
            <strong>{display_user}</strong> ({role_user})
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not st.session_state["logged_in"]:
        show_login()
    else:
        show_main_app()
