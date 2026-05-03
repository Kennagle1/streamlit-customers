from __future__ import annotations

import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from rapidfuzz import fuzz
from datetime import datetime
import io
import re
import difflib
import json
from html import escape as html_escape
from openai import OpenAI
import openai
import traceback

# -----------------------------------------------
# PAGE CONFIG
# -----------------------------------------------
st.set_page_config(page_title="Fenergo | Account Intelligence", layout="wide", page_icon="🏦")

# -----------------------------------------------
# APPLICATION CONSTANTS
# -----------------------------------------------
APP_VERSION = "3.0"
MAX_RESPONSES_API_RETRIES = 2          # Retry attempts for Responses API before fallback
_CAT_REGEX_12 = r'\b(cat|category)\s*[12]\b'   # matches "Cat 1", "Cat 2", "Category 1", etc.
_CAT_REGEX_3  = r'\b(cat|category)\s*3\b'       # matches "Cat 3", "Category 3"
_CAT_SECONDARY_OWNER_REGEX = r'\b(cat|category)\s*1\b'  # for secondary owner assignment

# -----------------------------------------------
# OPENAI CLIENT
# -----------------------------------------------
_openai_init_error = None
try:
    _openai_api_key = st.secrets["openai"]["api_key"]
    client = OpenAI(api_key=_openai_api_key)
except Exception as _e:
    client = None
    _openai_init_error = str(_e)

# -----------------------------------------------
# FENERGO BRAND STYLING
# Deep Teal: #002E33 | Java Turquoise: #21CFB2 | White: #FFFFFF
# -----------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f5f7f7; }

    /* Top header bar */
    .fenergo-header {
        background-color: #002E33;
        padding: 18px 32px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
    }
    .fenergo-header h1 {
        color: #21CFB2;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        font-family: sans-serif;
        letter-spacing: 0.5px;
    }
    .fenergo-header span {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        font-family: sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #002E33 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stFileUploader label {
        color: #21CFB2 !important;
    }

    /* Sidebar file upload browse button — make it visible on dark background */
    section[data-testid="stSidebar"] .stFileUploader button {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] .stFileUploader button:hover {
        background-color: #1ab89d !important;
        color: #002E33 !important;
    }

    /* Sidebar uploaded file name — override white text so it's readable on the widget's light background */
    section[data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderFile"] {
        color: #002E33 !important;
    }
    section[data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderFile"] * {
        color: #002E33 !important;
    }

    /* Sidebar expander content — dark background so white text remains readable */
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: #003a40 !important;
    }
    section[data-testid="stSidebar"] .streamlit-expanderContent * {
        color: #ffffff !important;
    }

    /* Sidebar success/warning/error/info alert boxes — dark background with white text */
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: #003a40 !important;
        border-color: #21CFB2 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stAlert"] * {
        color: #ffffff !important;
    }

    /* Sidebar checkbox, radio, selectbox label text */
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #ffffff !important;
    }

    /* Sidebar dataframe/table text */
    section[data-testid="stSidebar"] [data-testid="stDataFrame"] * {
        color: #002E33 !important;
        background-color: #ffffff !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #002E33;
        border-radius: 8px 8px 0 0;
        padding: 0 8px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0bfbf !important;
        background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border-radius: 0 0 8px 8px;
        padding: 24px;
        border: 1px solid #dde8e8;
    }

    /* Cards */
    .fen-card {
        background: #ffffff;
        border-left: 4px solid #21CFB2;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 4px rgba(0,46,51,0.08);
    }
    .fen-card h4 {
        color: #002E33;
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1ab89d !important;
    }

    /* Section headers */
    .fen-section-title {
        color: #002E33;
        font-weight: 700;
        font-size: 1rem;
        border-bottom: 2px solid #21CFB2;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }

    /* Placeholder tab content */
    .placeholder-box {
        background: #f0f9f8;
        border: 2px dashed #21CFB2;
        border-radius: 8px;
        padding: 60px 40px;
        text-align: center;
        color: #002E33;
    }
    .placeholder-box h3 { color: #002E33; font-size: 1.3rem; }
    .placeholder-box p { color: #5a7a7a; font-size: 0.95rem; }

    /* Salesforce-mirrored layout */
    .sf-layout {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        margin-top: 8px;
    }
    .sf-section {
        background: #ffffff;
        border: 1px solid #dddbda;
        border-radius: 4px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .sf-section-header {
        background-color: #f3f3f3;
        border-bottom: 1px solid #dddbda;
        padding: 8px 16px;
        font-size: 0.8rem;
        font-weight: 700;
        color: #3e3e3c;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .sf-fields-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
    }
    .sf-field {
        padding: 10px 16px;
        border-bottom: 1px solid #f3f3f3;
        min-height: 52px;
    }
    .sf-field-label {
        font-size: 0.7rem;
        color: #706e6b;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 3px;
        font-weight: 600;
    }
    .sf-field-value {
        font-size: 0.88rem;
        color: #181818;
        font-weight: 500;
        line-height: 1.3;
    }
    .sf-field-value.sf-empty {
        color: #c9c7c5;
    }
    .sf-field.sf-greyed .sf-field-label {
        color: #c9c7c5;
    }
    .sf-field.sf-greyed .sf-field-value {
        color: #c9c7c5;
    }
    .sf-field-note {
        font-size: 0.73rem;
        color: #706e6b;
        margin-top: 4px;
        font-style: italic;
        line-height: 1.3;
    }
</style>
""", unsafe_allow_html=True)

# Extended styles: animations, stepper, field population logic, visual diagrams, footer
st.markdown("""
<style>
    /* ── Tab switch animation ─────────────────────────────────────── */
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeInTab 0.25s ease;
    }
    @keyframes fadeInTab {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0);   }
    }

    /* ── Improved card hover effects ────────────────────────────────── */
    .fen-card {
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .fen-card:hover {
        box-shadow: 0 4px 16px rgba(0,46,51,0.15);
        transform: translateY(-1px);
    }

    /* ── Button transitions ─────────────────────────────────────────── */
    .stButton > button {
        transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.1s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(33,207,178,0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Improved metrics cards ─────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f0f9f8 100%);
        border: 1px solid #dde8e8;
        border-radius: 10px;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(0,46,51,0.07);
        transition: box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(0,46,51,0.13);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #002E33 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5a7a7a !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    /* ── Sidebar status indicator ─────────────────────────────────── */
    .sidebar-status {
        background: rgba(33,207,178,0.12);
        border: 1px solid rgba(33,207,178,0.3);
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 0.78rem;
        color: #21CFB2;
        margin-top: 12px;
    }

    /* ── 3-step workflow stepper ─────────────────────────────────── */
    .workflow-stepper {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
        margin: 20px 0 28px 0;
    }
    .workflow-step {
        background: #f0f9f8;
        border: 2px solid #21CFB2;
        border-radius: 10px;
        padding: 16px 18px;
        position: relative;
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .workflow-step:hover {
        box-shadow: 0 4px 14px rgba(33,207,178,0.28);
        transform: translateY(-2px);
    }
    .workflow-step-num {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #21CFB2;
        color: #002E33;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 10px;
    }
    .workflow-step-title {
        color: #002E33;
        font-weight: 700;
        font-size: 0.92rem;
        margin-bottom: 6px;
    }
    .workflow-step-desc {
        color: #5a7a7a;
        font-size: 0.81rem;
        line-height: 1.55;
    }
    .workflow-step-arrow {
        position: absolute;
        right: -10px;
        top: 50%;
        transform: translateY(-50%);
        color: #21CFB2;
        font-size: 1.2rem;
        z-index: 2;
    }

    /* ── Dropzone container ───────────────────────────────────────── */
    .dropzone-container {
        border: 2px dashed #21CFB2;
        border-radius: 10px;
        padding: 18px 20px;
        background: linear-gradient(135deg, #f0f9f8 0%, #e8f7f5 100%);
        margin-bottom: 12px;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .dropzone-container:hover {
        border-color: #002E33;
        background: #e0f5f1;
    }
    .dropzone-label {
        color: #002E33;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 6px;
    }
    .dropzone-hint {
        color: #5a7a7a;
        font-size: 0.82rem;
        margin-top: 4px;
    }

    /* ── Field Population Logic cards ────────────────────────────── */
    .fpl-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        margin-top: 12px;
    }
    .fpl-card {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #21CFB2;
        box-shadow: 0 1px 6px rgba(0,46,51,0.08);
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .fpl-card:hover {
        box-shadow: 0 5px 18px rgba(0,46,51,0.15);
        transform: translateY(-2px);
    }
    .fpl-field-name {
        color: #002E33;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }
    .fpl-badges { margin-bottom: 8px; }
    .fpl-source-badge {
        display: inline-block;
        padding: 2px 9px;
        border-radius: 12px;
        font-size: 0.74rem;
        font-weight: 600;
        margin-right: 4px;
        margin-bottom: 3px;
    }
    .badge-ai     { background: #e8f0fe; color: #1a56db; }
    .badge-web    { background: #d1fae5; color: #065f46; }
    .badge-matrix { background: #fef3c7; color: #92400e; }
    .badge-user   { background: #ede9fe; color: #4c1d95; }
    .badge-sf     { background: #d1fae5; color: #047857; }
    .badge-rules  { background: #fce7f3; color: #9d174d; }
    .fpl-description {
        color: #4a5568;
        font-size: 0.84rem;
        line-height: 1.6;
    }
    .fpl-section-header {
        color: #002E33;
        font-size: 1.05rem;
        font-weight: 700;
        border-bottom: 2px solid #21CFB2;
        padding-bottom: 6px;
        margin: 22px 0 14px 0;
    }

    /* ── Customer Segment Logic flowchart ────────────────────────── */
    .fc-outer {
        background: white;
        border-radius: 12px;
        border: 1px solid #dde8e8;
        padding: 20px;
        margin-bottom: 20px;
    }
    .fc-rule-banner {
        background: linear-gradient(90deg, #002E33 0%, #004a52 100%);
        color: white;
        border-radius: 8px;
        padding: 12px 18px;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .fc-segments-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
    }
    .fc-segment-card {
        border: 1px solid #dde8e8;
        border-radius: 10px;
        overflow: hidden;
    }
    .fc-seg-header {
        background: #002E33;
        color: #21CFB2;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 9px 14px;
        letter-spacing: 0.3px;
    }
    .fc-metric-group {
        padding: 10px 14px;
        border-bottom: 1px solid #f0f4f4;
    }
    .fc-metric-group:last-child { border-bottom: none; }
    .fc-metric-label {
        font-size: 0.78rem;
        color: #706e6b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 6px;
    }
    .fc-tiers { display: flex; flex-direction: column; gap: 3px; }
    .fc-tier {
        padding: 4px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .fc-enterprise { background: #d4edda; color: #155724; }
    .fc-midmarket  { background: #fff3cd; color: #856404; }
    .fc-scaleup    { background: #f8d7da; color: #721c24; }
    .fc-na         { background: #f3f3f3; color: #706e6b; font-style: italic; }
    .fc-legend {
        display: flex;
        gap: 16px;
        margin-top: 14px;
        padding: 10px 14px;
        background: #f8fafa;
        border-radius: 8px;
        font-size: 0.8rem;
    }
    .fc-legend-item { display: flex; align-items: center; gap: 6px; }
    .fc-legend-dot {
        width: 12px; height: 12px; border-radius: 3px;
    }

    /* ── Fenergo Segmentation visual tree ────────────────────────── */
    .seg-tree-outer {
        background: white;
        border-radius: 10px;
        border: 1px solid #dde8e8;
        padding: 10px;
        margin-bottom: 10px;
        overflow-x: auto;
    }
    .seg-market-section {
        margin-bottom: 8px;
    }
    .seg-market-label {
        background: linear-gradient(90deg, #002E33 0%, #004a52 100%);
        color: #21CFB2;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 6px;
        letter-spacing: 0.2px;
    }
    .seg-business-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-left: 12px;
    }
    .seg-business-card {
        background: #f0f9f8;
        border: 1px solid #21CFB2;
        border-radius: 6px;
        overflow: hidden;
        min-width: 140px;
        max-width: 200px;
        flex: 1;
    }
    .seg-business-header {
        background: #21CFB2;
        color: #002E33;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 3px 8px;
    }
    .seg-detailed-list {
        padding: 3px 8px;
    }
    .seg-detailed-item {
        font-size: 0.7rem;
        color: #002E33;
        padding: 1px 0;
        border-bottom: 1px solid rgba(33,207,178,0.12);
        line-height: 1.3;
    }
    .seg-detailed-item:last-child { border-bottom: none; }

    /* ── ICP Characteristics ──────────────────────────────────────── */
    .icp-card {
        background: white;
        border-left: 4px solid #21CFB2;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
        box-shadow: 0 1px 4px rgba(0,46,51,0.08);
    }
    .icp-card-title {
        color: #002E33;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 6px;
    }
    .icp-score-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 8px;
    }
    .icp-score-5 { background:#d4edda; color:#155724; }
    .icp-score-4 { background:#d4edda; color:#155724; }
    .icp-score-3 { background:#fff3cd; color:#856404; }
    .icp-score-2 { background:#f8d7da; color:#721c24; }
    .icp-score-1 { background:#f8d7da; color:#721c24; }
    .icp-score-0 { background:#f3f3f3; color:#706e6b; }
    .icp-overall {
        background: linear-gradient(135deg, #002E33 0%, #004a52 100%);
        color: white;
        border-radius: 10px;
        padding: 18px 24px;
        margin-top: 20px;
    }
    .icp-overall-title {
        color: #21CFB2;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 12px;
    }
    .icp-overall-score {
        font-size: 2.4rem;
        font-weight: 800;
        color: #21CFB2;
    }

    /* ── Reference flow diagram ───────────────────────────────────── */
    .flow-outer {
        background: white;
        border-radius: 12px;
        border: 1px solid #dde8e8;
        padding: 24px;
        margin-bottom: 20px;
    }
    .flow-box {
        background: #f0f9f8;
        border: 2px solid #21CFB2;
        border-radius: 8px;
        padding: 8px 14px;
        text-align: center;
        font-size: 0.82rem;
        font-weight: 600;
        color: #002E33;
        display: inline-block;
        min-width: 120px;
    }
    .flow-box-centre {
        background: #002E33;
        border: 2px solid #21CFB2;
        border-radius: 10px;
        padding: 12px 20px;
        text-align: center;
        font-size: 0.95rem;
        font-weight: 800;
        color: #21CFB2;
        display: inline-block;
        min-width: 160px;
    }
    .flow-arrow {
        color: #21CFB2;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .flow-note {
        font-size: 0.72rem;
        color: #5a7a7a;
        font-style: italic;
        margin-top: 4px;
    }

    /* ── Professional footer ──────────────────────────────────────── */
    .fen-footer {
        background: #002E33;
        color: rgba(255,255,255,0.6);
        border-radius: 8px;
        padding: 14px 24px;
        margin-top: 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.78rem;
    }
    .fen-footer-brand {
        color: #21CFB2;
        font-weight: 700;
    }
    .fen-footer-version {
        background: rgba(33,207,178,0.15);
        color: #21CFB2;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.74rem;
        font-weight: 600;
    }

    /* ── Divider animation ────────────────────────────────────────── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #21CFB2, transparent);
        margin: 20px 0;
        animation: shimmer 2s ease infinite;
    }
    @keyframes shimmer {
        0%   { opacity: 0.5; }
        50%  { opacity: 1;   }
        100% { opacity: 0.5; }
    }

    /* ── Improved data freshness / alert styling ─────────────────── */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
        border-left-width: 4px !important;
    }

    /* ── Breadcrumb context indicator ────────────────────────────── */
    .fen-breadcrumb {
        font-size: 0.78rem;
        color: #5a7a7a;
        margin-bottom: 16px;
        padding: 6px 0;
        border-bottom: 1px solid #e8eef0;
    }
    .fen-breadcrumb span { color: #21CFB2; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="fenergo-header" style="background: linear-gradient(90deg, #002E33 0%, #003d43 60%, #002E33 100%); padding: 18px 32px; border-radius: 8px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;">
    <div style="display:flex; align-items:center;">
        <h1 style="color:#21CFB2; font-size:1.6rem; font-weight:700; margin:0; font-family:sans-serif; letter-spacing:0.5px;">
            fener<span style="color:#21CFB2">g</span><span style="color:#ffffff">o</span>
        </h1>
        <span style="color:#ffffff; font-size:1.6rem; font-weight:700; font-family:sans-serif;">&nbsp;&nbsp;|&nbsp;&nbsp;Account Intelligence</span>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
        <span style="color:rgba(255,255,255,0.5); font-size:0.78rem;">🟢 System Operational</span>
        <span style="background:rgba(33,207,178,0.18); color:#21CFB2; padding:3px 10px; border-radius:10px; font-size:0.75rem; font-weight:600;">v{APP_VERSION}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------
# LOAD SEGMENT HIERARCHY FROM EXCEL (with fallback)
# -----------------------------------------------
@st.cache_data
def load_segment_hierarchy():
    """Load segment hierarchy from Excel file with fallback to hardcoded data.

    Priority:
    1. Salesforce Segments 06_10_25 v2.xlsx  (columns: Detailed Business Segment, Business Segment, Market Segment)
    2. Salesforce Segments.xlsx
    3. Hardcoded SEGMENT_HIERARCHY_DEFAULT
    """
    _SEGMENT_HIERARCHY_DEFAULT = [
        ("Alternative Asset Management",                   "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Asset Management",                               "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Hedge Funds",                                    "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Investech",                                      "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Pension Funds",                                  "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Private Banking",                                "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Real Estate",                                    "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Sovereign Wealth Funds",                         "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Wealth Management",                              "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Family Offices",                                 "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
        ("Asset Servicing",                                "Asset Servicing",                "Asset Mgmt., Servicing & Insurance"),
        ("Custodian",                                      "Asset Servicing",                "Asset Mgmt., Servicing & Insurance"),
        ("Insurance",                                      "Insurance",                      "Asset Mgmt., Servicing & Insurance"),
        ("Insurtech",                                      "Insurance",                      "Asset Mgmt., Servicing & Insurance"),
        ("Brokerage/Broker-dealer",                        "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
        ("Clearing House",                                 "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
        ("Transaction & Trust Activities",                 "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
        ("Investment / Institutional Banking",             "C&IB",                           "Banks"),
        ("Central Banking",                                "Commercial & Business",          "Banks"),
        ("Commercial Banking",                             "Commercial & Business",          "Banks"),
        ("Business Banking",                               "Commercial & Business",          "Banks"),
        ("Financial Services",                             "Commercial & Business",          "Banks"),
        ("Community Bank",                                 "Retail",                         "Banks"),
        ("Credit Union",                                   "Retail",                         "Banks"),
        ("Retail Banking",                                 "Retail",                         "Banks"),
        ("Mutual Savings Bank",                            "Retail",                         "Banks"),
        ("Exchanges and Commodity Trading",                "Exchanges and Commodity trading","Corporates"),
        ("Market Maker",                                   "Exchanges and Commodity trading","Corporates"),
        ("Oil & Gas",                                      "Oil & Gas",                      "Corporates"),
        ("Energy",                                         "Energy",                         "Corporates"),
        ("Renewable Energy",                               "Energy",                         "Corporates"),
        ("Banking as a Service",                           "Fintech",                        "Fintech"),
        ("Crypto",                                         "Fintech",                        "Fintech"),
        ("Digital Banks",                                  "Fintech",                        "Fintech"),
        ("Embedded Finance & BNPL",                        "Fintech",                        "Fintech"),
        ("E-money Institutions",                           "Fintech",                        "Fintech"),
        ("Fintech",                                        "Fintech",                        "Fintech"),
        ("Marketplaces",                                   "Fintech",                        "Fintech"),
        ("Money Services Business",                        "Fintech",                        "Fintech"),
        ("Neo Banks",                                      "Fintech",                        "Fintech"),
        ("Open Banking",                                   "Fintech",                        "Fintech"),
        ("Payments Service Provider",                      "Fintech",                        "Fintech"),
        ("Remittance",                                     "Fintech",                        "Fintech"),
        ("Gaming and Gambling",                            "Fintech",                        "Fintech"),
        ("Proptech",                                       "Fintech",                        "Fintech"),
        ("Full-Service Banks",                             "Full-Service Banks",             "Banks"),
        ("Precious Metals and Jewellery",                  "Other",                          "Other"),
        ("Legal and Accounting Services",                  "Other",                          "Other"),
        ("Other",                                          "Other",                          "Other"),
        ("Professional Services",                          "Other",                          "Other"),
        ("Other Corporates",                               "Other",                          "Other"),
        ("Building Society",                               "Other",                          "Other"),
        ("Aviation and Aerospace Component Manufacturing", "Other",                          "Other"),
        ("High Value Goods and Luxury Items",              "Other",                          "Other"),
    ]

    _col_map_options = [
        # common column name patterns: (detailed, business, market)
        ("Detailed Business Segment", "Business Segment", "Market Segment"),
        ("detailed business segment", "business segment", "market segment"),
        ("Detailed_Business_Segment", "Business_Segment", "Market_Segment"),
    ]

    for _fname in ("Salesforce Segments 06_10_25 v2.xlsx", "Salesforce Segments.xlsx"):
        try:
            _df = pd.read_excel(_fname)
            _cols_lc = {c: c.strip().lower() for c in _df.columns}
            _det_col = next((c for c, lc in _cols_lc.items() if "detailed" in lc and "segment" in lc), None)
            _biz_col = next((c for c, lc in _cols_lc.items() if "business" in lc and "segment" in lc and "detailed" not in lc), None)
            _mkt_col = next((c for c, lc in _cols_lc.items() if "market" in lc and "segment" in lc), None)
            if _det_col and _biz_col and _mkt_col:
                _hier = []
                for _, _row in _df.iterrows():
                    _d = str(_row[_det_col]).strip() if pd.notna(_row[_det_col]) else ""
                    _b = str(_row[_biz_col]).strip() if pd.notna(_row[_biz_col]) else ""
                    _m = str(_row[_mkt_col]).strip() if pd.notna(_row[_mkt_col]) else ""
                    if _d and _b and _m:
                        # Ensure Full-Service Banks market is "Banks"
                        if _b.lower() == "full-service banks" or _d.lower() == "full-service banks":
                            _m = "Banks"
                        _hier.append((_d, _b, _m))
                if _hier:
                    return _hier, _fname
        except FileNotFoundError:
            continue
        except Exception:
            continue

    return _SEGMENT_HIERARCHY_DEFAULT, "hardcoded"

SEGMENT_HIERARCHY, _seg_hierarchy_source = load_segment_hierarchy()

SEGMENT_LOOKUP = {
    row[0].lower(): {"detailed": row[0], "business": row[1], "market": row[2]}
    for row in SEGMENT_HIERARCHY
}
VALID_DETAILED_SEGMENTS = [row[0] for row in SEGMENT_HIERARCHY]
VALID_BUSINESS_SEGMENTS = list(dict.fromkeys(row[1] for row in SEGMENT_HIERARCHY))
VALID_MARKET_SEGMENTS   = list(dict.fromkeys(row[2] for row in SEGMENT_HIERARCHY))

FINANCIAL_STOP_WORDS = {
    "bank", "financial", "group", "capital", "asset", "management",
    "services", "solutions", "international", "global", "trust",
    "investments", "partners", "advisory", "fund", "funds",
    "federal", "savings", "national", "commercial", "credit",
    "corporate", "holding", "holdings", "co", "company",
}

COUNTRY_REGION_MAP = {
    # EMEA — UK & Ireland
    "United Kingdom": "EMEA",
    "Ireland": "EMEA",
    # EMEA — Western Europe
    "France": "EMEA", "Germany": "EMEA", "Netherlands": "EMEA",
    "Belgium": "EMEA", "Luxembourg": "EMEA", "Switzerland": "EMEA",
    "Austria": "EMEA", "Italy": "EMEA", "Spain": "EMEA",
    "Portugal": "EMEA", "Sweden": "EMEA", "Norway": "EMEA",
    "Denmark": "EMEA", "Finland": "EMEA", "Iceland": "EMEA",
    # EMEA — Eastern Europe
    "Poland": "EMEA", "Czech Republic": "EMEA", "Hungary": "EMEA",
    "Romania": "EMEA", "Bulgaria": "EMEA", "Croatia": "EMEA",
    "Slovakia": "EMEA", "Slovenia": "EMEA", "Serbia": "EMEA",
    "Greece": "EMEA", "Cyprus": "EMEA", "Malta": "EMEA",
    "Estonia": "EMEA", "Latvia": "EMEA", "Lithuania": "EMEA",
    "Ukraine": "EMEA", "Russia": "EMEA",
    # EMEA — Middle East & Africa
    "United Arab Emirates": "EMEA", "Saudi Arabia": "EMEA",
    "Qatar": "EMEA", "Kuwait": "EMEA", "Bahrain": "EMEA",
    "Oman": "EMEA", "Israel": "EMEA", "Turkey": "EMEA",
    "Jordan": "EMEA", "Lebanon": "EMEA", "Egypt": "EMEA",
    "South Africa": "EMEA", "Nigeria": "EMEA", "Kenya": "EMEA",
    "Ghana": "EMEA", "Morocco": "EMEA",
    # APAC
    "Australia": "APAC", "New Zealand": "APAC", "Singapore": "APAC",
    "Hong Kong": "APAC", "Japan": "APAC", "China": "APAC",
    "India": "APAC", "South Korea": "APAC", "Malaysia": "APAC",
    "Thailand": "APAC", "Indonesia": "APAC", "Philippines": "APAC",
    "Vietnam": "APAC", "Taiwan": "APAC", "Pakistan": "APAC",
    "Bangladesh": "APAC", "Sri Lanka": "APAC",
    # AMER
    "United States": "AMER", "Canada": "AMER",
    "Mexico": "AMER", "Brazil": "AMER", "Argentina": "AMER",
    "Chile": "AMER", "Colombia": "AMER", "Peru": "AMER",
    "Uruguay": "AMER", "Venezuela": "AMER", "Ecuador": "AMER",
    "Costa Rica": "AMER", "Panama": "AMER",
    "Cayman Islands": "AMER", "Bermuda": "AMER",
    "British Virgin Islands": "AMER",
}

# -----------------------------------------------
# Matching weights — Account Name is primary signal,
# Legal Name is a supporting signal.
# Special rule: if Account Name is an exact match (score = 100),
# the overall confidence is immediately returned as 100 regardless of legal name.
# Otherwise: combined score = ACCT_WEIGHT * acct_score + LEGAL_WEIGHT * legal_score
# -----------------------------------------------
ACCT_WEIGHT  = 0.70
LEGAL_WEIGHT = 0.30

# -----------------------------------------------
# G-SIB & D-SIB LISTS
# -----------------------------------------------
GSIB_LIST = [
    "jpmorgan chase", "bank of america", "citigroup", "wells fargo",
    "goldman sachs", "morgan stanley", "bank of new york mellon", "state street",
    "hsbc", "barclays", "standard chartered", "lloyds banking group", "natwest",
    "bnp paribas", "credit agricole", "groupe bpce", "societe generale",
    "deutsche bank", "unicredit", "ing group", "santander", "bbva",
    "ubs", "credit suisse",
    "mitsubishi ufj", "mizuho", "sumitomo mitsui",
    "bank of china", "icbc", "china construction bank", "agricultural bank of china",
    "bank of communications",
    "royal bank of canada", "toronto dominion", "td bank",
]

DSIB_LIST = {
    "ireland":      ["bank of ireland", "allied irish banks", "aib", "permanent tsb", "ulster bank"],
    "uk":           ["nationwide", "santander uk", "virgin money", "metro bank", "co-operative bank"],
    "germany":      ["commerzbank", "dz bank", "landesbank baden-wurttemberg", "lbbw", "bayerische landesbank", "norddeutsche landesbank"],
    "france":       ["la banque postale", "credit mutuel"],
    "netherlands":  ["rabobank", "abn amro"],
    "spain":        ["caixabank", "bankinter", "sabadell"],
    "italy":        ["intesa sanpaolo", "mediobanca"],
    "switzerland":  ["zuercher kantonalbank", "raiffeisen switzerland", "postfinance"],
    "australia":    ["commonwealth bank", "westpac", "anz", "nab", "national australia bank", "macquarie"],
    "canada":       ["bank of nova scotia", "scotiabank", "bank of montreal", "bmo", "canadian imperial bank", "cibc", "national bank of canada"],
    "singapore":    ["dbs", "ocbc", "uob"],
    "hong kong":    ["hang seng bank", "bank of east asia"],
    "india":        ["state bank of india", "sbi", "hdfc bank", "icici bank", "axis bank", "kotak mahindra"],
    "south africa": ["standard bank", "firstrand", "absa", "nedbank", "capitec"],
    "brazil":       ["itau unibanco", "bradesco", "caixa economica", "banco do brasil"],
    "sweden":       ["swedbank", "seb", "handelsbanken"],
    "norway":       ["dnb"],
    "denmark":      ["danske bank", "jyske bank", "sydbank"],
    "belgium":      ["kbc", "belfius"],
    "austria":      ["erste group", "raiffeisen bank international"],
    "poland":       ["pko bank polski", "pko bp", "bank pekao"],
    "uae":          ["emirates nbd", "first abu dhabi bank", "fab", "abu dhabi commercial bank", "adcb"],
    "saudi arabia": ["al rajhi bank", "national commercial bank", "snb", "samba financial"],
    "malaysia":     ["maybank", "cimb", "public bank", "rhb bank", "hong leong bank"],
    "new zealand":  ["anz new zealand", "westpac new zealand", "bnz", "asb bank", "kiwibank"],
}
DSIB_FLAT = [name for names in DSIB_LIST.values() for name in names]

# -----------------------------------------------
# SIDEBAR
# -----------------------------------------------
st.sidebar.markdown("### Account Intelligence")
st.sidebar.markdown("---")
st.sidebar.markdown("**📂 Salesforce Account List**")
uploaded_file = st.sidebar.file_uploader(
    "Upload Salesforce Accounts CSV",
    type=["csv"],
    help="Maximum recommended file size: 10 MB",
)
sf_accounts = None
if uploaded_file:
    sf_accounts = pd.read_csv(uploaded_file)
    st.sidebar.success(f"✅ Loaded {len(sf_accounts)} accounts")

# -----------------------------------------------
# LOAD ACCOUNT CATEGORY MATRIX
# -----------------------------------------------
@st.cache_data
def load_account_category_matrix():
    """Load account category matrix.

    Priority:
    1. ``account_category_matrix v2.xlsx`` — single header row; column headers
       are the concatenation of Customer Segment + Business Segment (no space).
       Stored as 2-tuple keys: ``(country_lower, cs+bs_lower)`` → value.
    2. ``account_category_matrix.xlsx`` — multi-header (primary) or
       single-header with separator fallback.  Stored as 3-tuple keys:
       ``(country_lower, bs_lower, cs_lower)`` → value.
    """

    # ── v2 (preferred) ────────────────────────────────────────────────────────
    _v2_err = None
    try:
        df_v2 = pd.read_excel("account_category_matrix v2.xlsx", header=0, index_col=0)
        lookup_v2 = {}
        for country in df_v2.index:
            if pd.isna(country):
                continue
            country_clean = str(country).strip().lower()
            for col in df_v2.columns:
                col_str = str(col).strip()
                # Skip the Region column (not a segment combination)
                if col_str.lower() == 'region':
                    continue
                # Strip zero-width spaces and other invisible Unicode characters
                col_clean = col_str.replace('\u200b', '').replace('\u00a0', '').strip()
                if not col_clean:
                    continue
                val = df_v2.loc[country, col]
                if pd.notna(val) and str(val).strip():
                    lookup_v2[(country_clean, col_clean.lower())] = str(val).strip()
        if lookup_v2:
            return lookup_v2, None
        _v2_err = "account_category_matrix v2.xlsx loaded but contains no valid entries"
    except FileNotFoundError:
        _v2_err = "account_category_matrix v2.xlsx not found — falling back to v1"
    except Exception as e_v2:
        _v2_err = f"Error reading v2 matrix: {e_v2}"

    # ── v1 fallback ───────────────────────────────────────────────────────────
    _primary_err = None
    try:
        df = pd.read_excel("account_category_matrix.xlsx", header=[0, 1], index_col=0)
        df.columns = pd.MultiIndex.from_arrays([
            pd.Series(df.columns.get_level_values(0)).ffill().values,
            df.columns.get_level_values(1)
        ])
        lookup = {}
        for country in df.index:
            if pd.isna(country):
                continue
            country_clean = str(country).strip().lower()
            for (business_seg, customer_seg) in df.columns:
                value = df.loc[country, (business_seg, customer_seg)]
                if pd.notna(value):
                    lookup[(
                        country_clean,
                        str(business_seg).strip().lower(),
                        str(customer_seg).strip().lower()
                    )] = str(value).strip()
        if lookup:
            return lookup, None
        _primary_err = "Multi-header read succeeded but matrix contains no valid entries"
    except FileNotFoundError:
        return {}, "account_category_matrix.xlsx not found in repo root"
    except Exception as e:
        _primary_err = str(e)

    # Fallback: single-header row with "BusinessSegment / CustomerSegment" column names
    try:
        df2 = pd.read_excel("account_category_matrix.xlsx", header=0, index_col=0)
        lookup2 = {}
        for country in df2.index:
            if pd.isna(country):
                continue
            country_clean = str(country).strip().lower()
            for col in df2.columns:
                col_str = str(col).strip()
                for sep in [' / ', ' | ', '/', ' - ']:
                    if sep in col_str:
                        parts = col_str.split(sep, 1)
                        bseg = parts[0].strip()
                        cseg = parts[1].strip()
                        val = df2.loc[country, col]
                        if pd.notna(val):
                            lookup2[(country_clean, bseg.lower(), cseg.lower())] = str(val).strip()
                        break
        if lookup2:
            return lookup2, None
        return {}, f"Matrix loaded but no entries found. Primary error: {_primary_err}. Fallback attempted with {len(df2.columns)} columns."
    except FileNotFoundError:
        return {}, "account_category_matrix.xlsx not found in repo root"
    except Exception as e2:
        return {}, f"Error loading matrix: primary={_primary_err}; fallback={e2}"

matrix_lookup, matrix_error = load_account_category_matrix()
if matrix_error:
    st.sidebar.warning(matrix_error)
else:
    st.sidebar.success(f"✅ Matrix loaded ({len(set(k[0] for k in matrix_lookup.keys()))} countries)")

# -----------------------------------------------
# LOAD ICP CHARACTERISTICS FROM EXCEL
# -----------------------------------------------
@st.cache_data
def load_icp_characteristics():
    """Load ICP Characteristics from Excel file.

    Returns a list of dicts with keys:
      id, characteristic, what_it_measures, weight, evidence,
      score_1, score_2, score_3, score_4, score_5
    """
    try:
        _df = pd.read_excel("ICP Characteristics.xlsx")
        _rows = []
        for _, _row in _df.iterrows():
            _rows.append({
                "id":               str(_row.get("#", "")).strip(),
                "characteristic":   str(_row.get("ICP Characteristic", "")).strip(),
                "what_it_measures": str(_row.get("What it Measures", "")).strip(),
                "weight":           _row.get("Weight (%)", 0),
                "evidence":         str(_row.get("Evidence / Data Support", "")).strip(),
                "score_1":          str(_row.get("1. Absent", "")).strip(),
                "score_2":          str(_row.get("2. Emerging", "")).strip(),
                "score_3":          str(_row.get("3.  Present", _row.get("3. Present", ""))).strip(),
                "score_4":          str(_row.get("4. Strong", "")).strip(),
                "score_5":          str(_row.get("5.  Dominant", _row.get("5. Dominant", ""))).strip(),
            })
        return _rows, None
    except FileNotFoundError:
        return [], "ICP Characteristics.xlsx not found"
    except Exception as _e:
        return [], str(_e)

icp_characteristics, icp_load_error = load_icp_characteristics()
if icp_load_error:
    st.sidebar.warning(f"ICP file: {icp_load_error}")
elif icp_characteristics:
    st.sidebar.success(f"✅ ICP Characteristics loaded ({len(icp_characteristics)} criteria)")

# Sidebar status / powered-by indicator
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div class="sidebar-status">
🤖 Powered by OpenAI gpt-4.1<br>
🔍 rapidfuzz · pandas · DuckDuckGo<br>
<span style="color:rgba(255,255,255,0.5); font-size:0.72rem;">Account Intelligence Platform v{APP_VERSION}</span>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------
# AI DEBUG INFO (sidebar) — visible to admins only
# -----------------------------------------------
try:
    _show_debug = st.secrets.get("show_debug", False)
except Exception:
    _show_debug = False

if _show_debug:
    with st.sidebar.expander("🔧 AI Debug Info"):
        st.markdown("**Model:** `gpt-4.1`")
        st.markdown(f"**openai SDK:** `{openai.__version__}`")
        if client is not None:
            st.success("✅ OpenAI client initialised")
        else:
            st.error("❌ OpenAI client NOT initialised")
            if _openai_init_error:
                st.code(_openai_init_error)

        # Matrix diagnostic info
        st.markdown("---")
        st.markdown("**Matrix Lookup Debug:**")
        if matrix_lookup:
            _matrix_country_set = {k[0] for k in matrix_lookup.keys()}
            st.markdown(f"Countries loaded: **{len(_matrix_country_set)}**")
            _sample_keys = list(matrix_lookup.keys())[:5]
            st.markdown("Sample keys (country, business_seg, customer_seg):")
            for _sk in _sample_keys:
                st.caption(f"`{_sk}`")
        else:
            st.warning("Matrix not loaded")

# -----------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------
def _highlight_conf(val):
    """Colour-code a confidence score cell for use with DataFrame.style.map()."""
    try:
        v = float(val)
        if v >= 90:
            return 'background-color: #d4edda; color: #155724'
        elif v >= 70:
            return 'background-color: #fff3cd; color: #856404'
        else:
            return 'background-color: #f8d7da; color: #721c24'
    except (ValueError, TypeError):
        return ''

def format_account_category(cat):
    """Format account category for display: 'Cat 1' → 'Category 1', etc."""
    if not cat:
        return cat
    return re.sub(r'\bCat\s*(\d+)\b', r'Category \1', str(cat), flags=re.IGNORECASE)

def generate_name_variations(name):
    variations = [name.lower().strip()]
    words = name.lower().split()
    initials = ''.join(w[0] for w in words if w not in ['of', 'the', 'and', '&'])
    if len(initials) >= 2:
        variations.append(initials)
    known = {
        "bank of ireland": ["boi"],
        "bank of america": ["boa", "bofa"],
        "jpmorgan chase": ["jpm", "jpmorgan"],
        "hsbc holdings": ["hsbc"],
        "deutsche bank": ["db"],
        "ubs group": ["ubs"],
        "standard chartered": ["stan chart", "stanchart"],
    }
    for key, abbrevs in known.items():
        if key in name.lower():
            variations.extend(abbrevs)
    return list(set(variations))

def normalize_name(name):
    """Strip common legal entity suffixes and normalise whitespace for fuzzy matching."""
    s = str(name).strip().lower()
    s = re.sub(r'[.,\-]', ' ', s)
    legal_suffixes = [
        r'\bpty\s+ltd\b', r'\bpte\s+ltd\b', r'\bltd\b', r'\bllc\b', r'\binc\b',
        r'\bcorp\b', r'\bcorporation\b', r'\bplc\b', r'\bag\b',
        r'\bsrl\b', r'\bgmbh\b', r'\bbv\b', r'\bnv\b', r'\bspa\b',
        r'\blimited\b', r'\bincorporated\b', r'\bholdings?\b',
        r'\bco\b', r'\bcompany\b',
    ]
    for suffix in legal_suffixes:
        s = re.sub(suffix, ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def compute_match_score(new_norm, val_norm):
    """Compute a calibrated fuzzy match score between two normalised strings.

    Scoring philosophy:
    - 100   = exact normalised match only
    - 85-99 = very close (minor word order / spelling differences)
    - 70-84 = good match (significant token overlap, similar length)
    - <70   = weak / coincidental overlap

    Key safeguards:
    1. token_set_ratio is scaled by the length ratio of the two strings so that a
       short name cannot score 100 as a pure subset of a longer name.
    2. fuzz.WRatio is NOT used — it internally returns the uncapped maximum of
       several methods including token_set_ratio, causing score inflation.
    3. Shared tokens that are all financial stop-words are penalised further.
    4. An additional multiplicative penalty is applied when the strings differ
       greatly in length (length_ratio < 0.6).
    5. Any non-exact match is capped at 99 so that 100 is reserved for exact matches.
    """
    if not new_norm or not val_norm:
        return 0

    # Exact normalised match → 100
    if new_norm == val_norm:
        return 100

    # Hard filter: very low character-level overlap
    char_ratio = difflib.SequenceMatcher(None, new_norm, val_norm).ratio()
    if char_ratio < 0.25:
        return 0

    # Length ratio — how similar are the two strings in length?
    len_a, len_b = len(new_norm), len(val_norm)
    length_ratio = min(len_a, len_b) / max(len_a, len_b) if max(len_a, len_b) > 0 else 1.0

    # Core metrics (no WRatio)
    r   = fuzz.ratio(new_norm, val_norm)             # pure character-level similarity
    tsr = fuzz.token_sort_ratio(new_norm, val_norm)  # token order-insensitive similarity

    # token_set_ratio: always scale by length ratio to penalise subset matches
    tset_contrib = 0.0
    if len(new_norm) >= 5 and len(val_norm) >= 5:
        raw_tset = fuzz.token_set_ratio(new_norm, val_norm)
        tset_adjusted = raw_tset * length_ratio   # scale down proportionally

        # Extra penalty if all shared tokens are financial stop-words
        new_tokens    = set(new_norm.split())
        val_tokens    = set(val_norm.split())
        shared_tokens = new_tokens & val_tokens
        if shared_tokens and shared_tokens.issubset(FINANCIAL_STOP_WORDS):
            tset_adjusted = min(tset_adjusted, 59)

        tset_contrib = tset_adjusted

    # Weighted blend: token_sort is most reliable, then char ratio, then adjusted token_set
    blended = 0.50 * tsr + 0.30 * r + 0.20 * tset_contrib

    # Extra multiplicative penalty for very large length differences (likely a subset match)
    if length_ratio < 0.6:
        blended *= (0.5 + 0.5 * length_ratio)

    # Word-level substring boost: if all words of the shorter name appear as whole words in
    # the longer name, boost to at least 75.  This handles abbreviations like "UBS" → "UBS IB"
    # or "UBS LUX" without relying solely on fuzzy ratios that penalize length differences.
    _new_words = set(new_norm.split()) if new_norm else set()
    _val_words = set(val_norm.split()) if val_norm else set()
    _shorter_words = _new_words if len(new_norm) <= len(val_norm) else _val_words
    _longer_words  = _val_words if len(new_norm) <= len(val_norm) else _new_words
    _shorter_norm  = new_norm if len(new_norm) <= len(val_norm) else val_norm
    if (
        len(_shorter_norm) >= 3
        and _shorter_words
        and _shorter_words.issubset(_longer_words)
        and not _shorter_words.issubset(FINANCIAL_STOP_WORDS)
    ):
        blended = max(blended, 75.0)

    # Cap at 99 — only exact normalised match earns 100
    return round(min(blended, 99.0), 1)

def combined_score(acct_score, legal_score):
    """Compute the overall confidence score for a candidate SF record.

    Rules (in priority order):
    1. If Account Name is an exact match (score = 100) → return 100 immediately.
       The account name is definitively correct; no blending needed.
    2. Otherwise → weighted blend: 70% Account Name + 30% Legal Name.
       A strong legal name match alone cannot compensate for a poor account name.

    Examples:
      Exact acct match:  acct=100, legal=any  → 100
      Close acct match:  acct=85,  legal=90   → 0.70*85 + 0.30*90 = 86.5
      Poor acct match:   acct=18,  legal=90   → 0.70*18 + 0.30*90 = 39.6
    """
    if acct_score == 100:
        return 100.0
    return round(ACCT_WEIGHT * acct_score + LEGAL_WEIGHT * legal_score, 1)

def check_duplicate(sf_accounts, account_name, region, country):
    if sf_accounts is None:
        return [], "No Salesforce account list uploaded — skipping duplicate check"
    variations = generate_name_variations(account_name)
    matches = []
    for _, row in sf_accounts.iterrows():
        row_name = str(
            row.get('Account Name', row.get('Name', row.get('account_name', row.iloc[0])))
        ).lower().strip()
        for var in variations:
            if var in row_name or row_name in var or (len(var) > 4 and var in row_name):
                row_region  = str(row.get('Region', row.get('region', ''))).strip()
                row_country = str(row.get('Country', row.get('country', ''))).strip()
                same_region  = region.lower() in row_region.lower() or row_region.lower() in region.lower()
                same_country = country.lower() in row_country.lower() or row_country.lower() in country.lower()
                matches.append({
                    'Matched Account Name': row.get('Account Name', row.get('Name', row.iloc[0])),
                    'Region':      row_region  or 'Unknown',
                    'Country':     row_country or 'Unknown',
                    'Same Region':  '🔴 Yes' if same_region  else '🟢 No',
                    'Same Country': '🔴 Yes' if same_country else '🟢 No',
                })
                break
    return matches, None

def parse_numeric(value_str):
    if not value_str or value_str in ('Not found', 'N/A', 'Unknown'):
        return None
    s = str(value_str).lower().replace(',', '').replace('$', '').replace('€', '').replace('£', '').strip()
    multiplier = 1.0
    if s.endswith('bn') or s.endswith('b'):
        s = s.rstrip('n').rstrip('b')
    elif s.endswith('m'):
        multiplier = 0.001
        s = s.rstrip('m')
    elif s.endswith('k'):
        multiplier = 0.000001
        s = s.rstrip('k')
    try:
        return float(s) * multiplier
    except ValueError:
        return None

def parse_employees(value_str):
    if not value_str or value_str in ('Not found', 'N/A', 'Unknown'):
        return None
    s = str(value_str).lower().replace(',', '').strip()
    match = re.search(r'[\d.]+', s)
    if not match:
        return None
    num = float(match.group())
    if 'k' in s:
        num *= 1000
    return int(num)

def resolve_segment(detailed_segment_guess):
    if not detailed_segment_guess:
        return None
    guess = detailed_segment_guess.lower().strip()
    if guess in SEGMENT_LOOKUP:
        return SEGMENT_LOOKUP[guess]
    for key, value in SEGMENT_LOOKUP.items():
        if guess in key or key in guess:
            return value
    return None

def lookup_sf_ultimate_parent(sf_accounts, ultimate_parent, account_name=""):
    """Search the SF upload for rows whose 'Ultimate Parent' column matches
    *ultimate_parent* (exact normalised match or fuzzy ≥ 80).

    When multiple matching rows exist with different Reporting Group values,
    the Reporting Group whose name most closely matches *account_name* (via
    fuzzy scoring) is returned.

    Args:
        sf_accounts: Salesforce accounts DataFrame.
        ultimate_parent: The ultimate parent name to look up.
        account_name: The original account name entered by the user — used to
            pick the best Reporting Group when multiple candidates exist.

    Returns:
        (parent_account: str|None, reporting_group: str|None)
    """
    if sf_accounts is None or not ultimate_parent:
        return None, None
    ult_str = str(ultimate_parent).strip()
    if ult_str.lower() in ('', 'not found', 'n/a', 'null', 'none'):
        return None, None

    cols = sf_accounts.columns.tolist()
    cols_lc = {c: c.lower().strip() for c in cols}

    # Detect Ultimate Parent column (exact first, then partial)
    ult_parent_col = None
    for c in cols:
        if cols_lc[c] in ('ultimate parent', 'ultimate_parent'):
            ult_parent_col = c
            break
    if ult_parent_col is None:
        for c in cols:
            lc = cols_lc[c]
            if 'ultimate' in lc and 'parent' in lc:
                ult_parent_col = c
                break

    # Detect Parent Account column (exact first, then partial, exclude IDs)
    parent_account_col = None
    for c in cols:
        if cols_lc[c] in ('parent account', 'parent_account'):
            parent_account_col = c
            break
    if parent_account_col is None:
        for c in cols:
            lc = cols_lc[c]
            if 'parent' in lc and 'account' in lc and 'id' not in lc and 'ultimate' not in lc:
                parent_account_col = c
                break

    # Detect Reporting Group column
    reporting_group_col = None
    for c in cols:
        lc = cols_lc[c]
        if 'reporting group' in lc or lc == 'reportinggroup' or lc == 'reporting_group':
            reporting_group_col = c
            break

    if not ult_parent_col:
        return None, None

    ult_norm = normalize_name(ult_str)

    # Collect all matching rows (same Ultimate Parent may appear multiple times
    # with different Reporting Groups, e.g. "Mastercard" and "AiiA" both under
    # "Mastercard Incorporated").
    matches = []
    for _, row in sf_accounts.iterrows():
        sf_ult_raw = row.get(ult_parent_col, '')
        if pd.isna(sf_ult_raw) or str(sf_ult_raw).strip() == '':
            continue
        sf_ult_norm = normalize_name(str(sf_ult_raw).strip())
        if sf_ult_norm == ult_norm or compute_match_score(ult_norm, sf_ult_norm) >= 80:
            parent_acct = ''
            rgroup = ''
            if parent_account_col:
                raw = row.get(parent_account_col, '')
                if pd.notna(raw):
                    parent_acct = str(raw).strip()
            if reporting_group_col:
                raw = row.get(reporting_group_col, '')
                if pd.notna(raw):
                    rgroup = str(raw).strip()
            matches.append((parent_acct, rgroup))

    if not matches:
        return None, None

    # If only one match (or no account_name provided for tie-breaking), return
    # the first result directly.
    if len(matches) == 1 or not account_name:
        pa, rg = matches[0]
        return pa or None, rg or None

    # Multiple matches: pick the Reporting Group most similar to account_name.
    acct_norm = normalize_name(account_name)
    best_pa, best_rg = matches[0]
    best_score = compute_match_score(acct_norm, normalize_name(best_rg)) if best_rg else 0
    for pa, rg in matches[1:]:
        if rg:
            score = compute_match_score(acct_norm, normalize_name(rg))
            if score > best_score:
                best_score = score
                best_pa = pa
                best_rg = rg
    return best_pa or None, best_rg or None

# -----------------------------------------------
# G-SIB / D-SIB CHECKS
# -----------------------------------------------
def is_gsib(account_name):
    name_lower = account_name.lower()
    return any(g in name_lower or name_lower in g for g in GSIB_LIST)

def is_dsib(account_name):
    name_lower = account_name.lower()
    return any(d in name_lower or name_lower in d for d in DSIB_FLAT)

def check_full_service_bank_eligibility(account_name):
    if is_gsib(account_name):
        return True, "G-SIB", None
    if is_dsib(account_name):
        return True, "D-SIB (static list match)", (
            "D-SIB match found on static list — please confirm against your "
            "local regulator's current D-SIB designation before assigning Full-Service Banks."
        )
    return False, "Neither G-SIB nor D-SIB", (
        "This institution is not on the G-SIB list and was not found on the static D-SIB list. "
        "It has been classified as Banks. If you believe this is a D-SIB, verify with the "
        "relevant local regulator and override manually."
    )

# -----------------------------------------------
# CUSTOMER SEGMENT LOGIC
# -----------------------------------------------
def classify_customer_segment(market_segment, aum_bn, revenue_bn, employees, account_name="", business_segment=""):
    all_unknown = aum_bn is None and revenue_bn is None and employees is None
    if all_unknown:
        return "Scale-up", "All metrics unknown — defaulting to Scale-up per business rules."

    seg = (market_segment or '').strip()
    bseg = (business_segment or '').strip()

    def tier(e_hit, m_hit, parts):
        rationale = " | ".join(parts) if parts else "Insufficient data"
        if e_hit:
            return "Enterprise", rationale
        if m_hit:
            return "Mid-Market", rationale
        return "Scale-up", rationale

    # Full-Service Banks check: triggered by business_segment OR legacy market_segment value
    if bseg == "Full-Service Banks" or seg == "Full-Service Banks":
        eligible, classification, warning = check_full_service_bank_eligibility(account_name)
        if eligible:
            msg = f"Confirmed {classification} — Full-Service Banks classification applied."
            if warning:
                msg += f" | {warning}"
            return "Enterprise", msg
        else:
            return classify_customer_segment("Banks", aum_bn, revenue_bn, employees, account_name, "")

    if seg == "Banks":
        e, m, parts = False, False, []
        if aum_bn is not None:
            if aum_bn > 200:
                e = True; parts.append(f"AUM {aum_bn:.1f}bn > 200bn (Enterprise)")
            elif aum_bn >= 10:
                m = True; parts.append(f"AUM {aum_bn:.1f}bn in 10-200bn (Mid-Market)")
            else:
                parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:
                e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000:
                m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Asset Mgmt., Servicing & Insurance":
        e, m, parts = False, False, []
        if aum_bn is not None:
            if aum_bn > 100:
                e = True; parts.append(f"AUM {aum_bn:.1f}bn > 100bn (Enterprise)")
            elif aum_bn >= 10:
                m = True; parts.append(f"AUM {aum_bn:.1f}bn in 10-100bn (Mid-Market)")
            else:
                parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 1000:
                e = True; parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 150:
                m = True; parts.append(f"{employees:,} FTE in 150-1,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 150 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Corporates":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:
                e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000:
                m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Fintech":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 0.5:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 0.5-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 500m (Scale-up)")
        if employees is not None:
            if employees > 1000:
                e = True; parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 250:
                m = True; parts.append(f"{employees:,} FTE in 250-1,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 250 (Scale-up)")
        return tier(e, m, parts)

    e, m, parts = False, False, []
    if revenue_bn is not None:
        if revenue_bn > 10:
            e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
        elif revenue_bn >= 2:
            m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
        else:
            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
    if employees is not None:
        if employees > 5000:
            e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
        elif employees >= 1000:
            m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
        else:
            parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
    return tier(e, m, parts)

# -----------------------------------------------
# ACCOUNT CATEGORY LOOKUP
# -----------------------------------------------
def fuzzy_country_match(country_input, lookup_keys):
    country_lower = country_input.strip().lower()
    aliases = {
        "usa": "united states", "us": "united states", "u.s.": "united states",
        "u.s.a.": "united states", "uk": "united kingdom", "u.k.": "united kingdom",
        "uae": "united arab emirates", "u.a.e.": "united arab emirates",
        "korea": "south korea", "republic of ireland": "ireland", "eire": "ireland",
    }
    country_lower = aliases.get(country_lower, country_lower)
    if country_lower in lookup_keys:
        return country_lower
    for key in lookup_keys:
        if country_lower in key or key in country_lower:
            return key
    return None

def get_account_category(country, business_segment, customer_segment, matrix_lookup):
    if not matrix_lookup:
        return "Matrix not loaded", "Matrix file could not be loaded"
    country_keys = set(k[0] for k in matrix_lookup.keys())
    matched_country = fuzzy_country_match(country, country_keys)
    _country_normalized = str(country).strip().lower()
    if not matched_country:
        return "No match found", f"Country '{country}' not found in matrix (normalised lookup key: '{_country_normalized}')"

    # Detect matrix format from the first key's tuple length.
    # v2 keys are 2-tuples: (country, customer_segment+business_segment)
    # v1 keys are 3-tuples: (country, business_segment, customer_segment)
    _sample_key = next(iter(matrix_lookup))
    if len(_sample_key) == 2:
        # v2 format: lookup key = (country, customer_segment + business_segment) — no space
        cs_norm = str(customer_segment).strip().lower()
        bs_norm = str(business_segment).strip().lower()
        concat_key = cs_norm + bs_norm
        lookup_key = (matched_country, concat_key)
        if lookup_key in matrix_lookup:
            return matrix_lookup[lookup_key], f"Matched (v2): {matched_country.title()} | {customer_segment} | {business_segment}"
        # Diagnostic: show what keys are available for this country
        _available = sorted({k[1] for k in matrix_lookup if k[0] == matched_country})
        return (
            "No match found",
            (
                f"No v2 matrix entry for {matched_country.title()} + '{customer_segment}{business_segment}'. "
                f"Available segment keys for this country: {_available[:8]}."
            )
        )
    else:
        # v1 format: lookup key = (country, business_segment, customer_segment)
        bs_norm = str(business_segment).strip().lower()
        cs_norm = str(customer_segment).strip().lower()
        lookup_key = (matched_country, bs_norm, cs_norm)
        if lookup_key in matrix_lookup:
            return matrix_lookup[lookup_key], f"Matched: {matched_country.title()} | {business_segment} | {customer_segment}"
        # Diagnostic: collect what business/customer segment keys exist for this country
        _available_bs = sorted({k[1] for k in matrix_lookup if k[0] == matched_country})
        _available_cs = sorted({k[2] for k in matrix_lookup if k[0] == matched_country})
        return (
            "No match found",
            (
                f"No matrix entry for {matched_country.title()} + '{business_segment}' + '{customer_segment}'. "
                f"Available business segments for this country: {_available_bs[:5]}. "
                f"Available customer segments: {_available_cs}."
            )
        )

# -----------------------------------------------
# SECONDARY ACCOUNT OWNER
# -----------------------------------------------
def get_secondary_account_owner(region, account_category):
    region_upper = (region or '').upper()
    if "AMER" in region_upper or "AMERICAS" in region_upper:
        if account_category and re.search(_CAT_SECONDARY_OWNER_REGEX, str(account_category).lower()):
            return "Elaine Zhang"
        else:
            current_month = datetime.now().month
            if current_month % 2 == 1:
                return "Joseph Cawley"
            else:
                return "Gabriel Simpatico"
    if "EMEA" in region_upper:
        return "Elaine Zhang"
    if "APAC" in region_upper:
        return "Vernis Tan"
    if "UK" in region_upper or "IRELAND" in region_upper:
        return "Elaine Zhang"
    return "Region not recognised — please assign manually"

# -----------------------------------------------
# WEB RESEARCH
# -----------------------------------------------
def web_research(account_name):
    data = {
        'legal_name': 'Not found', 'country_hq': 'Not found',
        'annual_revenue_eur': 'Not found', 'employees': 'Not found',
        'aum_eur': 'N/A', 'ultimate_parent': 'Not found',
        'ultimate_parent_hq': 'Not found',
        'detailed_business_segment': 'Not found',
        'business_segment': 'Not found', 'market_segment': 'Not found',
        'sources': [], 'snippets': []
    }
    queries = [
        f"{account_name} annual revenue employees headquarters",
        f"{account_name} legal name parent company",
        f"{account_name} AUM assets under management",
        f"{account_name} industry type financial services",
    ]
    try:
        with DDGS() as ddgs:
            for query in queries:
                results = list(ddgs.text(query, max_results=3))
                for r in results:
                    if r.get('href') and r['href'] not in data['sources']:
                        data['sources'].append(r['href'])
                    if r.get('body'):
                        data['snippets'].append({
                            'query':   query,
                            'source':  r.get('href', ''),
                            'snippet': r.get('body', '')
                        })
    except Exception as e:
        data['error'] = str(e)
    return data

# -----------------------------------------------
# LLM FIRMOGRAPHIC EXTRACTION
# -----------------------------------------------
def enrich_with_llm(snippets, account_name):
    """Extract structured firmographic data using the OpenAI Responses API
    with the built-in web_search tool for live internet data.

    Primary path: Responses API with web_search tool — searches the live web for
    current employee counts, revenue figures, parent company info, etc.
    Fallback: Chat Completions API (used if the Responses API call fails for any reason).

    The `snippets` parameter accepts pre-fetched web snippets.
    When `snippets` is empty, the LLM is prompted to search the web directly for all
    fields.
    """
    use_knowledge_fallback = not snippets

    # Shared JSON field definitions
    _fields = f"""- legal_name: full registered legal name (string or null)
- country_hq: ISO country name of headquarters (string or null)
- annual_revenue_eur: revenue as a human-readable string like "€4.5bn" or "€320m"; include the data year, e.g. "€4.5bn (FY2024)" — MUST be the most recent year available (string or null)
- employees: headcount as integer or human-readable string like "12,500"; include the data year, e.g. "12,500 (2024)" — MUST be the most recent year available (string or null)
- aum_eur: assets under management as a human-readable string like "€1.2tn"; include the data year; use "N/A" if not applicable to this company type, or null if unknown (string or null)
- ultimate_parent: full legal name of the ultimate parent / group holding company at the very top of the corporate ownership chain. See instructions above — MUST always be populated for publicly traded companies. (string or null)
- ultimate_parent_hq: country of the ultimate parent HQ (string or null)
- detailed_business_segment: the single best-fit Detailed Business Segment — must be exactly one of {json.dumps(VALID_DETAILED_SEGMENTS)}. This is the PRIMARY segment; business_segment and market_segment are derived automatically from it. (string)
- alternative_detailed_business_segment: if more than one Detailed Business Segment is equally valid for this company, provide ONE alternative here — must be one of {json.dumps(VALID_DETAILED_SEGMENTS)}, or null if only one segment clearly applies (string or null)
- business_segment: must be one of {json.dumps(VALID_BUSINESS_SEGMENTS)} — will be overridden by hierarchy lookup but provide your best estimate (string)
- market_segment: must be one of {json.dumps(VALID_MARKET_SEGMENTS)} — will be overridden by hierarchy lookup but provide your best estimate (string)
- industry_classification_rationale: a 1-2 sentence explanation of why you chose the detailed_business_segment value for this company (string or null)
- reporting_group_suggestion: a short, commonly-used friendly name for this company or its group — the informal name rather than the full legal name (e.g. "Barclays" for "Barclays Services Limited", "Mastercard" for "Mastercard Incorporated", "HSBC" for "HSBC Holdings plc", "UBS" for "UBS Group AG"). Used as the Reporting Group if not found in the CRM upload. (string or null)
- sources: a JSON object with keys "revenue_source", "employees_source", "aum_source" — each value should be the URL of the source used for that data point, or null if unavailable (object)"""

    system_prompt = f"""You are a financial-services data analyst with broad knowledge of global financial institutions.

Conduct COMPREHENSIVE DEEP RESEARCH on the named company using multiple authoritative sources. Do NOT rely on just the first result you find — cross-reference multiple sources and assess their credibility before settling on a value.

SOURCE PRIORITY ORDER (highest to lowest authority):
1. The company's own website — annual reports, investor relations pages, official press releases
2. Official regulatory filings — SEC EDGAR, Companies House, central bank registers, stock exchange filings
3. Major financial data providers — Bloomberg, Reuters, S&P Global, Moody's, Fitch, FactSet
4. Wikipedia and established business databases — Crunchbase, LinkedIn, Dun & Bradstreet, Bureau van Dijk
5. News articles from reputable outlets — Financial Times, Wall Street Journal, The Economist

For REVENUE and EMPLOYEE figures: You MUST use the MOST RECENT data available — current year (2025) or last fiscal year (FY2024/FY2025). Do NOT return 2023 data if 2024 or 2025 data exists. Always check the company's latest annual report or most recent quarterly filing FIRST. If more recent data exists, use it and explicitly state the year (e.g. "€4.5bn (FY2024)" or "€4.5bn (FY2025)"). Never use outdated data when more recent data is available. If sources conflict, use the most authoritative and recent one.

For ULTIMATE PARENT: You MUST find and return the ultimate parent company for EVERY company — do NOT return null without exhaustive research. This is critically important.

CRITICAL RULE: For well-known publicly traded companies that ARE themselves the ultimate parent entity, you MUST return the company itself (or its holding company name). Examples:
- Mastercard Incorporated → "Mastercard Incorporated" (self-owned, publicly traded — Mastercard IS the ultimate parent)
- Visa Inc. → "Visa Inc." (self-owned, publicly traded)
- PayPal Holdings, Inc. → "PayPal Holdings, Inc." (publicly traded holding company)
- Apple Inc. → "Apple Inc." (self-owned, publicly traded)
- Bank of Ireland → "Bank of Ireland Group plc" (the listed holding company)
- AIB → "AIB Group plc"
- Barclays → "Barclays PLC"
- JPMorgan Chase Bank → "JPMorgan Chase & Co."
- Goldman Sachs Bank → "The Goldman Sachs Group, Inc."
- UBS → "UBS Group AG"
Do NOT return null for major publicly traded companies. Always return the top-level listed or registered entity, not an operating subsidiary.

IMPORTANT:
- Include the year/date of each data point where possible (e.g. "€4.5bn (FY2024)").
- For each data point (revenue, employees, AUM), include the source URL where you found the information.
- If different sources give different values, prefer the most authoritative/recent source and note the discrepancy.

Extract structured firmographic data about the named company and return it as a single JSON object with exactly these keys:
{_fields}

Use null for fields you cannot determine. For segment fields, pick the single best match from the valid values list; use "Other" if none fits."""

    if use_knowledge_fallback:
        user_message = (
            f"Company: {account_name}\n\n"
            "Conduct comprehensive deep research on this company using multiple authoritative sources. "
            "Search the company's own website (annual reports, investor relations pages) first, "
            "then regulatory filings, then major financial data providers. "
            "Find the MOST RECENT figures for revenue, employees, AUM, ultimate parent company, and all other fields. "
            "For employee count and revenue, ALWAYS use the most recent year available (2024 or 2025 if possible). "
            "For ultimate parent, research the full corporate ownership chain to find the top-level holding company. "
            "For well-known public companies, return themselves as the ultimate parent if they have no parent above them. "
            "Cross-reference multiple sources and note any discrepancies. "
            "Include the year/date of the data where possible."
        )
    else:
        snippets_text = "\n\n".join(
            f"[Query: {s['query']}]\nSource: {s['source']}\n{s['snippet']}"
            for s in snippets
        )
        user_message = (
            f"Company: {account_name}\n\n"
            f"Preliminary web search results (these may be limited or incomplete):\n{snippets_text}\n\n"
            "Now conduct your own comprehensive deep research to verify and supplement the above data. "
            "Search the company's own website (annual reports, investor relations) as the primary source, "
            "then cross-reference with regulatory filings and major financial data providers. "
            "Pay special attention to: (1) the MOST RECENT employee count and revenue (prefer 2024/2025 data), "
            "(2) the full corporate ownership chain to identify the ultimate parent holding company, "
            "(3) for well-known public companies that are their own ultimate parent, return themselves. "
            "Note any discrepancies between sources."
        )

    try:
        if client is None:
            return {"_llm_error": "OpenAI client not configured"}

        extracted = None

        # --- Primary path: Responses API with web_search tool for live internet data ---
        # Up to MAX_RESPONSES_API_RETRIES retries before falling back to Chat Completions.
        _responses_api_error = None
        _search_method = None

        combined_input = (
            f"{system_prompt}\n\n{user_message}\n\n"
            "IMPORTANT: Use the web_search tool to conduct comprehensive deep research. "
            "Search multiple authoritative sources — prioritise the company's own website, "
            "annual reports, regulatory filings, then major financial data providers. "
            "Do NOT stop at the first result. Cross-reference sources and use the most "
            "authoritative/recent data. Return your response as a JSON object."
        )

        for _attempt in range(MAX_RESPONSES_API_RETRIES + 1):
            try:
                resp_data = client.responses.create(
                    model="gpt-4.1",
                    tools=[{"type": "web_search_preview"}],
                    input=combined_input,
                )

                # Use SDK's built-in property to extract text from the response
                text_content = resp_data.output_text or ""

                # Strip markdown code fences if present (e.g. ```json ... ```)
                text_content = text_content.strip()
                if text_content.startswith("```"):
                    lines = text_content.split("\n")
                    if len(lines) >= 3:
                        text_content = "\n".join(lines[1:-1]).strip()

                # Remove any citation annotations like 【4:0†source】
                text_content = re.sub(r'【[^】]*】', '', text_content)

                # If still not valid JSON, try to extract the JSON object
                if text_content and not text_content.startswith("{"):
                    first_brace = text_content.find("{")
                    last_brace = text_content.rfind("}")
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        text_content = text_content[first_brace:last_brace + 1]

                if not text_content:
                    raise ValueError(f"Responses API returned empty text after cleanup. Raw output_text: {repr(resp_data.output_text)[:500]}")

                extracted = json.loads(text_content)
                _search_method = "responses_api_web_search"
                break  # success — exit retry loop
            except Exception as e:
                _raw_preview = ""
                try:
                    if 'resp_data' in locals():
                        _raw_preview = f" | Raw output_text preview: {repr(resp_data.output_text)[:300]}"
                except Exception:
                    pass
                _attempt_msg = f"[Attempt {_attempt + 1}/{MAX_RESPONSES_API_RETRIES + 1}] {type(e).__name__}: {e}{_raw_preview}"
                if _responses_api_error:
                    _responses_api_error += f" || {_attempt_msg}"
                else:
                    _responses_api_error = _attempt_msg
                if _attempt < MAX_RESPONSES_API_RETRIES:
                    continue  # retry
                # All retries exhausted — fall through to Chat Completions

        # --- Fallback path: Chat Completions API (training data only) ---
        if extracted is None:
            # Build a modified system prompt that prohibits URL fabrication since this
            # path has no internet access (only training data).
            fallback_system_prompt = (
                system_prompt
                + "\n\nCRITICAL — NO INTERNET ACCESS IN THIS MODE:\n"
                "- You do NOT have access to the internet. Do NOT fabricate or guess source URLs.\n"
                "- For the sources object, set all values to null since you cannot verify any URLs.\n"
                "- Clearly indicate that figures come from training data and may be outdated by "
                "appending '(training data, may be outdated)' to revenue and employee values, "
                "e.g. '€4.5bn (FY2023, training data, may be outdated)'."
            )

            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": fallback_system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            extracted = json.loads(response.choices[0].message.content)
            _search_method = "chat_completions_fallback"

        result = {}
        for key in ("legal_name", "country_hq", "annual_revenue_eur", "employees",
                    "aum_eur", "ultimate_parent", "ultimate_parent_hq",
                    "detailed_business_segment", "business_segment", "market_segment",
                    "industry_classification_rationale",
                    "alternative_detailed_business_segment", "reporting_group_suggestion"):
            val = extracted.get(key)
            if val is not None and str(val).strip():
                result[key] = str(val).strip()
        # Preserve sources dict as-is (not coerced to string)
        sources = extracted.get("sources")
        if isinstance(sources, dict):
            result["sources"] = sources
        # Record which API path was used (for UI freshness indicator)
        result["_search_method"] = _search_method
        if _responses_api_error:
            result["_responses_api_error"] = _responses_api_error
        return result
    except Exception as e:
        return {"_llm_error": str(e), "_llm_traceback": traceback.format_exc()}

# -----------------------------------------------
# FULL SEGMENTATION
# -----------------------------------------------
def apply_segmentation(research_data, account_name="", region="", country=""):
    market_segment   = research_data.get('market_segment', '')
    business_segment = research_data.get('business_segment', '')
    aum_bn     = parse_numeric(research_data.get('aum_eur', ''))
    revenue_bn = parse_numeric(research_data.get('annual_revenue_eur', ''))
    employees  = parse_employees(research_data.get('employees', ''))
    customer_segment, rationale = classify_customer_segment(
        market_segment, aum_bn, revenue_bn, employees, account_name, business_segment
    )
    account_category, category_note = get_account_category(
        country, business_segment, customer_segment, matrix_lookup
    )
    secondary_owner = get_secondary_account_owner(region, account_category)
    return {
        'customer_segment':           customer_segment,
        'customer_segment_rationale': rationale,
        'account_category':           account_category,
        'account_category_note':      category_note,
        'secondary_account_owner':    secondary_owner,
    }

# -----------------------------------------------
# FUZZY DUPLICATE CHECK HELPER
# -----------------------------------------------
def run_fuzzy_dup_check(sf_accounts, account_name, top_n=10, min_score=60):
    """Score account_name against every row in sf_accounts using the same
    fuzzy-matching engine as Tab 3.  Returns a list of dicts (sorted
    high→low by Confidence %) containing only rows with combined score
    ≥ min_score, capped at top_n results.

    Args:
        sf_accounts (pd.DataFrame | None): The uploaded Salesforce Accounts CSV.
            Column names are auto-detected (Account ID, Account Name, Legal Name,
            Country).  Returns [] immediately when None or empty.
        account_name (str): The name to search for.
        top_n (int): Maximum number of results to return (default 10).
        min_score (float): Minimum combined confidence score to include a row
            (default 60, i.e. 60%).

    Returns:
        list[dict]: Each dict has keys: Account ID, Account Name, Legal Name,
            Country, Confidence %.
    """
    if sf_accounts is None or sf_accounts.empty:
        return []

    cols = sf_accounts.columns.tolist()
    cols_lc = {c: c.lower().strip() for c in cols}

    # Detect Account ID column — exact "account id" > "accountid" > partial > "id"
    sf_id_col = None
    for c in cols:
        if cols_lc[c] == "account id":
            sf_id_col = c
            break
    if sf_id_col is None:
        for c in cols:
            if cols_lc[c] == "accountid":
                sf_id_col = c
                break
    if sf_id_col is None:
        for c in cols:
            lc = cols_lc[c]
            if "account" in lc and "id" in lc:
                sf_id_col = c
                break
    if sf_id_col is None:
        for c in cols:
            if cols_lc[c] == "id":
                sf_id_col = c
                break

    # Detect Account Name column (exclude columns containing "id")
    sf_acct_name_col = None
    non_id_cols = [c for c in cols if 'id' not in cols_lc[c]]
    for c in non_id_cols:
        if cols_lc[c] == 'account name':
            sf_acct_name_col = c
            break
    if sf_acct_name_col is None:
        for c in non_id_cols:
            if 'account name' in cols_lc[c]:
                sf_acct_name_col = c
                break
    if sf_acct_name_col is None:
        for c in non_id_cols:
            if 'name' in cols_lc[c]:
                sf_acct_name_col = c
                break

    # Detect Legal Name column
    sf_legal_col = None
    for c in cols:
        if 'legal name' in cols_lc[c]:
            sf_legal_col = c
            break
    if sf_legal_col is None:
        for c in cols:
            if 'legal' in cols_lc[c]:
                sf_legal_col = c
                break

    # Detect Country column — prefer exact "country" match over partial
    sf_country_col = None
    for c in cols:
        if cols_lc[c] == 'country':
            sf_country_col = c
            break
    if sf_country_col is None:
        for c in cols:
            if 'country' in cols_lc[c]:
                sf_country_col = c
                break

    new_norm = normalize_name(account_name)
    scored = []

    for _, row in sf_accounts.iterrows():
        acct_score = 0
        acct_val = ""
        if sf_acct_name_col:
            raw = row.get(sf_acct_name_col, "")
            if pd.notna(raw):
                acct_val = str(raw).strip()
                if acct_val:
                    acct_score = compute_match_score(new_norm, normalize_name(acct_val))

        legal_score = 0
        legal_val = ""
        if sf_legal_col:
            raw = row.get(sf_legal_col, "")
            if pd.notna(raw):
                legal_val = str(raw).strip()
                if legal_val:
                    legal_score = compute_match_score(new_norm, normalize_name(legal_val))

        score = combined_score(acct_score, legal_score)

        if score >= min_score and acct_val:
            id_val = ""
            if sf_id_col:
                raw = row.get(sf_id_col, "")
                id_val = str(raw).strip() if pd.notna(raw) else ""

            country_val = ""
            if sf_country_col:
                raw = row.get(sf_country_col, "")
                country_val = str(raw).strip() if pd.notna(raw) else ""

            scored.append({
                "Account ID": id_val,
                "Account Name": acct_val,
                "Legal Name": legal_val,
                "Country": country_val,
                "Confidence %": score,
            })

    scored.sort(key=lambda x: x["Confidence %"], reverse=True)
    return scored[:top_n]

# -----------------------------------------------
# ICP CHARACTERISTIC RESEARCH
# -----------------------------------------------
def research_icp_characteristic(account_name, characteristic, what_it_measures, weight, evidence, scoring_rubric):
    """Research a single ICP characteristic for the given account using Responses API with web search.

    Returns a dict with:
      score (int 0-5), score_label (str), assessment (str), source_url (str|None),
      search_method (str), raw_error (str|None)
    """
    if client is None:
        return {
            "score": 0, "score_label": "N/A",
            "assessment": "OpenAI client not configured.",
            "source_url": None, "search_method": "unavailable", "raw_error": None
        }

    _score_labels = {0: "No information found", 1: "Absent", 2: "Emerging", 3: "Present", 4: "Strong", 5: "Dominant"}

    _prompt = f"""You are a financial services sales intelligence analyst evaluating whether a company is an ICP (Ideal Customer Profile) fit for Fenergo.

Fenergo is a leading Client Lifecycle Management (CLM) and KYC/AML compliance platform for financial services institutions. Fenergo helps banks, asset managers, insurance companies, and fintechs automate client onboarding, regulatory compliance (KYC, AML, FATCA, MiFID II), and client data management. Key product areas: Enterprise CLM, KYC/AML, Client Onboarding Automation, Regulatory Compliance, Financial Crime Prevention, and Data Management.

You are evaluating: **{account_name}**

ICP Characteristic to assess: **{characteristic}**
What it measures: {what_it_measures}
Weight in overall ICP score: {weight}%

Scoring rubric (1=Absent → 5=Dominant):
1. Absent: {scoring_rubric.get('1', '')}
2. Emerging: {scoring_rubric.get('2', '')}
3. Present: {scoring_rubric.get('3', '')}
4. Strong: {scoring_rubric.get('4', '')}
5. Dominant: {scoring_rubric.get('5', '')}

Supporting evidence context: {evidence}

INSTRUCTIONS:
1. Search the web for current, authoritative information about {account_name} relevant to this characteristic.
2. Assess the evidence against the scoring rubric above.
3. Assign a score from 1-5 (or 0 if no information found at all).
4. Provide a concise 2-3 sentence assessment explaining your score.
5. Include the URL of the most relevant source you found.

Return ONLY a JSON object with these keys:
- "score": integer 0-5 (0 = no information found)
- "score_label": one of "No information found", "Absent", "Emerging", "Present", "Strong", "Dominant"
- "assessment": string — 2-3 sentences explaining the score with specific evidence
- "source_url": string URL of primary source, or null if none found

Use web_search to find current information. Do NOT rely on training data alone."""

    _responses_api_error = None
    _extracted = None
    _search_method = None

    for _attempt in range(MAX_RESPONSES_API_RETRIES + 1):
        try:
            resp_data = client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "web_search_preview"}],
                input=_prompt,
            )
            text_content = resp_data.output_text or ""
            text_content = text_content.strip()
            if text_content.startswith("```"):
                lines = text_content.split("\n")
                if len(lines) >= 3:
                    text_content = "\n".join(lines[1:-1]).strip()
            text_content = re.sub(r'【[^】]*】', '', text_content)
            if text_content and not text_content.startswith("{"):
                first_brace = text_content.find("{")
                last_brace = text_content.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    text_content = text_content[first_brace:last_brace + 1]
            if not text_content:
                raise ValueError("Empty response from Responses API")
            _extracted = json.loads(text_content)
            _search_method = "responses_api_web_search"
            break
        except Exception as _e:
            _attempt_msg = f"[Attempt {_attempt + 1}] {type(_e).__name__}: {_e}"
            _responses_api_error = (_responses_api_error + " || " + _attempt_msg) if _responses_api_error else _attempt_msg
            if _attempt < MAX_RESPONSES_API_RETRIES:
                continue

    # Fallback to chat completions
    if _extracted is None:
        try:
            _fallback_prompt = _prompt + "\n\nNOTE: You do NOT have internet access in this mode. Use your training knowledge only. Clearly indicate if information may be outdated. Set source_url to null."
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": _fallback_prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            _extracted = json.loads(response.choices[0].message.content)
            _search_method = "chat_completions_fallback"
        except Exception as _fe:
            return {
                "score": 0, "score_label": "No information found",
                "assessment": f"Research failed: {_fe}",
                "source_url": None, "search_method": "failed", "raw_error": str(_fe)
            }

    _score = int(_extracted.get("score", 0))
    if _score not in range(6):
        _score = 0
    return {
        "score": _score,
        "score_label": _extracted.get("score_label", _score_labels.get(_score, "Unknown")),
        "assessment": _extracted.get("assessment", "No assessment available."),
        "source_url": _extracted.get("source_url"),
        "search_method": _search_method,
        "raw_error": _responses_api_error,
    }

# -----------------------------------------------
# TABS
# -----------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Single Account Enrichment", "Bulk Account Enrichment", "Lead Matching",
    "Reference & Process Overview"
])

# ===============================================
# TAB 1 — SINGLE ACCOUNT ENRICHMENT
# ===============================================
with tab1:

    # Initialise session state keys
    for _k, _v in [
        ("tab1_phase", "input"),
        ("tab1_dup_results", []),
        ("tab1_research", None),
        ("tab1_segmentation", None),
        ("tab1_snap", {}),
        ("tab1_icp_results", None),
        ("tab1_icp_requested", False),
    ]:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Single Account Enrichment</span></div>', unsafe_allow_html=True)
    st.markdown(
        """
        **How to use this tool:**
        Upload your Salesforce account list via the sidebar, then enter the account details below and
        click **Run Enrichment Checks**. The tool will check for potential duplicate accounts, research the
        company online using AI with live web search, and generate a recommended Fenergo segmentation.
        """,
    )

    st.markdown('<p class="fen-section-title">Enter Account Details</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        account_name = st.text_input("Account Name *", placeholder="e.g. Bank of Ireland")
    with col2:
        account_type = st.selectbox("Account Type *", ["Prospect", "Partner"], index=0)
    with col3:
        # Build country options: union of SF account countries + COUNTRY_REGION_MAP keys
        _sf_country_opts = []
        if sf_accounts is not None:
            for _c in sf_accounts.columns:
                if 'country' in _c.lower():
                    _raw = sf_accounts[_c].dropna().astype(str).str.strip().str.title()
                    _sf_country_opts = sorted(_raw[_raw != ""].unique().tolist())
                    break
        _all_countries = sorted(set(_sf_country_opts) | set(COUNTRY_REGION_MAP.keys()))
        t1_country = st.selectbox(
            "Country *",
            options=[""] + _all_countries,
            help="Type to search countries",
            key="tab1_country",
        )
    with col4:
        t1_region = COUNTRY_REGION_MAP.get(t1_country, "")
        st.text_input("Region", value=t1_region, disabled=True)

    run_button = st.button("Run Enrichment Checks", type="primary", use_container_width=True)

    if run_button:
        if not account_name.strip() or not t1_country:
            st.error("Please fill in all required fields: Account Name and Country.")
            st.stop()

        if sf_accounts is None:
            st.error(
                "⚠️ **No Salesforce Account list uploaded.** Please upload the Salesforce Accounts CSV "
                "using the sidebar uploader before running enrichment checks. "
                "This is required to perform the duplicate check."
            )
            st.stop()

        st.session_state["tab1_snap"] = {
            "account_name": account_name,
            "account_type": account_type,
            "country": t1_country,
            "region": t1_region,
        }
        st.session_state["tab1_dup_results"] = run_fuzzy_dup_check(sf_accounts, account_name)
        st.session_state["tab1_phase"] = "dup_check"
        st.session_state["tab1_research"] = None
        st.session_state["tab1_segmentation"] = None
        st.session_state["tab1_icp_results"] = None
        st.session_state["tab1_icp_requested"] = False
        st.rerun()

    # ── Phases: dup_check / enrichment ────────────────────────────────────────
    if st.session_state["tab1_phase"] in ("dup_check", "enrichment"):
        _snap         = st.session_state.get("tab1_snap", {})
        _account_name = _snap.get("account_name", "")
        _account_type = _snap.get("account_type", "")
        _country      = _snap.get("country", "")
        _region       = _snap.get("region", "")
        _dup_results  = st.session_state.get("tab1_dup_results", [])

        st.divider()
        st.markdown(
            f'<p class="fen-section-title">Running checks for: {html_escape(_account_name)}</p>',
            unsafe_allow_html=True,
        )

        # ── PARTNER FLOW ──────────────────────────────────────────────────────
        if _account_type == "Partner":
            st.info("Partner Account — only a duplicate check is required.")
            st.markdown(
                '<p class="fen-section-title">Suggested Matches</p>',
                unsafe_allow_html=True,
            )
            if not _dup_results:
                st.success("No potential duplicate accounts found.")
            else:
                _dup_df = pd.DataFrame(_dup_results)
                _styled = _dup_df.style.map(_highlight_conf, subset=["Confidence %"])
                st.dataframe(_styled, use_container_width=True, hide_index=True)

                _same_country = [
                    m for m in _dup_results
                    if m.get("Country", "").strip().lower() == _country.strip().lower()
                ]
                if _same_country:
                    st.warning(
                        "⚠️ Similar account found in the same country. "
                        "Please check with the Account Owner before proceeding."
                    )

        # ── PROSPECT (and all non-Partner) FLOW ───────────────────────────────
        else:
            st.markdown(
                '<p class="fen-section-title">Suggested Matches</p>',
                unsafe_allow_html=True,
            )
            if not _dup_results:
                st.success("No potential duplicate accounts found.")
            else:
                _dup_df = pd.DataFrame(_dup_results)
                _styled = _dup_df.style.map(_highlight_conf, subset=["Confidence %"])
                st.dataframe(_styled, use_container_width=True, hide_index=True)

            # Show "Continue" button only in dup_check phase
            if st.session_state["tab1_phase"] == "dup_check":
                _continue = st.button(
                    "✅ Continue with Enrichment", type="primary", use_container_width=True
                )
                if _continue:
                    st.session_state["tab1_phase"] = "enrichment"
                    st.rerun()

            # Enrichment: Steps 2 & 3
            elif st.session_state["tab1_phase"] == "enrichment":
                # Step 2 — AI extraction with live web search (run once, cache in session state)
                if st.session_state["tab1_research"] is None:
                    _research = {}
                    with st.status(
                        "Step 2 of 3: Researching company with AI (live web search)...", expanded=True
                    ) as _status:
                        st.write("Querying OpenAI (gpt-4.1) with live web search for current firmographic data...")
                        st.write("Searching: revenue, employees, HQ, legal name, parent company, AUM, industry")
                        _llm_data = enrich_with_llm([], _account_name)
                        if '_llm_error' in _llm_data:
                            st.warning(f"AI extraction unavailable: {_llm_data['_llm_error']}")
                            if _show_debug and '_llm_traceback' in _llm_data:
                                with st.expander("🔍 Error details"):
                                    st.code(_llm_data['_llm_traceback'])
                            _status.update(
                                label="Step 2: AI extraction failed",
                                state="error",
                            )
                        else:
                            _empty = {None, 'Not found', 'N/A', ''}
                            _fields_found = []
                            for _key, _val in _llm_data.items():
                                # sources is a dict — store as-is without empty-value filtering
                                if _key == 'sources':
                                    if isinstance(_val, dict):
                                        _research[_key] = _val
                                        _fields_found.append(_key)
                                elif _key.startswith('_'):
                                    # Internal metadata keys (e.g. _search_method, _responses_api_error)
                                    _research[_key] = _val
                                elif _val not in _empty:
                                    _research[_key] = _val
                                    _fields_found.append(_key)
                            st.write(f"Extracted {len(_fields_found)} firmographic field(s): {', '.join(_fields_found)}")
                            _search_method_val = _llm_data.get('_search_method')
                            _resp_err = _llm_data.get('_responses_api_error')
                            if _search_method_val == "responses_api_web_search":
                                st.write("✅ Used Responses API (gpt-4.1) with live web search")
                            elif _search_method_val == "chat_completions_fallback":
                                st.warning(
                                    "⚠️ **TRAINING DATA FALLBACK** — Live web search (Responses API) was "
                                    "unavailable after 2 retries. Data was sourced from AI training data and "
                                    "**may be significantly outdated**. Revenue and employee figures will be "
                                    "annotated accordingly."
                                )
                            if _resp_err:
                                st.caption(f"🔍 Responses API error detail: {_resp_err}")
                            _status.update(
                                label=f"Step 2: AI extraction complete ({len(_fields_found)} fields)",
                                state="complete",
                            )

                        # Override business_segment and market_segment from hierarchy
                        # (AI only determines detailed_business_segment; roll-ups are auto-derived)
                        _det_seg_llm = _research.get('detailed_business_segment', '')
                        if _det_seg_llm:
                            _seg_resolved = resolve_segment(_det_seg_llm)
                            if _seg_resolved:
                                _research['business_segment'] = _seg_resolved['business']
                                _research['market_segment'] = _seg_resolved['market']

                        # Lookup Parent Account and Reporting Group from SF upload
                        _ult_parent_llm = _research.get('ultimate_parent', '')
                        if _ult_parent_llm and sf_accounts is not None:
                            _sf_parent_acct, _sf_rgroup = lookup_sf_ultimate_parent(sf_accounts, _ult_parent_llm, account_name=_account_name)
                            if _sf_parent_acct:
                                _research['_parent_account'] = _sf_parent_acct
                            if _sf_rgroup:
                                _research['_reporting_group'] = _sf_rgroup
                                _research['_reporting_group_source'] = 'sf'
                            elif _research.get('reporting_group_suggestion'):
                                _research['_reporting_group'] = _research['reporting_group_suggestion']
                                _research['_reporting_group_source'] = 'ai'
                        elif _research.get('reporting_group_suggestion'):
                            _research['_reporting_group'] = _research['reporting_group_suggestion']
                            _research['_reporting_group_source'] = 'ai'

                    st.session_state["tab1_research"] = _research

                # Step 3 — Segmentation (run once, cache in session state)
                if st.session_state["tab1_segmentation"] is None:
                    _research = st.session_state["tab1_research"]
                    _segmentation = {}
                    with st.status(
                        "Step 3 of 3: Applying segmentation logic...", expanded=True
                    ) as _status:
                        st.write(
                            "Applying Customer Segment, Account Category and Secondary Owner rules..."
                        )
                        _segmentation = apply_segmentation(
                            _research, _account_name, _region, _country
                        )
                        _seg = _segmentation.get('customer_segment', '')
                        _colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(
                            _seg, "⚪"
                        )
                        st.write(f"{_colour} Customer Segment: {_seg}")
                        _rationale = _segmentation.get('customer_segment_rationale', '')
                        if "warning" in _rationale.lower() or "verify" in _rationale.lower():
                            st.warning(_rationale)
                        else:
                            st.caption(f"Rationale: {_rationale}")
                        _status.update(
                            label=f"Step 3: Segmentation complete — {_seg}", state="complete"
                        )
                    st.session_state["tab1_segmentation"] = _segmentation

                # Display results from session state
                _research     = st.session_state["tab1_research"]
                _segmentation = st.session_state["tab1_segmentation"]

                st.divider()
                st.markdown(
                    '<p class="fen-section-title">Segmentation Results</p>',
                    unsafe_allow_html=True,
                )

                # ── Salesforce-mirrored layout ──────────────────────────────────
                _seg     = _segmentation.get('customer_segment', '')
                _colour  = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(_seg, "⚪")
                _seg_display = f"{_colour} {_seg}" if _seg else ""
                _rationale   = _segmentation.get('customer_segment_rationale', '')

                # Source URLs returned by LLM (dict or None)
                _llm_sources = _research.get('sources', {})
                if not isinstance(_llm_sources, dict):
                    _llm_sources = {}

                _URL_DISPLAY_MAX = 60  # max chars to show for a source URL before truncating

                def _source_link_html(url):
                    """Return a small HTML link for a source URL, or empty string."""
                    if url and isinstance(url, str) and url.startswith('http'):
                        display = url if len(url) <= _URL_DISPLAY_MAX else url[:_URL_DISPLAY_MAX - 3] + '...'
                        return (
                            f'<div class="sf-field-note">'
                            f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                            f'style="font-size:0.75rem;color:#21CFB2;">🔗 {display}</a>'
                            f'</div>'
                        )
                    return ''

                def _sf_field(label, value, greyed=False, note=None, source_url=None, highlight=None):
                    """Return HTML for one Salesforce-style field cell.

                    highlight: 'green' | 'red' | None — applies a background tint to the value.
                    source_url: optional URL rendered as a small clickable link below the value.
                    """
                    css_class    = "sf-field sf-greyed" if greyed else "sf-field"
                    value_stripped = str(value).strip()
                    value_string = value_stripped if value and value_stripped not in ('', 'N/A') else "—"
                    value_class  = "sf-field-value sf-empty" if value_string == "—" else "sf-field-value"
                    note_html    = f'<div class="sf-field-note">{note}</div>' if note else ""
                    src_html     = _source_link_html(source_url)
                    if highlight == 'green':
                        hl_style = 'background:#d4edda;color:#155724;padding:2px 6px;border-radius:4px;'
                    elif highlight == 'red':
                        hl_style = 'background:#f8d7da;color:#721c24;padding:2px 6px;border-radius:4px;'
                    else:
                        hl_style = ''
                    escaped_value = html_escape(value_string) if value_string != "—" else value_string
                    value_inner = (
                        f'<span style="{hl_style}">{escaped_value}</span>'
                        if hl_style and value_string != "—"
                        else escaped_value
                    )
                    return (
                        f'<div class="{css_class}">'
                        f'<div class="sf-field-label">{label}</div>'
                        f'<div class="{value_class}">{value_inner}</div>'
                        f'{note_html}'
                        f'{src_html}'
                        f'</div>'
                    )

                # Account Category colour coding — apply display formatting then colour-code
                # Use word-boundary regex to avoid false positives like "cat 12" → "cat 1"
                _acct_cat_val = format_account_category(_segmentation.get('account_category', ''))
                _acct_cat_lower = str(_acct_cat_val).lower()
                if re.search(_CAT_REGEX_12, _acct_cat_lower):
                    _acct_cat_highlight = 'green'
                elif re.search(_CAT_REGEX_3, _acct_cat_lower):
                    _acct_cat_highlight = 'red'
                else:
                    _acct_cat_highlight = None

                # Section 1 — About The Account (6 rows × 2 columns)
                _parent_account_disp = _research.get('_parent_account', '')
                _reporting_group_disp = _research.get('_reporting_group', '')
                _rg_source = _research.get('_reporting_group_source', '')
                _rg_note = "AI-generated friendly name (no matching entry in Salesforce)" if _rg_source == 'ai' else None
                _s1_left = [
                    _sf_field("Account Name",            _account_name),
                    _sf_field("Account Type",            _account_type),
                    _sf_field("Parent Account",          _parent_account_disp,
                              greyed=not bool(_parent_account_disp)),
                    _sf_field("Reporting Group",         _reporting_group_disp,
                              greyed=not bool(_reporting_group_disp), note=_rg_note),
                    _sf_field("Account Owner",           "",  greyed=True),
                    _sf_field("Secondary Account Owner", _segmentation.get('secondary_account_owner', '')),
                ]
                _s1_right = [
                    _sf_field("Market Segment",            _research.get('market_segment', '')),
                    _sf_field("Business Segment",          _research.get('business_segment', '')),
                    _sf_field("Detailed Business Segment", _research.get('detailed_business_segment', '')),
                    _sf_field("Customer Segment",          _seg_display,
                              note=_rationale if _rationale else None),
                    _sf_field("Account Category",          _acct_cat_val,
                              note=_segmentation.get('account_category_note', '') or None,
                              highlight=_acct_cat_highlight),
                    _sf_field("Priority Account",          "",  greyed=True),
                ]
                _s1_cells = "".join(left_cell + right_cell for left_cell, right_cell in zip(_s1_left, _s1_right))

                # AUM: always visible; show "N/A — not applicable" when LLM flags it as N/A
                _aum_raw = _research.get('aum_eur', '')
                _aum_display = (
                    "N/A — not applicable"
                    if str(_aum_raw).strip().upper() in ('N/A', 'NOT FOUND', 'NOT APPLICABLE', '')
                    else _aum_raw
                )

                # Section 2 — Supplementary Account Information (4 rows + rationale row)
                _s2_rows = [
                    (_sf_field("BvD ID (Moody's)", "",  greyed=True),
                     _sf_field("Account ID",        "",  greyed=True)),
                    (_sf_field("NAICS Code",         "",  greyed=True),
                     _sf_field("Annual Revenue",     _research.get('annual_revenue_eur', ''),
                               source_url=_llm_sources.get('revenue_source'))),
                    (_sf_field("Legal Name (BvD)",   _research.get('legal_name', '')),
                     _sf_field("Employees",          _research.get('employees', ''),
                               source_url=_llm_sources.get('employees_source'))),
                    (_sf_field("Ultimate Parent",    _research.get('ultimate_parent', '')),
                     _sf_field("AUM (EUR)",          _aum_display,
                               source_url=_llm_sources.get('aum_source'))),
                ]
                _s2_cells = "".join(left_cell + right_cell for left_cell, right_cell in _s2_rows)
                # Industry Classification Rationale spans left column only
                _s2_cells += (
                    _sf_field("Industry Classification Rationale",
                              _research.get('industry_classification_rationale', ''))
                    + '<div class="sf-field"></div>'
                )

                st.markdown(f"""
<div class="sf-layout">
  <div class="sf-section">
    <div class="sf-section-header">About The Account</div>
    <div class="sf-fields-grid">{_s1_cells}</div>
  </div>
  <div class="sf-section">
    <div class="sf-section-header">Supplementary Account Information</div>
    <div class="sf-fields-grid">{_s2_cells}</div>
  </div>
</div>
""", unsafe_allow_html=True)

                # Data freshness indicator
                _search_method_display = _research.get('_search_method')
                _resp_api_err_display = _research.get('_responses_api_error')
                if _search_method_display == "responses_api_web_search":
                    st.success("🌐 **Live data** — sourced via real-time web search (OpenAI gpt-4.1 Responses API)")
                elif _search_method_display == "chat_completions_fallback":
                    _err_detail = f"\n\n🔍 **Error detail:** {_resp_api_err_display}" if _resp_api_err_display else ""
                    st.warning(
                        f"⚠️ **TRAINING DATA FALLBACK** — Live web search (Responses API) was unavailable "
                        f"after 2 retries. Data sourced from AI training data and **may be significantly outdated**. "
                        f"Revenue and employee figures are annotated with '(training data, may be outdated)'.{_err_detail}"
                    )

                # Alternative segment warning (Change 6)
                _alt_seg = _research.get('alternative_detailed_business_segment', '')
                if _alt_seg:
                    st.warning(
                        f"⚠️ **Multiple Detailed Business Segments could apply** for this company: "
                        f"**{_research.get('detailed_business_segment', '')}** (selected) and "
                        f"**{_alt_seg}** (alternative). "
                        "Please review and confirm the most appropriate segment."
                    )

                # ── ICP CHARACTERISTICS STEP ───────────────────────────────────
                st.divider()
                st.markdown('<p class="fen-section-title">ICP Characteristics Assessment</p>', unsafe_allow_html=True)
                st.markdown(
                    "Run deep AI research to assess whether **" + html_escape(_account_name) +
                    "** meets Fenergo's Ideal Customer Profile (ICP) criteria. "
                    "This drills beyond segmentation to evaluate strategic fit.",
                    unsafe_allow_html=False
                )

                _icp_run_btn = st.button("🔍 Run ICP Characteristics", type="primary", use_container_width=True, key="run_icp_btn")
                if _icp_run_btn:
                    st.session_state["tab1_icp_requested"] = True
                    st.session_state["tab1_icp_results"] = None
                    st.rerun()

                # Run ICP research when requested and results not yet available
                if st.session_state.get("tab1_icp_requested") and st.session_state.get("tab1_icp_results") is None:
                    # Run ICP research
                    if not icp_characteristics:
                        st.error("ICP Characteristics file not loaded. Please ensure 'ICP Characteristics.xlsx' is in the repo root.")
                    else:
                        _icp_results = []
                        with st.status("Running ICP Characteristics research (live web search)...", expanded=True) as _icp_status:
                            for _ic in icp_characteristics:
                                _ic_name = _ic["characteristic"]
                                st.write(f"🔍 Researching: **{_ic_name}** (weight: {_ic['weight']}%)")
                                _scoring_rubric = {
                                    "1": _ic["score_1"], "2": _ic["score_2"],
                                    "3": _ic["score_3"], "4": _ic["score_4"],
                                    "5": _ic["score_5"],
                                }
                                _ic_result = research_icp_characteristic(
                                    _account_name, _ic_name, _ic["what_it_measures"],
                                    _ic["weight"], _ic["evidence"], _scoring_rubric
                                )
                                _ic_result["characteristic"] = _ic_name
                                _ic_result["weight"] = _ic["weight"]
                                _ic_result["what_it_measures"] = _ic["what_it_measures"]
                                _ic_result["id"] = _ic["id"]
                                _icp_results.append(_ic_result)
                                _score_emoji = {0:"⬜",1:"🔴",2:"🟠",3:"🟡",4:"🟢",5:"✅"}.get(_ic_result["score"], "⬜")
                                st.write(f"  {_score_emoji} Score: {_ic_result['score']}/5 — {_ic_result['score_label']}")
                            _icp_status.update(label="ICP Characteristics research complete", state="complete")
                        st.session_state["tab1_icp_results"] = _icp_results

                # Display ICP results if available
                _icp_results_display = st.session_state.get("tab1_icp_results")
                if _icp_results_display and _icp_results_display != "__running__":
                    # Individual characteristic cards
                    _score_css = {0:"icp-score-0",1:"icp-score-1",2:"icp-score-2",3:"icp-score-3",4:"icp-score-4",5:"icp-score-5"}
                    _score_emoji = {0:"⬜",1:"🔴",2:"🟠",3:"🟡",4:"🟢",5:"✅"}

                    for _ir in _icp_results_display:
                        _sc = _ir.get("score", 0)
                        _sc_class = _score_css.get(_sc, "icp-score-0")
                        _sc_emoji = _score_emoji.get(_sc, "⬜")
                        _src_url = _ir.get("source_url")
                        _src_html = ""
                        if _src_url and isinstance(_src_url, str) and _src_url.startswith("http"):
                            _src_display = _src_url[:70] + "..." if len(_src_url) > 70 else _src_url
                            _src_html = f'<a href="{_src_url}" target="_blank" rel="noopener noreferrer" style="font-size:0.75rem;color:#21CFB2;">🔗 {_src_display}</a>'
                        elif _sc == 0:
                            _src_html = '<span style="color:#706e6b;font-size:0.75rem;">No information found</span>'

                        _method = _ir.get("search_method", "")
                        _method_badge = ""
                        if _method == "responses_api_web_search":
                            _method_badge = '<span style="background:#d1fae5;color:#065f46;font-size:0.7rem;padding:1px 6px;border-radius:10px;font-weight:600;">🌐 Live Web</span>'
                        elif _method == "chat_completions_fallback":
                            _method_badge = '<span style="background:#fef3c7;color:#92400e;font-size:0.7rem;padding:1px 6px;border-radius:10px;font-weight:600;">⚠️ Training Data</span>'

                        st.markdown(f"""
<div class="icp-card">
  <div class="icp-card-title">
    {_sc_emoji} {html_escape(_ir.get('characteristic', ''))}
    <span class="icp-score-badge {_sc_class}">{_sc}/5 — {html_escape(_ir.get('score_label', ''))}</span>
    <span style="font-size:0.72rem;color:#5a7a7a;margin-left:8px;">Weight: {_ir.get('weight', 0)}%</span>
    {_method_badge}
  </div>
  <div style="font-size:0.82rem;color:#4a5568;margin-bottom:8px;">{html_escape(_ir.get('assessment', 'No assessment available.'))}</div>
  <div>{_src_html}</div>
</div>
""", unsafe_allow_html=True)

                    # Overall ICP Assessment
                    _total_weight = sum(ir.get("weight", 0) for ir in _icp_results_display)
                    _weighted_score = sum(ir.get("score", 0) * ir.get("weight", 0) for ir in _icp_results_display)
                    _max_weighted = 5 * _total_weight
                    _icp_pct = round((_weighted_score / _max_weighted * 100) if _max_weighted > 0 else 0, 1)
                    _criteria_met = sum(1 for ir in _icp_results_display if ir.get("score", 0) >= 3)
                    _total_criteria = len(_icp_results_display)

                    if _icp_pct >= 70:
                        _icp_verdict = "✅ Strong ICP Fit"
                        _verdict_note = "This account strongly matches Fenergo's ICP criteria."
                    elif _icp_pct >= 45:
                        _icp_verdict = "🟡 Moderate ICP Fit"
                        _verdict_note = "This account shows moderate ICP alignment — further qualification recommended."
                    else:
                        _icp_verdict = "🔴 Weak ICP Fit"
                        _verdict_note = "This account shows limited ICP alignment at this stage."

                    st.markdown(f"""
<div class="icp-overall">
  <div class="icp-overall-title">🎯 Overall ICP Assessment</div>
  <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
    <div>
      <div class="icp-overall-score">{_icp_pct}%</div>
      <div style="color:rgba(255,255,255,0.7);font-size:0.78rem;">Weighted ICP Score</div>
    </div>
    <div>
      <div style="font-size:1.4rem;font-weight:700;color:#21CFB2;">{_criteria_met}/{_total_criteria}</div>
      <div style="color:rgba(255,255,255,0.7);font-size:0.78rem;">Criteria met (score ≥ 3)</div>
    </div>
    <div style="flex:1;min-width:200px;">
      <div style="font-size:1rem;font-weight:700;color:#ffffff;margin-bottom:4px;">{_icp_verdict}</div>
      <div style="color:rgba(255,255,255,0.75);font-size:0.82rem;">{_verdict_note}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ===============================================
# TAB 2 — BULK ACCOUNT ENRICHMENT
# ===============================================
with tab2:
    st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Bulk Account Enrichment</span></div>', unsafe_allow_html=True)

    # 3-step workflow stepper
    st.markdown("""
<div class="workflow-stepper">
  <div class="workflow-step">
    <div class="workflow-step-num">1</div>
    <div class="workflow-step-title">⬆️ Upload &amp; Match</div>
    <div class="workflow-step-desc">Upload your list of potential new accounts. Each account is fuzzy-matched against your existing Salesforce accounts to identify overlaps.</div>
  </div>
  <div class="workflow-step">
    <div class="workflow-step-num">2</div>
    <div class="workflow-step-title">📥 Review &amp; Download</div>
    <div class="workflow-step-desc">Download the matching results as CSV. Review the matches — identify which accounts did <strong>not</strong> match (new accounts that need to be created).</div>
  </div>
  <div class="workflow-step">
    <div class="workflow-step-num">3</div>
    <div class="workflow-step-title">✨ Enrich &amp; Create</div>
    <div class="workflow-step-desc">Run unmatched accounts through Bulk Enrichment below. Download the enriched CSV and import into Salesforce to create the new records.</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<p class="fen-section-title">Step 1 — Account Matching</p>', unsafe_allow_html=True)
    NO_VALUE_PLACEHOLDER = "—"
    HIGH_CONFIDENCE_THRESHOLD = 80
    MAX_TOP_MATCHES_TO_CONSIDER = 10

    st.markdown(f"""
Upload your list of potential new accounts (CSV or Excel). Each name is fuzzy-matched against the
**Account Name** and **Legal Name** columns in the Salesforce Accounts CSV loaded in the sidebar.
Results show a confidence score — accounts below the threshold are marked **"No match found"** and
are candidates for new record creation via Step 3.

**Scoring rules:**
- **100%** = exact Account Name match (after normalisation) — no blending applied
- Otherwise: **{int(ACCT_WEIGHT*100)}% Account Name** + **{int(LEGAL_WEIGHT*100)}% Legal Name** weighted blend
- Both the matched Account Name and Legal Name are shown for Primary and Secondary matches
""")

    st.markdown("""
<div class="dropzone-container">
  <div class="dropzone-label">📂 Upload New Customer File (CSV or Excel)</div>
  <div class="dropzone-hint">Drag &amp; drop your file here, or click Browse to select — CSV, XLSX, or XLS formats supported.</div>
</div>
""", unsafe_allow_html=True)

    new_customer_file = st.file_uploader(
        "Upload New Customer File (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        key="account_matching_upload",
        help="Maximum recommended file size: 10 MB",
        label_visibility="collapsed",
    )

    if new_customer_file is not None:
        try:
            if new_customer_file.name.endswith(('.xlsx', '.xls')):
                new_customers_df = pd.read_excel(new_customer_file)
            else:
                new_customers_df = pd.read_csv(new_customer_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        name_col_candidates = [c for c in new_customers_df.columns if any(
            kw in c.lower() for kw in ['name', 'account', 'customer', 'company', 'organisation', 'organization']
        )]
        if name_col_candidates:
            default_col = name_col_candidates[0]
        else:
            default_col = new_customers_df.columns[0]

        name_column = st.selectbox(
            "Select the column containing customer names:",
            options=new_customers_df.columns.tolist(),
            index=new_customers_df.columns.tolist().index(default_col)
        )

        new_country_col_candidates = [c for c in new_customers_df.columns if 'country' in c.lower()]
        new_customer_country_col_options = ["(none)"] + new_customers_df.columns.tolist()
        default_country_idx = 0
        if new_country_col_candidates:
            default_country_idx = new_customer_country_col_options.index(new_country_col_candidates[0])
        new_customer_country_col_raw = st.selectbox(
            "Select the Country column in the New Customer file (optional — used to refine match suggestions):",
            options=new_customer_country_col_options,
            index=default_country_idx,
            key="new_cust_country_col"
        )
        new_customer_country_col = new_customer_country_col_raw if new_customer_country_col_raw != "(none)" else None

        st.info(f"📋 Loaded **{len(new_customers_df)}** new customers from uploaded file.")

        if sf_accounts is None:
            st.warning("⚠️ No Salesforce Accounts CSV uploaded. Please upload it in the sidebar first.")
        else:
            sf_columns = sf_accounts.columns.tolist()
            sf_columns_lc = {c: c.lower() for c in sf_columns}

            def pick_col(primary_terms, secondary_terms=None, exclude_terms=None):
                secondary_terms = secondary_terms or []
                exclude_terms = exclude_terms or []
                candidates = [
                    c for c in sf_columns
                    if not any(ex in sf_columns_lc[c] for ex in exclude_terms)
                ]
                for term in primary_terms:
                    for c in candidates:
                        if term in sf_columns_lc[c]:
                            return c
                for term in secondary_terms:
                    for c in candidates:
                        if term in sf_columns_lc[c]:
                            return c
                return None

            account_col_candidates = [c for c in sf_columns if 'id' not in sf_columns_lc[c]]
            sf_account_name_col = next(
                (c for c in account_col_candidates if sf_columns_lc[c].strip() == 'account name'),
                None
            )
            if sf_account_name_col is None:
                sf_account_name_col = pick_col(
                    primary_terms=['account name'],
                    secondary_terms=['name', 'account'],
                    exclude_terms=['id']
                )
            sf_legal_name_col = pick_col(primary_terms=['legal name'], secondary_terms=['legal'])
            sf_country_col = pick_col(primary_terms=['country'], secondary_terms=[])

            detected_columns = []
            if sf_account_name_col:
                detected_columns.append(f'Account Name → "{sf_account_name_col}"')
            if sf_legal_name_col:
                detected_columns.append(f'Legal Name → "{sf_legal_name_col}"')
            if sf_country_col:
                detected_columns.append(f'Country → "{sf_country_col}"')
            if detected_columns:
                st.success(" | ".join(detected_columns))

            confidence_threshold = st.slider(
                "Minimum confidence threshold to show a match (%)",
                min_value=0, max_value=100, value=60, step=5,
                help="Matches below this threshold will be marked as 'No match found'"
            )

            run_matching = st.button("▶ Run Account Matching", type="primary", use_container_width=True)

            if run_matching:
                new_names = new_customers_df[name_column].dropna().astype(str).tolist()
                new_customer_country_map = {}
                if new_customer_country_col:
                    country_df = new_customers_df[[name_column, new_customer_country_col]].drop_duplicates(
                        subset=[name_column],
                        keep="first"
                    )
                    for _, country_row in country_df.iterrows():
                        row_name = str(country_row.get(name_column, "")).strip()
                        row_country = country_row.get(new_customer_country_col, "")
                        if row_name and pd.notna(row_country):
                            new_customer_country_map[row_name] = str(row_country).strip().lower()

                sf_records = sf_accounts.to_dict("records")

                # Pre-compute normalised names for every SF record once to avoid
                # repeated normalize_name() calls inside the inner loop (O(n²) → O(n+m)).
                sf_records_normalised = []
                for row in sf_records:
                    acct_name_val = ""
                    acct_norm = ""
                    if sf_account_name_col:
                        val = row.get(sf_account_name_col, "")
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str:
                                acct_name_val = val_str
                                acct_norm = normalize_name(val_str)
                    legal_name_val = ""
                    legal_norm = ""
                    if sf_legal_name_col:
                        val = row.get(sf_legal_name_col, "")
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str:
                                legal_name_val = val_str
                                legal_norm = normalize_name(val_str)
                    sf_country_val = ""
                    if sf_country_col:
                        raw = row.get(sf_country_col, "")
                        sf_country_val = str(raw).strip() if pd.notna(raw) else ""
                    sf_records_normalised.append((
                        acct_name_val, acct_norm,
                        legal_name_val, legal_norm,
                        sf_country_val,
                    ))

                results = []
                progress = st.progress(0, text="Matching accounts...")

                total = len(new_names)
                for i, new_name in enumerate(new_names):
                    new_norm = normalize_name(new_name)

                    # Each entry: (rep_score, acct_name_val, legal_name_val, sf_country_val, acct_score, legal_score)
                    top_matches = []

                    for acct_name_val, acct_norm, legal_name_val, legal_norm, sf_country_val in sf_records_normalised:
                        # ── Score against Account Name column ──────────────────────────
                        acct_score = 0
                        if acct_name_val:
                            acct_score = compute_match_score(new_norm, acct_norm)

                        # ── Score against Legal Name column ────────────────────────────
                        legal_score = 0
                        if legal_name_val:
                            legal_score = compute_match_score(new_norm, legal_norm)

                        # ── Combined score ─────────────────────────────────────────────
                        # If account name is exact (100) → overall = 100.
                        # Otherwise → 70% acct + 30% legal weighted blend.
                        rep_score = combined_score(acct_score, legal_score)

                        if rep_score > 0 and acct_name_val:
                            top_matches.append((
                                rep_score,
                                acct_name_val,
                                legal_name_val,
                                sf_country_val,
                                acct_score,
                                legal_score,
                            ))

                    # Sort by combined score descending, keep top N
                    top_matches = sorted(top_matches, key=lambda x: x[0], reverse=True)[:MAX_TOP_MATCHES_TO_CONSIDER]
                    new_cust_country = new_customer_country_map.get(str(new_name).strip(), "")

                    # ── Filter by confidence threshold ─────────────────────────────────
                    primary_name       = "No match found"
                    primary_legal      = NO_VALUE_PLACEHOLDER
                    primary_score      = None
                    primary_sf_country = ""
                    secondary_name     = NO_VALUE_PLACEHOLDER
                    secondary_legal    = NO_VALUE_PLACEHOLDER
                    secondary_score    = None

                    if top_matches:
                        eligible = [m for m in top_matches if m[0] >= confidence_threshold]

                        # Country-aware re-sort: country match used as tiebreaker
                        if eligible and new_cust_country:
                            eligible = sorted(
                                eligible,
                                key=lambda x: (
                                    x[0],
                                    1 if str(x[3] or "").strip().lower() == new_cust_country else 0,
                                ),
                                reverse=True
                            )

                        if eligible:
                            primary_score      = round(eligible[0][0], 1)
                            primary_name       = eligible[0][1]
                            primary_legal      = eligible[0][2] if eligible[0][2] else NO_VALUE_PLACEHOLDER
                            primary_sf_country = eligible[0][3]
                            if len(eligible) > 1:
                                secondary_score = round(eligible[1][0], 1)
                                secondary_name  = eligible[1][1]
                                secondary_legal = eligible[1][2] if eligible[1][2] else NO_VALUE_PLACEHOLDER
                        else:
                            primary_name  = "No match found"
                            primary_score = None

                    # ── Country match flag ─────────────────────────────────────────────
                    country_match_flag = ""
                    if new_cust_country and primary_sf_country:
                        country_match_flag = "✅" if primary_sf_country.strip().lower() == new_cust_country else "⬜"

                    results.append({
                        "New Customer Name":          new_name,
                        "Primary Match (Account)":    primary_name,
                        "Primary Match (Legal Name)": primary_legal,
                        "Confidence Score (%)":       primary_score if primary_score is not None else NO_VALUE_PLACEHOLDER,
                        "Country Match":              country_match_flag,
                        "Secondary Match (Account)":    secondary_name,
                        "Secondary Match (Legal Name)": secondary_legal,
                        "Secondary Confidence (%)":   secondary_score if secondary_score is not None else NO_VALUE_PLACEHOLDER,
                    })

                    if (i + 1) % max(1, total // 20) == 0 or i == total - 1:
                        progress.progress((i + 1) / total, text=f"Matching accounts... {i+1}/{total}")

                progress.empty()

                results_df = pd.DataFrame(results)

                matched   = results_df[results_df["Primary Match (Account)"] != "No match found"]
                unmatched = results_df[results_df["Primary Match (Account)"] == "No match found"]
                high_conf = matched[
                    pd.to_numeric(matched["Confidence Score (%)"], errors='coerce') >= HIGH_CONFIDENCE_THRESHOLD
                ]

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Total New Customers", total)
                col_m2.metric("Matched", len(matched))
                col_m3.metric(f"High Confidence (≥{HIGH_CONFIDENCE_THRESHOLD}%)", len(high_conf))
                col_m4.metric("No Match Found", len(unmatched))

                st.divider()
                st.markdown('<p class="fen-section-title">Matching Results</p>', unsafe_allow_html=True)

                styled_df = results_df.style.map(
                    _highlight_conf,
                    subset=["Confidence Score (%)"]
                )
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                st.markdown('<p class="fen-section-title">Step 2 — Review &amp; Download Results</p>', unsafe_allow_html=True)
                st.markdown("""
Review the matches above. Accounts with **"No match found"** are new accounts that do not yet exist in
Salesforce. Download the CSV, identify the unmatched rows, and take them to **Step 3** (Bulk Enrichment below)
to enrich and prepare them for import.
""")

                export_df = results_df.copy()
                for col in ["Confidence Score (%)", "Secondary Confidence (%)"]:
                    export_df[col] = export_df[col].replace(NO_VALUE_PLACEHOLDER, "")
                for col in ["Secondary Match (Account)", "Secondary Match (Legal Name)", "Primary Match (Legal Name)"]:
                    export_df[col] = export_df[col].replace(NO_VALUE_PLACEHOLDER, "")

                csv_buffer = io.StringIO()
                export_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode("utf-8")

                st.download_button(
                    label="⬇️ Download Results as CSV",
                    data=csv_bytes,
                    file_name="account_matching_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    else:
        st.markdown("""
        <div class="placeholder-box">
            <h3>Step 1 — Account Matching</h3>
            <p>Upload a New Customer file above to begin.<br>
            Ensure the Salesforce Accounts CSV is also loaded in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)

    # ── BULK CUSTOMER ENRICHMENT (Step 3) ─────────────────────────────────────
    st.divider()
    st.markdown('<p class="fen-section-title">Step 3 — Bulk Customer Enrichment</p>', unsafe_allow_html=True)
    st.markdown(
        """
        Take the **unmatched accounts** from Step 1 (those with "No match found") and upload them here.
        The tool runs the same AI enrichment logic as **Single Account Enrichment** — LLM web research,
        segment resolution, and Account Category matrix lookup — for every row simultaneously.
        Download the enriched CSV and import directly into Salesforce to create the new records.
        """
    )

    st.markdown("""
<div class="dropzone-container">
  <div class="dropzone-label">📂 Upload CSV of Unmatched Accounts</div>
  <div class="dropzone-hint">Drag &amp; drop your CSV file here, or click Browse to select — must contain <strong>Account Name</strong> and <strong>Country</strong> columns.</div>
</div>
""", unsafe_allow_html=True)

    bulk_enrich_file = st.file_uploader(
        "Upload CSV (Account Name + Country)",
        type=["csv"],
        key="bulk_enrich_upload",
        help="Must contain at least Account Name and Country columns. Maximum recommended size: 10 MB.",
        label_visibility="collapsed",
    )

    if bulk_enrich_file is not None:
        try:
            bulk_df_raw = pd.read_csv(bulk_enrich_file)
        except Exception as _e:
            st.error(f"Error reading bulk enrichment file: {_e}")
        else:
            # ── Auto-detect columns ──────────────────────────────────────────
            _b_cols = bulk_df_raw.columns.tolist()
            _b_cols_lc = {c: c.lower().strip() for c in _b_cols}

            # Account Name column
            _b_name_col = None
            for _c in _b_cols:
                if _b_cols_lc[_c] in ('account name', 'accountname', 'account'):
                    _b_name_col = _c
                    break
            if _b_name_col is None:
                for _c in _b_cols:
                    if any(kw in _b_cols_lc[_c] for kw in ('name', 'customer', 'company', 'organisation', 'organization')):
                        _b_name_col = _c
                        break
            if _b_name_col is None and _b_cols:
                _b_name_col = _b_cols[0]

            # Country column
            _b_country_col = None
            for _c in _b_cols:
                if _b_cols_lc[_c] == 'country':
                    _b_country_col = _c
                    break
            if _b_country_col is None:
                for _c in _b_cols:
                    if 'country' in _b_cols_lc[_c]:
                        _b_country_col = _c
                        break

            _b_name_col = st.selectbox(
                "Account Name column",
                options=_b_cols,
                index=_b_cols.index(_b_name_col) if _b_name_col in _b_cols else 0,
                key="bulk_name_col",
            )
            _b_country_col_opts = ["(none)"] + _b_cols
            _b_country_default_idx = (
                _b_country_col_opts.index(_b_country_col)
                if _b_country_col and _b_country_col in _b_country_col_opts
                else 0
            )
            _b_country_col_sel = st.selectbox(
                "Country column",
                options=_b_country_col_opts,
                index=_b_country_default_idx,
                key="bulk_country_col",
            )
            _b_country_col = _b_country_col_sel if _b_country_col_sel != "(none)" else None

            st.info(f"📋 **{len(bulk_df_raw)}** rows loaded from uploaded file.")

            if client is None:
                st.error("⚠️ OpenAI client not configured — bulk enrichment requires the AI research step.")
            else:
                run_bulk = st.button(
                    "▶ Run Bulk Enrichment",
                    type="primary",
                    use_container_width=True,
                    key="run_bulk_enrich",
                )

                if run_bulk:
                    _bulk_rows = bulk_df_raw.dropna(subset=[_b_name_col]).to_dict("records")
                    _bulk_results = []
                    _bulk_progress = st.progress(0, text="Enriching accounts...")
                    _bulk_total = len(_bulk_rows)

                    for _bi, _brow in enumerate(_bulk_rows):
                        _b_acct_name = str(_brow.get(_b_name_col, "")).strip()
                        _b_country = (
                            str(_brow.get(_b_country_col, "")).strip()
                            if _b_country_col else ""
                        )
                        _b_region = COUNTRY_REGION_MAP.get(_b_country, "")

                        # Step A: LLM enrichment (same as Tab 1 Step 2)
                        _b_research = {}
                        try:
                            _b_llm_data = enrich_with_llm([], _b_acct_name)
                            if '_llm_error' not in _b_llm_data:
                                _empty = {None, 'Not found', 'N/A', ''}
                                for _k, _v in _b_llm_data.items():
                                    if _k == 'sources':
                                        if isinstance(_v, dict):
                                            _b_research[_k] = _v
                                    elif _k.startswith('_'):
                                        _b_research[_k] = _v
                                    elif _v not in _empty:
                                        _b_research[_k] = _v
                        except Exception:
                            pass

                        # Step B: resolve segment roll-ups from hierarchy
                        _b_det_seg = _b_research.get('detailed_business_segment', '')
                        if _b_det_seg:
                            _b_seg_resolved = resolve_segment(_b_det_seg)
                            if _b_seg_resolved:
                                _b_research['business_segment'] = _b_seg_resolved['business']
                                _b_research['market_segment'] = _b_seg_resolved['market']

                        # Step C: Parent Account + Reporting Group from SF upload
                        _b_ult_parent = _b_research.get('ultimate_parent', '')
                        _b_parent_acct = ''
                        _b_rgroup = ''
                        if _b_ult_parent and sf_accounts is not None:
                            _b_sf_pa, _b_sf_rg = lookup_sf_ultimate_parent(
                                sf_accounts, _b_ult_parent, account_name=_b_acct_name
                            )
                            if _b_sf_pa:
                                _b_parent_acct = _b_sf_pa
                            if _b_sf_rg:
                                _b_rgroup = _b_sf_rg
                            elif _b_research.get('reporting_group_suggestion'):
                                _b_rgroup = _b_research['reporting_group_suggestion']
                        elif _b_research.get('reporting_group_suggestion'):
                            _b_rgroup = _b_research['reporting_group_suggestion']

                        # Step D: segmentation (customer segment, account category, secondary owner)
                        _b_segmentation = apply_segmentation(
                            _b_research, _b_acct_name, _b_region, _b_country
                        )

                        _bulk_results.append({
                            "Account Name":              _b_acct_name,
                            "Country":                   _b_country,
                            "Region":                    _b_region,
                            "Legal Name":                _b_research.get('legal_name', ''),
                            "Ultimate Parent":           _b_ult_parent,
                            "Parent Account":            _b_parent_acct,
                            "Reporting Group":           _b_rgroup,
                            "Detailed Business Segment": _b_research.get('detailed_business_segment', ''),
                            "Business Segment":          _b_research.get('business_segment', ''),
                            "Market Segment":            _b_research.get('market_segment', ''),
                            "Customer Segment":          _b_segmentation.get('customer_segment', ''),
                            "Account Category":          format_account_category(_b_segmentation.get('account_category', '')),
                            "Secondary Account Owner":   _b_segmentation.get('secondary_account_owner', ''),
                            "Annual Revenue":             _b_research.get('annual_revenue_eur', ''),
                            "Employees":                 _b_research.get('employees', ''),
                            "AUM":                       _b_research.get('aum_eur', ''),
                        })

                        _bulk_progress.progress(
                            (_bi + 1) / _bulk_total,
                            text=f"Enriching accounts... {_bi + 1}/{_bulk_total} — {_b_acct_name}"
                        )

                    _bulk_progress.empty()

                    st.success(f"✅ Bulk enrichment complete — {len(_bulk_results)} accounts processed.")
                    _bulk_results_df = pd.DataFrame(_bulk_results)
                    st.dataframe(_bulk_results_df, use_container_width=True, hide_index=True)

                    _bulk_csv_buf = io.StringIO()
                    _bulk_results_df.to_csv(_bulk_csv_buf, index=False)
                    st.download_button(
                        label="⬇️ Download Results as CSV",
                        data=_bulk_csv_buf.getvalue().encode("utf-8"),
                        file_name="bulk_enrichment_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

# ===============================================
# TAB 3 — LEAD MATCHING (placeholder)
# ===============================================
with tab3:
    st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Lead Matching</span></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="placeholder-box">
        <h3>Lead Matching</h3>
        <p>This module is coming soon.<br>
        It will automatically match enriched accounts against open leads in Salesforce,<br>
        surfacing potential overlaps and routing recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================================
# TAB 4 — REFERENCE & PROCESS OVERVIEW
# ===============================================
with tab4:
    st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Reference &amp; Process Overview</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="fen-section-title">Reference &amp; Process Overview</p>', unsafe_allow_html=True)
    st.markdown("""
This tab provides reference documentation for the Account Intelligence pipeline:
the overall data flow, customer segment logic, segmentation hierarchy, and field population details.
""")

    # ── Overall Data Flow Diagram ─────────────────────────────────────────────
    st.markdown('<p class="fen-section-title">📊 Overall Data Flow</p>', unsafe_allow_html=True)
    st.markdown("""
<div class="flow-outer">
<div style="font-size:0.82rem;color:#5a7a7a;margin-bottom:16px;">
This diagram shows how each data attribute is sourced and how they flow into the <strong>Account Category</strong> — the central output of the enrichment pipeline.
</div>

<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:center;margin-bottom:16px;">
  <div style="display:flex;flex-direction:column;gap:8px;">
    <div class="flow-box" style="background:#e8f7f5;">🌐 Revenue (Live Web)</div>
    <div class="flow-box" style="background:#e8f7f5;">🌐 AUM (Live Web)</div>
    <div class="flow-box" style="background:#e8f7f5;">🌐 Employees (Live Web)</div>
  </div>
  <div class="flow-arrow" style="text-align:center;">→</div>
  <div style="text-align:center;">
    <div class="flow-box" style="background:#fff3cd;border-color:#856404;color:#002E33;">📊 Customer Segment<br><span style="font-size:0.7rem;font-weight:400;">(Enterprise / Mid-Market / Scale-up)</span></div>
  </div>
  <div class="flow-arrow" style="text-align:center;">→</div>
  <div style="text-align:center;">
    <div class="flow-box-centre">🗂️ Account Category<br><span style="font-size:0.72rem;font-weight:400;">(Cat 1 / 2 / 3)</span></div>
    <div class="flow-note">Central output of the enrichment pipeline</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:start;margin-bottom:16px;">
  <div style="display:flex;flex-direction:column;gap:6px;">
    <div class="flow-box" style="background:#e8f7f5;">🌐 Detailed Business Segment<br><span style="font-size:0.7rem;font-weight:400;">(AI web research)</span></div>
    <div style="margin-left:16px;display:flex;flex-direction:column;gap:4px;">
      <div style="color:#21CFB2;font-size:0.8rem;text-align:center;">↓ spin-off</div>
      <div class="flow-box" style="font-size:0.75rem;background:#ede9fe;border-color:#7c3aed;color:#4c1d95;">🤖 Industry Classification<br>Rationale</div>
    </div>
  </div>
  <div class="flow-arrow" style="text-align:center;padding-top:8px;">→</div>
  <div style="display:flex;flex-direction:column;gap:6px;padding-top:2px;">
    <div class="flow-box" style="background:#e8f7f5;">📊 Market Segment<br><span style="font-size:0.7rem;font-weight:400;">(from mapping table)</span></div>
    <div class="flow-box" style="background:#e8f7f5;">📂 Business Segment<br><span style="font-size:0.7rem;font-weight:400;">(from mapping table)</span></div>
  </div>
  <div class="flow-arrow" style="text-align:center;padding-top:20px;">→</div>
  <div style="padding-top:20px;">
    <div style="font-size:0.78rem;color:#5a7a7a;text-align:center;">Business Segment flows<br>into Customer Segment &amp;<br>Account Category lookup</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:start;margin-bottom:16px;">
  <div style="display:flex;flex-direction:column;gap:6px;">
    <div class="flow-box" style="background:#ede9fe;border-color:#7c3aed;color:#4c1d95;">👤 Country<br><span style="font-size:0.7rem;font-weight:400;">(user input)</span></div>
    <div style="margin-left:16px;display:flex;flex-direction:column;gap:4px;">
      <div style="color:#21CFB2;font-size:0.8rem;text-align:center;">↓ spin-off</div>
      <div class="flow-box" style="font-size:0.75rem;background:#d1fae5;border-color:#065f46;color:#065f46;">👥 Secondary Account Owner<br><span style="font-size:0.68rem;">(from country mapping table)</span></div>
    </div>
  </div>
  <div class="flow-arrow" style="text-align:center;padding-top:8px;">→</div>
  <div style="padding-top:8px;">
    <div class="flow-box-centre" style="font-size:0.82rem;">🗂️ Account Category<br><span style="font-size:0.7rem;font-weight:400;">(Cat 1 / 2 / 3)</span></div>
    <div class="flow-note" style="text-align:center;">Country logic determined by SAM review —<br>server availability, regulatory compliance strength, etc.</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:center;">
  <div>
    <div class="flow-box" style="background:#ede9fe;border-color:#7c3aed;color:#4c1d95;">👤 Customer Name<br><span style="font-size:0.7rem;font-weight:400;">(user input)</span></div>
  </div>
  <div class="flow-arrow" style="text-align:center;">→</div>
  <div>
    <div class="flow-box" style="background:#e8f7f5;">🌐 Ultimate Parent<br><span style="font-size:0.7rem;font-weight:400;">(AI web research)</span></div>
  </div>
  <div class="flow-arrow" style="text-align:center;">→</div>
  <div style="display:flex;flex-direction:column;gap:6px;">
    <div class="flow-box" style="background:#d1fae5;border-color:#065f46;color:#065f46;font-size:0.75rem;">📋 Reporting Group<br><span style="font-size:0.68rem;">(SF cross-ref or AI suggestion)</span></div>
    <div class="flow-box" style="background:#d1fae5;border-color:#065f46;color:#065f46;font-size:0.75rem;">🔗 Salesforce Parent Name<br><span style="font-size:0.68rem;">(SF cross-ref)</span></div>
  </div>
</div>

<div style="margin-top:16px;padding:10px 14px;background:#f0f9f8;border-radius:8px;font-size:0.78rem;color:#002E33;border-left:3px solid #21CFB2;">
  <strong>Legend:</strong>
  &nbsp; <span style="background:#e8f7f5;border:1px solid #21CFB2;padding:1px 6px;border-radius:4px;">🌐 Live Web Search</span>
  &nbsp; <span style="background:#ede9fe;border:1px solid #7c3aed;padding:1px 6px;border-radius:4px;color:#4c1d95;">👤 User Input</span>
  &nbsp; <span style="background:#d1fae5;border:1px solid #065f46;padding:1px 6px;border-radius:4px;color:#065f46;">🔗 SF Cross-ref</span>
  &nbsp; <span style="background:#fef3c7;border:1px solid #856404;padding:1px 6px;border-radius:4px;color:#856404;">📊 Rules / Matrix</span>
  &nbsp; <span style="background:#fff0f0;border:1px solid #dc2626;padding:1px 6px;border-radius:4px;color:#dc2626;">🗂️ Central Output</span>
</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # Sub-tabs for reference content
    ref_tab1, ref_tab2, ref_tab3 = st.tabs([
        "📊 Customer Segment Logic",
        "🏛️ Fenergo Segmentation",
        "📋 Field Population Logic",
    ])

    with ref_tab1:

        st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Customer Segment Logic</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="fen-section-title">Customer Segment Logic</p>', unsafe_allow_html=True)
        st.markdown("""
    This tab explains how the **Customer Segment** (Enterprise / Mid-Market / Scale-up) is derived for each account.
    The classification is based on the account's **Market Segment** combined with key financial metrics.
    """)

        # Visual flowchart diagram
        st.markdown("""
    <div class="fc-outer">
      <div class="fc-rule-banner">
        ⭐ &nbsp;HIGHEST TIER WINS &nbsp;—&nbsp; any single metric reaching the Enterprise threshold classifies the account as Enterprise, regardless of other metrics.
        &nbsp;&nbsp;|&nbsp;&nbsp; ❓ All metrics unknown → defaults to <strong>Scale-up</strong>
      </div>

      <div class="fc-segments-grid">

        <!-- Banks -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">🏦 Banks</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">AUM (Assets)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €200bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €10bn – €200bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €10bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Annual Revenue</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €10bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €2bn – €10bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €2bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Employees (FTE)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; 5,000</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› 1,000 – 5,000</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; 1,000</div>
            </div>
          </div>
        </div>

        <!-- Asset Mgmt -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">📈 Asset Mgmt., Servicing &amp; Insurance</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">AUM (Assets)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €100bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €10bn – €100bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €10bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Annual Revenue</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €10bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €2bn – €10bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €2bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Employees (FTE)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; 1,000</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› 150 – 1,000</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; 150</div>
            </div>
          </div>
        </div>

        <!-- Corporates -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">🏭 Corporates</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">AUM (Assets)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-na">N/A — not assessed for Corporates</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Annual Revenue</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €10bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €2bn – €10bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €2bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Employees (FTE)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; 5,000</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› 1,000 – 5,000</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; 1,000</div>
            </div>
          </div>
        </div>

        <!-- Fintech -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">💳 Fintech</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">AUM (Assets)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-na">N/A — not assessed for Fintech</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Annual Revenue</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €10bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €500m – €10bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €500m</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Employees (FTE)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; 1,000</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› 250 – 1,000</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; 250</div>
            </div>
          </div>
        </div>

        <!-- Full-Service Banks -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">🌐 Full-Service Banks</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">G-SIB designation</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› Automatic (G-SIB list match)</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">D-SIB designation</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› With regulator verification</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Neither G-SIB nor D-SIB</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-na">Falls back to Banks thresholds ↗</div>
            </div>
          </div>
        </div>

        <!-- Other / Default -->
        <div class="fc-segment-card">
          <div class="fc-seg-header">📦 Other / Default</div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">AUM (Assets)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-na">N/A — not assessed</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Annual Revenue</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; €10bn</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› €2bn – €10bn</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; €2bn</div>
            </div>
          </div>
          <div class="fc-metric-group">
            <div class="fc-metric-label">Employees (FTE)</div>
            <div class="fc-tiers">
              <div class="fc-tier fc-enterprise">Enterprise &nbsp;› &gt; 5,000</div>
              <div class="fc-tier fc-midmarket">Mid-Market &nbsp;› 1,000 – 5,000</div>
              <div class="fc-tier fc-scaleup">Scale-up &nbsp;› &lt; 1,000</div>
            </div>
          </div>
        </div>

      </div><!-- end fc-segments-grid -->

      <div class="fc-legend">
        <div class="fc-legend-item">
          <div class="fc-legend-dot" style="background:#d4edda; border:1px solid #155724;"></div>
          <span style="color:#155724; font-weight:600;">Enterprise</span>
        </div>
        <div class="fc-legend-item">
          <div class="fc-legend-dot" style="background:#fff3cd; border:1px solid #856404;"></div>
          <span style="color:#856404; font-weight:600;">Mid-Market</span>
        </div>
        <div class="fc-legend-item">
          <div class="fc-legend-dot" style="background:#f8d7da; border:1px solid #721c24;"></div>
          <span style="color:#721c24; font-weight:600;">Scale-up</span>
        </div>
        <div class="fc-legend-item">
          <div class="fc-legend-dot" style="background:#f3f3f3; border:1px solid #ccc;"></div>
          <span style="color:#706e6b; font-weight:600;">Not applicable</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🏦 Full-Service Banks — Special Classification Logic")
        st.markdown("""
    Full-Service Banks follow a distinct classification path:

    | Designation | How classified | Notes |
    |---|---|---|
    | **G-SIB** (Global Systemically Important Bank) | Automatically **Enterprise** | The G-SIB list is maintained in the code (`GSIB_LIST`). If the account name matches any G-SIB, it is immediately classified as Enterprise. |
    | **D-SIB** (Domestic Systemically Important Bank) | **Enterprise** after verification | D-SIBs are matched against a static list by country (`DSIB_LIST`). A warning is shown to verify with the local regulator before finalising. |
    | **Neither G-SIB nor D-SIB** | Falls back to **Banks** thresholds | AUM / Revenue / Employees thresholds for "Banks" are applied as normal. |

    > ⚠️ The D-SIB list is maintained in the application code and should be kept up to date. D-SIB designations can change — always verify with the relevant local regulator.
    """)

        st.markdown("---")
        st.markdown("### 📝 Notes")
        st.markdown("""
    - **AUM** (Assets Under Management) is primarily relevant for Banks and Asset Management firms. For Corporates and Fintechs, it is typically N/A.
    - **Revenue** figures should be in EUR billions (€bn). The LLM converts values from other currencies automatically.
    - **Employees** refers to full-time equivalent (FTE) headcount.
    - When both Revenue and Employees are known, **either one** can independently trigger Enterprise or Mid-Market — the highest tier wins.
    - The "Other / Default" thresholds apply to any Market Segment not explicitly listed above (e.g. Other, Precious Metals, Legal Services, etc.).
    """)

    with ref_tab2:
        st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Fenergo Segmentation</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="fen-section-title">Fenergo Segmentation Hierarchy</p>', unsafe_allow_html=True)
        st.markdown("""
    This tab shows the full **three-level segmentation hierarchy** used by Fenergo.
    Every account is classified across three levels:

    > **Market Segment** → **Business Segment** → **Detailed Business Segment**

    The Detailed Business Segment drives the **Customer Segment**, **Account Category**, and **Secondary Account Owner** assignments.
    """)

        # Build a grouped structure from SEGMENT_HIERARCHY
        _hier_dict = {}
        for (detailed, business, market) in SEGMENT_HIERARCHY:
            _hier_dict.setdefault(market, {}).setdefault(business, []).append(detailed)

        # Visual tree diagram
        _tree_html_parts = ['<div class="seg-tree-outer">']
        for _ms, _bs_dict in _hier_dict.items():
            _tree_html_parts.append(f'<div class="seg-market-section">')
            _tree_html_parts.append(f'<div class="seg-market-label">🏛️ {html_escape(_ms)}</div>')
            _tree_html_parts.append('<div class="seg-business-row">')
            for _bs, _ds_list in _bs_dict.items():
                _tree_html_parts.append('<div class="seg-business-card">')
                _tree_html_parts.append(f'<div class="seg-business-header">📂 {html_escape(_bs)}</div>')
                _tree_html_parts.append('<div class="seg-detailed-list">')
                for _ds in _ds_list:
                    _tree_html_parts.append(f'<div class="seg-detailed-item">• {html_escape(_ds)}</div>')
                _tree_html_parts.append('</div>')  # seg-detailed-list
                _tree_html_parts.append('</div>')  # seg-business-card
            _tree_html_parts.append('</div>')  # seg-business-row
            # Special note for Full-Service Banks (now a Business Segment under Banks)
            if _ms == "Banks" and "Full-Service Banks" in _bs_dict:
                _tree_html_parts.append(
                    '<div style="margin:8px 0 0 20px; padding:10px 14px; background:#f0f9f8; border-left:3px solid #21CFB2; border-radius:0 6px 6px 0; font-size:0.81rem; color:#002E33;">'
                    '<strong>⚠️ Special logic:</strong> Requires G-SIB or D-SIB designation for Enterprise. '
                    'Without it, standard Banks thresholds apply.'
                    '</div>'
                )
            _tree_html_parts.append('</div>')  # seg-market-section
        _tree_html_parts.append('</div>')  # seg-tree-outer
        st.markdown("".join(_tree_html_parts), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📝 Notes")
        st.markdown("""
    - The **Detailed Business Segment** is the most granular classification — it is what the LLM assigns based on the company's industry and activities.
    - The **Business Segment** is the mid-level grouping (e.g. "Asset & Wealth Mgmt." groups together Asset Management, Hedge Funds, Pension Funds, etc.).
    - The **Market Segment** is the top-level grouping that drives the Customer Segment thresholds (see the **Customer Segment Logic** tab).
    - These three levels are used together to determine the **Account Category** (via the account category matrix) and the **Secondary Account Owner**.
    - The G-SIB and D-SIB lists (`GSIB_LIST` and `DSIB_LIST`) are maintained in the application code and should be reviewed periodically to ensure accuracy.
    """)

    with ref_tab3:
        st.markdown('<div class="fen-breadcrumb">Account Intelligence &rsaquo; <span>Field Population Logic</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="fen-section-title">Field Population Logic</p>', unsafe_allow_html=True)
        st.markdown("""
    This tab provides a detailed breakdown of **how each enriched field is populated** — from simple user
    input through to multi-step AI web research and matrix lookups. It illustrates the depth and
    sophistication of the enrichment pipeline.
    """)

        st.info("""
    **Data source legend:**
    &nbsp; 👤 **User Input** — provided directly by the user
    &nbsp; 🌐 **Live Web Search** — AI searches the web in real time
    &nbsp; 🤖 **AI Reasoning** — AI derives/classifies from research
    &nbsp; 📊 **Matrix / Rules Engine** — deterministic lookup or rules
    &nbsp; 🔗 **Salesforce Cross-ref** — matched against your SF account list
    """)

        st.markdown("""
    <div class="fpl-section-header">📋 Core Account Identification</div>
    <div class="fpl-grid">

      <div class="fpl-card">
        <div class="fpl-field-name">🏢 Account Name</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-user">👤 User Input</span>
        </div>
        <div class="fpl-description">
          Provided directly by the user as the primary identifier for the account.
          Used as the starting point for all downstream research and matching.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">📜 Legal Name</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Research</span>
        </div>
        <div class="fpl-description">
          AI (OpenAI gpt-4.1 with live web search) researches the company's full registered legal name.
          Sources checked: company registries (Companies House, SEC EDGAR), regulatory filings,
          Bloomberg, official corporate websites and annual reports.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">🌍 Country</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-user">👤 User Input</span>
        </div>
        <div class="fpl-description">
          The country of the account's headquarters is selected by the user from a
          dropdown of 60+ countries. Used as the input to the Account Category matrix lookup
          and as a contextual signal for all AI research.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">🗺️ Region</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-matrix">📊 Country Mapping Table</span>
        </div>
        <div class="fpl-description">
          Auto-derived from Country using a 60+ country mapping table (EMEA / APAC / AMER).
          No user input required — the region is determined instantly from the selected country.
          Also drives the Secondary Account Owner assignment rules.
        </div>
      </div>

    </div>

    <div class="fpl-section-header">🏷️ Industry Classification</div>
    <div class="fpl-grid">

      <div class="fpl-card">
        <div class="fpl-field-name">🔍 Detailed Business Segment</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Classification</span>
        </div>
        <div class="fpl-description">
          AI classifies the company into exactly <strong>one of 38 Detailed Business Segments</strong>
          using live web research. The AI searches company websites, news, regulatory filings and
          financial databases to understand the company's core business activities and select the
          most appropriate segment.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">📂 Business Segment</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-matrix">📊 Hierarchy Lookup</span>
        </div>
        <div class="fpl-description">
          Auto-derived from the Detailed Business Segment via a 3-level segment hierarchy table.
          No AI inference required — the Business Segment is a deterministic roll-up from the
          Detailed Segment (e.g. "Asset Management" → "Asset &amp; Wealth Mgmt.").
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">🏛️ Market Segment</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-matrix">📊 Hierarchy Lookup</span>
        </div>
        <div class="fpl-description">
          Auto-derived from the Detailed Business Segment via the same 3-level hierarchy.
          The Market Segment is the top-level grouping (Banks / Asset Mgmt. / Corporates / Fintech /
          Full-Service Banks / Other) and drives the Customer Segment threshold logic.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">📝 Industry Classification Rationale</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-ai">🤖 AI Explanation</span>
        </div>
        <div class="fpl-description">
          AI generates a 1–2 sentence explanation of <em>why</em> the chosen Detailed Business Segment
          was selected. This provides transparency and allows users to verify or override the
          AI's classification reasoning.
        </div>
      </div>

    </div>

    <div class="fpl-section-header">💹 Customer Segmentation</div>
    <div class="fpl-grid">

      <div class="fpl-card">
        <div class="fpl-field-name">📊 Customer Segment</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-rules">📊 Rules Engine</span>
          <span class="fpl-source-badge badge-web">🌐 Live Web Data</span>
        </div>
        <div class="fpl-description">
          A rules engine evaluates AUM, Annual Revenue, and Employees against
          market-segment-specific thresholds. <strong>"Highest tier wins"</strong> — any single metric
          reaching Enterprise level classifies the account as Enterprise.
          G-SIB/D-SIB banks get special handling: they are automatically Enterprise
          without relying on financial metrics.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">🗂️ Account Category</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-matrix">📊 Excel Matrix Lookup</span>
        </div>
        <div class="fpl-description">
          A matrix lookup using <strong>Country × Customer Segment × Business Segment</strong>
          against an Excel-based matrix covering 60+ countries. Returns Category 1, 2, or 3,
          which drives commercial prioritisation. No AI involved — this is a pure
          deterministic lookup against the approved business rules matrix.
        </div>
      </div>

    </div>

    <div class="fpl-section-header">🔗 Corporate Hierarchy &amp; Ownership</div>
    <div class="fpl-grid">

      <div class="fpl-card">
        <div class="fpl-field-name">🏢 Ultimate Parent</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Research</span>
        </div>
        <div class="fpl-description">
          AI researches the full corporate ownership chain to identify the top-level holding entity.
          Sources: annual reports, SEC filings, Companies House, regulatory databases, Bloomberg.
          For publicly traded companies that are their own ultimate parent, the AI correctly
          returns the listed entity rather than null.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">🔗 Parent Account &amp; Reporting Group</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-sf">🔗 Salesforce Cross-ref</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Suggestion (fallback)</span>
        </div>
        <div class="fpl-description">
          Cross-referenced against the uploaded Salesforce account list using
          <strong>fuzzy matching (rapidfuzz)</strong> with normalisation of legal suffixes
          (Ltd, Inc, plc, GmbH, etc.). The Reporting Group is taken from the SF record whose
          Ultimate Parent matches the AI-identified ultimate parent. If no SF match is found,
          the AI suggests a friendly short name (e.g. "Barclays" for "Barclays Services Ltd").
        </div>
      </div>

    </div>

    <div class="fpl-section-header">👥 Account Ownership &amp; Financial Metrics</div>
    <div class="fpl-grid">

      <div class="fpl-card">
        <div class="fpl-field-name">👤 Secondary Account Owner</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-rules">📊 Rules Engine</span>
        </div>
        <div class="fpl-description">
          Determined by a rules engine using <strong>Region + Account Category</strong>.
          EMEA and UK/Ireland accounts are assigned to Elaine Zhang. APAC accounts to Vernis Tan.
          AMER accounts: Category 1 → Elaine Zhang; other categories rotate monthly
          between Joseph Cawley and Gabriel Simpatico (odd months vs even months).
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">💰 Annual Revenue</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Research</span>
        </div>
        <div class="fpl-description">
          AI web research prioritises the company's own investor relations pages and annual reports,
          then regulatory filings, then major financial data providers (Bloomberg, Reuters, S&amp;P Global).
          The most recent year available is always used (2024/2025 where possible).
          Source URL is captured and displayed for verification.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">👥 Employees</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Research</span>
        </div>
        <div class="fpl-description">
          Full-time equivalent (FTE) headcount sourced from company reports, LinkedIn,
          regulatory filings, or financial databases. AI cross-references multiple sources
          and uses the most authoritative, most recent figure. Source URL is captured.
        </div>
      </div>

      <div class="fpl-card">
        <div class="fpl-field-name">📈 AUM (Assets Under Management)</div>
        <div class="fpl-badges">
          <span class="fpl-source-badge badge-web">🌐 Live Web Search</span>
          <span class="fpl-source-badge badge-ai">🤖 AI Research</span>
        </div>
        <div class="fpl-description">
          Assets Under Management — relevant for banks, asset managers, hedge funds, pension funds,
          insurance companies and similar. For companies where AUM is not applicable (e.g. Fintechs,
          Corporates), the AI correctly returns "N/A". Source URL is captured for validation.
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)

        st.markdown("---")
        st.info("""
    **ℹ️ Data Freshness:** The system always attempts live web search via OpenAI gpt-4.1 (Responses API with web_search tool).
    If the live search fails, it retries up to 2 times before falling back to the model's training data.
    When training data is used, a prominent warning is shown and figures are annotated as potentially outdated.
    """)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="fen-footer">
  <div>
    <span class="fen-footer-brand">fenergo</span>
    &nbsp;Account Intelligence Platform
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Built for Fenergo Sales &amp; Account Management
  </div>
  <div style="display:flex; align-items:center; gap:12px;">
    <span>Powered by OpenAI gpt-4.1 + rapidfuzz</span>
    <span class="fen-footer-version">v{APP_VERSION}</span>
  </div>
</div>
""", unsafe_allow_html=True)

