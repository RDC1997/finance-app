from html import escape

import pandas as pd
import streamlit as st

PEOPLE = ["Ruben", "Gabi"]
MOVEMENT_TYPES = ["Salário", "Despesa"]
MONTHS = {
    "Todos": 0,
    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12,
}

CATEGORY_TONES = {
    "salário": "income",
    "salario": "income",
    "casa": "home",
    "compras": "shopping",
    "comida": "food",
    "contas": "bills",
    "transportes": "transport",
    "saúde": "health",
    "saude": "health",
    "lazer": "leisure",
    "outros": "other",
}

CSS = """
<style>
    :root {
        color-scheme: light;
        --bg: #f6f7fb;
        --bg-2: #eef2f7;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --surface-tint: #fff7f7;
        --text: #0f172a;
        --muted: #64748b;
        --line: #d8e0eb;
        --line-strong: #cbd5e1;
        --accent: #ef4444;
        --accent-soft: #fee2e2;
        --accent-muted: #fff1f2;
        --green: #059669;
        --green-deep: #047857;
        --red: #dc2626;
        --red-soft: #ef4444;
        --blue: #2563eb;
        --amber: #f59e0b;
        --shadow: 0 18px 45px rgba(15, 23, 42, .08);
        --shadow-soft: 0 10px 28px rgba(15, 23, 42, .06);
        --shadow-card: 0 12px 30px rgba(15, 23, 42, .075);
        --radius: 1.1rem;
        --radius-sm: .9rem;
    }

    *,
    *::before,
    *::after {
        color-scheme: light !important;
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    .stApp,
    .stMain,
    .main {
        background:
            radial-gradient(circle at 10% 0%, rgba(254, 226, 226, .75), transparent 30rem),
            linear-gradient(135deg, #f8fafc 0%, var(--bg) 48%, var(--bg-2) 100%) !important;
        color: var(--text) !important;
        color-scheme: light !important;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    [data-testid="stAppViewBlockContainer"],
    .block-container {
        padding-top: 1.75rem;
        padding-bottom: 2.25rem;
        max-width: 1180px;
    }

    header,
    [data-testid="stHeader"],
    [data-testid="stHeader"]::before,
    [data-testid="stHeader"]::after,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stHeader"] div,
    [data-testid="stHeader"] span,
    [data-testid="stHeader"] button {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border-color: transparent !important;
        color: var(--text) !important;
    }

    [data-testid="stHeader"] svg,
    [data-testid="stToolbar"] svg,
    [data-testid="stStatusWidget"] svg {
        color: var(--text) !important;
        fill: var(--text) !important;
        stroke: var(--text) !important;
    }

    [data-testid="stHeader"] *,
    [data-testid="stToolbar"] *,
    [data-testid="stStatusWidget"] * {
        background-color: transparent !important;
        color: var(--text) !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"],
    [data-testid="stSidebarHeader"] {
        background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.94)) !important;
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--line) !important;
        box-shadow: 12px 0 34px rgba(15, 23, 42, .04) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] hr {
        border-top-color: var(--line) !important;
    }

    h1, h2, h3, h4, h5, h6,
    label,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: var(--text) !important;
        letter-spacing: -.015em;
    }

    .hero { margin-bottom: 1.1rem; }

    .title {
        color: var(--text) !important;
        font-size: clamp(1.85rem, 5vw, 2.85rem);
        font-weight: 900;
        letter-spacing: -1.35px;
        line-height: 1.02;
    }

    .subtitle {
        color: var(--muted) !important;
        font-size: 1rem;
        line-height: 1.55;
        margin-top: .42rem;
    }

    .section-title {
        color: var(--text) !important;
        font-size: 1.22rem;
        font-weight: 850;
        margin: 1.05rem 0 .65rem;
        letter-spacing: -.35px;
    }

    .card,
    .clean-box,
    .movement-card,
    [data-testid="stMetric"],
    [data-testid="stExpander"],
    details {
        background: rgba(255, 255, 255, .95) !important;
        border: 1px solid rgba(216, 224, 235, .95) !important;
        border-radius: 1.25rem !important;
        box-shadow: var(--shadow-soft) !important;
        color: var(--text) !important;
    }

    .card {
        position: relative;
        overflow: hidden;
        padding: 1rem 1.05rem;
        margin-bottom: .55rem;
        min-height: 96px;
        transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }

    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 34px rgba(15, 23, 42, .10) !important;
    }

    .card::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 3px;
        background: #e2e8f0;
    }

    .card::after {
        content: "";
        position: absolute;
        right: -.9rem;
        top: -.9rem;
        width: 5.2rem;
        height: 5.2rem;
        border-radius: 999px;
        background: rgba(148, 163, 184, .10);
    }

    .card-head {
        align-items: center;
        display: flex;
        gap: .55rem;
        justify-content: space-between;
        position: relative;
        z-index: 1;
    }

    .card-icon {
        align-items: center;
        border-radius: .85rem;
        display: inline-flex;
        font-size: 1rem;
        height: 2.15rem;
        justify-content: center;
        width: 2.15rem;
    }

    .card-income {
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 55%, #dcfce7 100%) !important;
        border-color: rgba(5, 150, 105, .16) !important;
    }

    .card-income::before { background: linear-gradient(180deg, #10b981, var(--green-deep)); }

    .card-income::after { background: rgba(16, 185, 129, .12); }

    .card-income .card-icon { background: #d1fae5; color: var(--green-deep) !important; }

    .card-income .card-value { color: var(--green-deep) !important; }

    .card-expense {
        background: linear-gradient(135deg, #ffffff 0%, #fff7ed 45%, #fee2e2 100%) !important;
        border-color: rgba(220, 38, 38, .16) !important;
    }

    .card-expense::before { background: linear-gradient(180deg, #fb7185, var(--red)); }

    .card-expense::after { background: rgba(239, 68, 68, .12); }

    .card-expense .card-icon { background: #fee2e2; color: #b91c1c !important; }

    .card-expense .card-value { color: var(--red) !important; }

    .card-balance-positive {
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 52%, #e0f2fe 100%) !important;
        border-color: rgba(5, 150, 105, .16) !important;
        box-shadow: 0 14px 34px rgba(5, 150, 105, .08) !important;
    }

    .card-balance-positive::before { background: linear-gradient(180deg, #34d399, var(--green)); }

    .card-balance-positive::after { background: rgba(5, 150, 105, .10); }

    .card-balance-positive .card-icon { background: #d1fae5; color: var(--green-deep) !important; }

    .card-balance-positive .card-title { color: #047857 !important; }

    .card-balance-positive .card-value { color: var(--green) !important; }

    .card-balance-negative {
        background: linear-gradient(135deg, #ffffff 0%, #fff7ed 50%, #fee2e2 100%) !important;
        border-color: rgba(220, 38, 38, .16) !important;
        box-shadow: 0 14px 34px rgba(220, 38, 38, .08) !important;
    }

    .card-balance-negative::before { background: linear-gradient(180deg, #fb7185, var(--red)); }

    .card-balance-negative::after { background: rgba(220, 38, 38, .10); }

    .card-balance-negative .card-icon { background: #fee2e2; color: #b91c1c !important; }

    .card-balance-negative .card-title { color: #b91c1c !important; }

    .card-balance-negative .card-value { color: var(--red) !important; }

    .card-balance-neutral::before { background: #64748b; }

    .card-balance-neutral .card-icon { background: #f1f5f9; color: #334155 !important; }

    .card-balance-neutral .card-value { color: var(--text) !important; }

    .card-title {
        color: var(--muted) !important;
        font-size: .78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .06em;
    }

    .card-value,
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.52rem;
        font-weight: 900;
        letter-spacing: -.7px;
        line-height: 1.1;
        margin-top: .42rem;
        position: relative;
        z-index: 1;
    }

    .clean-box {
        padding: 1rem;
        margin-bottom: .85rem;
        box-shadow: var(--shadow) !important;
    }

    .form-caption {
        color: var(--muted) !important;
        font-size: .86rem;
        margin: -.2rem 0 .85rem;
    }

    .list-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.05rem 0 .65rem;
    }

    .list-header .section-title {
        margin: 0;
    }

    .list-count {
        color: var(--muted) !important;
        font-size: .82rem;
        font-weight: 800;
        background: #f1f5f9;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: .28rem .65rem;
        white-space: nowrap;
    }

    .movement-card {
        position: relative;
        padding: .72rem .82rem;
        margin-bottom: .55rem;
        transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }

    .movement-card:hover {
        transform: translateY(-1px);
        border-color: #cbd5e1 !important;
        box-shadow: 0 14px 34px rgba(15, 23, 42, .09) !important;
    }

    .movement-card.income-movement {
        border-left: 4px solid rgba(5, 150, 105, .55) !important;
    }

    .movement-card.expense-movement {
        border-left: 4px solid rgba(220, 38, 38, .50) !important;
    }

    .movement-top {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
    }

    .movement-heading {
        display: flex;
        align-items: center;
        gap: .55rem;
        flex-wrap: wrap;
    }

    .movement-title {
        color: var(--text) !important;
        font-weight: 900;
        font-size: .92rem;
        line-height: 1.2;
    }

    .movement-meta,
    .small-muted {
        color: var(--muted) !important;
        font-size: .78rem;
        font-weight: 700;
        margin-top: .18rem;
    }

    .movement-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 900;
        letter-spacing: .04em;
        padding: .24rem .52rem;
        text-transform: uppercase;
    }

    .movement-badge.income-badge {
        color: #047857 !important;
        background: #d1fae5 !important;
        border: 1px solid #a7f3d0;
    }

    .movement-badge.expense-badge {
        color: #b91c1c !important;
        background: #fee2e2 !important;
        border: 1px solid #fecaca;
    }

    .movement-date {
        color: #475569 !important;
        font-weight: 800;
    }

    .person-summary-card {
        border-left: 4px solid #94a3b8 !important;
    }

    .compact-panel-title {
        align-items: center;
        color: var(--text) !important;
        display: flex;
        font-size: .84rem;
        font-weight: 900;
        gap: .4rem;
        letter-spacing: .04em;
        margin: .1rem 0 .5rem;
        text-transform: uppercase;
    }

    .salary-title { color: var(--green-deep) !important; }

    .expense-title { color: #b91c1c !important; }

    .compact-movement-card,
    .empty-mini-card {
        background: rgba(255, 255, 255, .96) !important;
        border: 1px solid rgba(216, 224, 235, .90) !important;
        border-radius: .95rem !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .055) !important;
        color: var(--text) !important;
        margin-bottom: .45rem;
        padding: .62rem .7rem;
        transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
    }

    .compact-movement-card.compact-income {
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%) !important;
        border-color: rgba(5, 150, 105, .14) !important;
    }

    .compact-movement-card.compact-expense {
        background: linear-gradient(135deg, #ffffff 0%, #fff1f2 100%) !important;
        border-color: rgba(220, 38, 38, .14) !important;
    }

    .compact-movement-card:hover {
        transform: translateY(-1px);
        border-color: #cbd5e1 !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, .08) !important;
    }

    .compact-row {
        align-items: center;
        display: flex;
        gap: .7rem;
        justify-content: space-between;
    }

    .compact-main {
        min-width: 0;
    }

    .compact-title {
        color: var(--text) !important;
        font-size: .88rem;
        font-weight: 850;
        line-height: 1.2;
    }

    .compact-description {
        color: #475569 !important;
        font-size: .78rem;
        margin-top: .18rem;
    }

    .empty-mini-card {
        color: var(--muted) !important;
        font-size: .86rem;
        font-weight: 750;
    }

    .income,
    .expense {
        font-size: 1.05rem;
        font-weight: 900;
        white-space: nowrap;
    }

    .income { color: var(--green) !important; }

    .expense { color: var(--red) !important; }

    .neutral { color: var(--text) !important; }

    .pill {
        display: inline-block;
        padding: .3rem .65rem;
        border-radius: 999px;
        background: #f1f5f9 !important;
        color: #334155 !important;
        font-size: .75rem;
        font-weight: 800;
    }

    [data-testid="stHorizontalBlock"] { gap: 1rem; }

    [data-testid="stVerticalBlock"] { gap: .75rem; }

    [data-testid="stDataFrame"] {
        background: var(--surface) !important;
        border-radius: 1rem !important;
        border: 1px solid var(--line) !important;
        padding: .4rem !important;
        box-shadow: var(--shadow-soft) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        background: rgba(255,255,255,.70);
        border: 1px solid var(--line);
        border-radius: 1rem;
        padding: .35rem;
        box-shadow: var(--shadow-soft);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        min-height: 2.35rem;
        align-items: center;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted) !important;
    }

    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stTextArea"] [data-baseweb="textarea"],
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-baseweb="select"],
    [data-baseweb="select"] > div,
    [data-baseweb="input"],
    [data-baseweb="textarea"] {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        border-color: var(--line-strong) !important;
        border-radius: .9rem !important;
        box-shadow: none !important;
        color: var(--text) !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] div,
    [data-baseweb="select"] div {
        background-color: transparent !important;
        color: var(--text) !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] input,
    [data-baseweb="select"] span,
    [data-baseweb="select"] [class*="singleValue"],
    [data-baseweb="select"] [class*="placeholder"],
    input,
    textarea {
        background: transparent !important;
        color: var(--text) !important;
        caret-color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        border-color: transparent !important;
    }

    [data-baseweb="select"] svg,
    [data-baseweb="input"] svg,
    [data-testid="stDateInput"] svg,
    [data-testid="stNumberInput"] svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
    }

    [data-testid="stTextInput"] [data-baseweb="input"]:hover,
    [data-testid="stNumberInput"] [data-baseweb="input"]:hover,
    [data-testid="stDateInput"] [data-baseweb="input"]:hover,
    [data-testid="stTextArea"] [data-baseweb="textarea"]:hover,
    [data-baseweb="select"] > div:hover,
    [data-baseweb="input"]:hover,
    [data-baseweb="textarea"]:hover {
        background: var(--surface-soft) !important;
        border-color: #94a3b8 !important;
    }

    [data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
    [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
    [data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
    [data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="input"]:focus-within,
    [data-baseweb="textarea"]:focus-within {
        background: var(--surface) !important;
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, .14) !important;
    }

    [data-testid="stNumberInput"] button,
    [data-testid="stNumberInput"] [aria-label="Increment"],
    [data-testid="stNumberInput"] [aria-label="Decrement"],
    [data-testid="stDateInput"] button,
    [data-baseweb="input"] button {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stNumberInput"] button svg,
    [data-testid="stNumberInput"] button svg path,
    [data-testid="stDateInput"] button svg,
    [data-testid="stDateInput"] button svg path {
        fill: var(--muted) !important;
        color: var(--muted) !important;
        stroke: var(--muted) !important;
    }

    [data-testid="stNumberInput"] button:hover,
    [data-testid="stNumberInput"] [aria-label="Increment"]:hover,
    [data-testid="stNumberInput"] [aria-label="Decrement"]:hover,
    [data-testid="stDateInput"] button:hover,
    [data-baseweb="input"] button:hover {
        background: var(--accent-muted) !important;
        background-color: var(--accent-muted) !important;
        color: var(--accent) !important;
    }

    body [data-baseweb="popover"],
    body [data-baseweb="popover"] > div,
    body [data-baseweb="menu"],
    body [data-baseweb="menu"] ul,
    body [data-baseweb="select-dropdown"],
    body [role="listbox"],
    body [role="menu"] {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 1rem !important;
        box-shadow: 0 22px 55px rgba(15, 23, 42, .16) !important;
        color-scheme: light !important;
    }

    body [data-baseweb="popover"] *,
    body [data-baseweb="menu"] *,
    body [data-baseweb="select-dropdown"] *,
    body [role="listbox"] *,
    body [role="menu"] * {
        background-color: var(--surface) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        text-shadow: none !important;
    }

    body [role="option"],
    body [role="menuitem"],
    body [data-baseweb="menu"] li,
    body [role="listbox"] li,
    body [role="listbox"] div[role="option"] {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
        border-radius: .75rem !important;
        margin: .12rem .25rem !important;
        color-scheme: light !important;
    }

    body [role="option"] *,
    body [role="menuitem"] *,
    body [data-baseweb="menu"] li *,
    body [role="listbox"] li * {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }

    body [role="option"]:hover,
    body [role="option"][aria-selected="true"],
    body [role="option"][aria-current="true"],
    body [role="option"][data-highlighted="true"],
    body [role="menuitem"]:hover,
    body [role="menuitem"][aria-selected="true"],
    body [data-baseweb="menu"] li:hover,
    body [role="listbox"] li:hover {
        background: var(--accent-muted) !important;
        background-color: var(--accent-muted) !important;
        color: var(--text) !important;
    }

    body [role="option"]:hover *,
    body [role="option"][aria-selected="true"] *,
    body [role="option"][aria-current="true"] *,
    body [role="option"][data-highlighted="true"] *,
    body [role="menuitem"]:hover *,
    body [data-baseweb="menu"] li:hover *,
    body [role="listbox"] li:hover * {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }

    body [data-baseweb="calendar"],
    body [data-baseweb="calendar"] > div,
    body [data-baseweb="calendar"] table,
    body [data-baseweb="calendar"] th,
    body [data-baseweb="calendar"] td {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
        color-scheme: light !important;
    }

    body [data-baseweb="calendar"] button,
    body [data-baseweb="calendar"] div,
    body [data-baseweb="calendar"] span {
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }

    body [data-baseweb="calendar"] button:hover,
    body [data-baseweb="calendar"] [aria-selected="true"] {
        background: var(--accent-soft) !important;
        background-color: var(--accent-soft) !important;
        color: var(--text) !important;
    }

    body [data-baseweb="calendar"] [aria-disabled="true"],
    body [data-baseweb="calendar"] [aria-disabled="true"] * {
        background: var(--surface-soft) !important;
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"],
    button[kind="secondary"],
    button[kind="primary"] {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--line-strong) !important;
        border-radius: .9rem !important;
        font-weight: 800 !important;
        min-height: 2.65rem !important;
        padding: .58rem .95rem !important;
        box-shadow: 0 8px 18px rgba(15, 23, 42, .05) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[kind="secondary"]:hover,
    button[kind="primary"]:hover {
        background: var(--accent-muted) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }

    button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        border-color: #dc2626 !important;
        color: #ffffff !important;
        box-shadow: 0 12px 26px rgba(220, 38, 38, .22) !important;
    }

    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
        color: #ffffff !important;
        border-color: #b91c1c !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0f766e, #059669) !important;
        border-color: #047857 !important;
        color: #ffffff !important;
        box-shadow: 0 12px 26px rgba(5, 150, 105, .20) !important;
    }

    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #047857, #065f46) !important;
        border-color: #065f46 !important;
        color: #ffffff !important;
    }

    .stButton > button *,
    .stDownloadButton > button *,
    button[data-testid^="baseButton"] * {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
    }

    [role="radiogroup"] label {
        background: transparent !important;
        border-radius: .85rem !important;
        padding: .35rem .45rem !important;
    }

    [role="radiogroup"] label:hover {
        background: #f1f5f9 !important;
    }

    [role="radiogroup"] label * {
        color: var(--text) !important;
    }

    [data-testid="stAlert"] {
        background: var(--surface) !important;
        border-radius: 1rem !important;
        border-color: var(--line) !important;
        color: var(--text) !important;
    }

    [data-testid="stExpander"] summary,
    details summary,
    details div,
    details p,
    details span {
        color: var(--text) !important;
    }

    hr {
        border: none;
        border-top: 1px solid var(--line);
        margin: 1.75rem 0;
    }

    .category-grid-card {
        align-items: center;
        background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(248,250,252,.96)) !important;
        border: 1px solid rgba(216, 224, 235, .92) !important;
        border-radius: 1rem !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .055) !important;
        display: flex;
        gap: .55rem;
        margin-bottom: .35rem;
        min-height: 3.1rem;
        padding: .68rem .78rem;
    }

    .category-dot {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        border-radius: 999px;
        flex: 0 0 .58rem;
        height: .58rem;
        width: .58rem;
    }

    .category-name {
        color: var(--text) !important;
        font-size: .9rem;
        font-weight: 850;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .category-protected {
        color: var(--muted) !important;
        font-size: .72rem;
        font-weight: 800;
        margin: -.15rem 0 .65rem;
        text-align: center;
    }



    .sidebar-brand {
        background: transparent !important;
        border-bottom: 1px solid var(--line);
        color: var(--text) !important;
        margin: .25rem 0 .9rem;
        padding: .25rem 0 .85rem;
    }

    .sidebar-brand-title {
        color: var(--text) !important;
        font-size: 1.24rem;
        font-weight: 950;
        letter-spacing: -.045em;
        line-height: 1;
    }

    .sidebar-brand-subtitle {
        color: var(--muted) !important;
        font-size: .8rem;
        font-weight: 750;
        margin-top: .38rem;
        line-height: 1.35;
    }

    .sidebar-section-label {
        color: #475569 !important;
        font-size: .72rem;
        font-weight: 900;
        letter-spacing: .08em;
        margin: .75rem 0 .35rem;
        text-transform: uppercase;
    }

    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextInput {
        margin-bottom: .28rem;
    }

    .category-icon {
        align-items: center;
        background: #fff1f2;
        border: 1px solid #ffe4e6;
        border-radius: .78rem;
        display: inline-flex;
        flex: 0 0 2rem;
        height: 2rem;
        justify-content: center;
        width: 2rem;
    }

    .category-grid-card {
        min-height: 2.8rem;
        padding: .52rem .6rem;
    }

    .category-protected {
        background: #f1f5f9;
        border: 1px solid var(--line);
        border-radius: 999px;
        display: inline-flex;
        margin: -.08rem 0 .55rem;
        padding: .16rem .5rem;
    }



    .form-caption {
        color: var(--muted) !important;
        font-size: .86rem;
        font-weight: 750;
        margin: -.25rem 0 .8rem;
    }

    .selected-movement-card,
    .danger-zone-note {
        background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(248,250,252,.96)) !important;
        border: 1px solid rgba(216, 224, 235, .95) !important;
        border-radius: 1.05rem !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, .055) !important;
        margin: .2rem 0 .75rem;
        padding: .82rem .9rem;
    }

    .selected-movement-eyebrow,
    .edit-block-label {
        color: var(--muted) !important;
        font-size: .72rem;
        font-weight: 900;
        letter-spacing: .07em;
        text-transform: uppercase;
    }

    .selected-movement-title {
        align-items: center;
        color: var(--text) !important;
        display: flex;
        flex-wrap: wrap;
        font-size: .98rem;
        font-weight: 900;
        gap: .45rem;
        margin-top: .18rem;
    }

    .selected-movement-meta {
        color: var(--muted) !important;
        font-size: .82rem;
        font-weight: 750;
        margin-top: .16rem;
    }

    .edit-block-label {
        margin: .15rem 0 .25rem;
    }

    .danger-zone-note {
        background: linear-gradient(135deg, #fff 0%, #fff7ed 100%) !important;
        border-color: rgba(251, 146, 60, .22) !important;
        color: #9a3412 !important;
        font-size: .84rem;
        font-weight: 750;
        margin-top: .55rem;
    }

    .goal-stats {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin-top: .55rem;
    }

    .goal-stat-pill {
        background: #f8fafc !important;
        border: 1px solid var(--line);
        border-radius: 999px;
        color: var(--text) !important;
        font-size: .76rem;
        font-weight: 850;
        padding: .28rem .58rem;
    }

    .goal-card {
        background: rgba(255, 255, 255, .96) !important;
        border: 1px solid rgba(216, 224, 235, .95) !important;
        border-radius: 1.2rem !important;
        box-shadow: var(--shadow-soft) !important;
        margin-bottom: .65rem;
        padding: .95rem;
    }

    .goal-title-row,
    .export-summary-grid {
        align-items: center;
        display: flex;
        gap: .8rem;
        justify-content: space-between;
    }

    .goal-title { color: var(--text) !important; font-size: 1rem; font-weight: 900; }

    .goal-amount { color: var(--green-deep) !important; font-size: .96rem; font-weight: 950; white-space: nowrap; }

    .goal-missing { color: var(--muted) !important; font-size: .84rem; font-weight: 800; margin-top: .25rem; }

    .goal-progress-track {
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, .10);
    }

    .goal-progress-fill {
        align-items: center;
        color: #ffffff !important;
        display: flex;
        font-size: .68rem;
        font-weight: 950;
        justify-content: center;
        min-width: 1.8rem;
        text-shadow: 0 1px 1px rgba(0,0,0,.18);
    }

    .export-summary-card {
        background:
            radial-gradient(circle at 100% 0%, rgba(239,68,68,.12), transparent 9rem),
            rgba(255,255,255,.96) !important;
        border: 1px solid rgba(216, 224, 235, .95) !important;
        border-radius: 1.2rem;
        box-shadow: var(--shadow-soft);
        margin-bottom: .9rem;
        padding: 1rem;
    }

    .export-summary-item { min-width: 0; }

    .export-summary-label {
        color: var(--muted) !important;
        font-size: .72rem;
        font-weight: 900;
        letter-spacing: .06em;
        text-transform: uppercase;
    }

    .export-summary-value {
        color: var(--text) !important;
        font-size: 1.08rem;
        font-weight: 950;
        margin-top: .2rem;
    }

    .goal-progress-wrap {
        margin: .65rem 0 .85rem;
    }

    .goal-progress-meta {
        align-items: center;
        display: flex;
        justify-content: space-between;
        margin-bottom: .42rem;
    }

    .goal-progress-label {
        color: var(--muted) !important;
        font-size: .78rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: .05em;
    }

    .goal-progress-percent {
        color: var(--text) !important;
        font-size: .86rem;
        font-weight: 900;
    }

    .goal-progress-track {
        background: #e2e8f0;
        border-radius: 999px;
        height: .82rem;
        overflow: hidden;
        position: relative;
    }

    .goal-progress-fill {
        border-radius: inherit;
        height: 100%;
        transition: width .45s ease, background .25s ease;
    }



    .category-tone-income { background: linear-gradient(135deg, #34d399, #059669) !important; }
    .category-tone-home { background: linear-gradient(135deg, #60a5fa, #2563eb) !important; }
    .category-tone-shopping { background: linear-gradient(135deg, #a78bfa, #7c3aed) !important; }
    .category-tone-food { background: linear-gradient(135deg, #fb923c, #ea580c) !important; }
    .category-tone-bills { background: linear-gradient(135deg, #facc15, #d97706) !important; }
    .category-tone-transport { background: linear-gradient(135deg, #38bdf8, #0284c7) !important; }
    .category-tone-health { background: linear-gradient(135deg, #f472b6, #db2777) !important; }
    .category-tone-leisure { background: linear-gradient(135deg, #818cf8, #4f46e5) !important; }
    .category-tone-other { background: linear-gradient(135deg, #94a3b8, #475569) !important; }

    .category-dot {
        border: 2px solid rgba(255, 255, 255, .95);
        border-radius: 999px;
        box-shadow: 0 0 0 1px rgba(15, 23, 42, .08), 0 4px 10px rgba(15, 23, 42, .08);
        display: inline-flex;
        flex: 0 0 .68rem;
        height: .68rem;
        width: .68rem;
    }

    .category-dot-large {
        flex-basis: .82rem;
        height: .82rem;
        width: .82rem;
    }

    .category-grid-card {
        position: relative;
        justify-content: flex-start;
    }

    .category-grid-card::before {
        background: linear-gradient(180deg, rgba(239, 68, 68, .55), rgba(15, 118, 110, .45));
        border-radius: 999px;
        content: "";
        height: 58%;
        left: 0;
        position: absolute;
        top: 21%;
        width: 3px;
    }

    .selected-movement-card {
        border-left: 4px solid rgba(15, 118, 110, .35) !important;
    }

    .edit-block-label {
        background: #f8fafc;
        border: 1px solid var(--line);
        border-radius: 999px;
        display: inline-flex;
        padding: .22rem .58rem;
    }

    .goal-card {
        border-left: 4px solid rgba(15, 118, 110, .40) !important;
    }

    .goal-card + .goal-progress-wrap {
        background: rgba(255,255,255,.96);
        border: 1px solid rgba(216,224,235,.9);
        border-radius: 1rem;
        box-shadow: 0 8px 18px rgba(15,23,42,.045);
        padding: .75rem .85rem .85rem;
    }

    @media (max-width: 760px) {
        [data-testid="stAppViewBlockContainer"],
        .block-container {
            padding-left: .85rem;
            padding-right: .85rem;
            padding-top: 1.05rem;
            max-width: 100%;
        }

        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
            gap: .55rem;
        }

        [data-testid="stHorizontalBlock"] > div {
            min-width: min(100%, 18rem) !important;
        }

        .title { font-size: 1.75rem; }

        .subtitle { font-size: .92rem; }

        .card {
            min-height: auto;
            padding: 1rem;
        }

        .card-value {
            font-size: 1.45rem;
        }

        .clean-box {
            padding: 1rem;
        }

        .movement-top,
        .goal-title-row,
        .export-summary-grid {
            align-items: flex-start;
            flex-direction: column;
            gap: .45rem;
        }

        .movement-top .income,
        .movement-top .expense,
        .goal-amount {
            width: 100%;
        }

        .income,
        .expense {
            font-size: .95rem;
        }

        .list-header {
            align-items: flex-start;
            flex-direction: column;
            gap: .45rem;
        }

        .category-grid-card { margin-bottom: .2rem; }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 2.85rem !important;
        }
    }

    @media (min-width: 761px) and (max-width: 1100px) {
        [data-testid="stAppViewBlockContainer"],
        .block-container {
            max-width: 980px;
        }
    }
</style>
"""


def apply_style() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def category_label(category: str) -> str:
    return str(category or "Outros").strip() or "Outros"


def category_tone_class(category: str) -> str:
    tone = CATEGORY_TONES.get(str(category).strip().lower(), "other")
    return f"category-tone-{tone}"


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Rubi &amp; Gabi</div>
            <div class="sidebar-brand-subtitle">Finanças do casal, simples e rápidas.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(value) -> str:
    return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def card(title: str, value: str, tone: str = "neutral") -> None:
    tone_class = f" card-{tone}"
    icon_map = {
        "income": "+",
        "expense": "-",
        "balance-positive": "OK",
        "balance-negative": "!",
        "balance-neutral": "=",
        "neutral": "=",
    }
    icon = icon_map.get(tone, "•")

    st.markdown(
        f"""
        <div class="card{tone_class}">
            <div class="card-head">
                <div class="card-title">{escape(title)}</div>
                <div class="card-icon">{escape(icon)}</div>
            </div>
            <div class="card-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str = "") -> None:
    subtitle_html = f'<div class="subtitle">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="hero"><div class="title">{escape(title)}</div>{subtitle_html}</div>', unsafe_allow_html=True)


def section_title(title: str) -> None:
    st.markdown(f'<div class="section-title">{escape(title)}</div>', unsafe_allow_html=True)


def list_header(title: str, count: int | None = None) -> None:
    count_html = f'<div class="list-count">{count} movimentos</div>' if count is not None else ""

    st.markdown(
        f'<div class="list-header"><div class="section-title">{escape(title)}</div>{count_html}</div>',
        unsafe_allow_html=True,
    )


def movement_card(row: pd.Series) -> None:
    is_income = str(row["type"]).lower() == "salário"
    value_class = "income" if is_income else "expense"
    movement_class = "income-movement" if is_income else "expense-movement"
    badge_class = "income-badge" if is_income else "expense-badge"
    signal = "+" if is_income else "-"
    description = str(row.get("description") or "").strip()
    category_raw = str(row["category"])
    category_text = category_label(category_raw)
    category_tone = category_tone_class(category_raw)
    desc_text = f" · {escape(description)}" if description else ""

    st.markdown(
        f"""
        <div class="movement-card {movement_class}">
            <div class="movement-top">
                <div>
                    <div class="movement-heading">
                        <span class="category-dot {category_tone}" aria-hidden="true"></span>
                        <div class="movement-title">{escape(category_text)}</div>
                        <span class="movement-badge {badge_class}">{escape(str(row['type']))}</span>
                    </div>
                    <div class="movement-meta"><span class="movement-date">{escape(str(row['date']))}</span> · {escape(str(row['person']))}{desc_text}</div>
                </div>
                <div class="{value_class}">{signal}{money(row['value'])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def filter_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    filtered = dataframe.copy()

    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="sidebar-section-label">Filtros rápidos</div>', unsafe_allow_html=True)

    selected_person = st.sidebar.selectbox("Pessoa", ["Todos"] + PEOPLE)

    if selected_person != "Todos":
        filtered = filtered[filtered["person"] == selected_person]

    years = sorted(filtered["year"].dropna().astype(int).unique().tolist(), reverse=True)

    if years:
        selected_year = st.sidebar.selectbox("Ano", ["Todos"] + years)

        if selected_year != "Todos":
            filtered = filtered[filtered["year"] == int(selected_year)]

    selected_month = st.sidebar.selectbox("Mês", list(MONTHS.keys()))

    if MONTHS[selected_month] != 0:
        filtered = filtered[filtered["month"] == MONTHS[selected_month]]

    search = st.sidebar.text_input("Pesquisar")

    if search.strip():
        term = search.strip().lower()
        searchable = filtered[["description", "category", "type", "person"]].fillna("").agg(" ".join, axis=1).str.lower()
        filtered = filtered[searchable.str.contains(term, regex=False)]

    return filtered


def financial_summary(dataframe: pd.DataFrame) -> tuple[float, float, float]:
    if dataframe.empty:
        return 0, 0, 0

    grouped = dataframe.groupby("type_normalized", dropna=False)["value"].sum()
    income = float(grouped.get("salário", 0))
    expense = float(grouped.get("despesa", 0))

    return income, expense, income - expense


def balance_tone(balance: float) -> str:
    if balance > 0:
        return "balance-positive"
    if balance < 0:
        return "balance-negative"
    return "balance-neutral"


def balance_class(balance: float) -> str:
    if balance > 0:
        return "income"
    if balance < 0:
        return "expense"
    return "neutral"


def summary_cards(dataframe: pd.DataFrame, balance_label: str = "Saldo") -> None:
    income, expense, balance = financial_summary(dataframe)

    c1, c2, c3 = st.columns(3)

    with c1:
        card("Salário", money(income), "income")

    with c2:
        card("Despesas", money(expense), "expense")

    with c3:
        card(balance_label, money(balance), balance_tone(balance))


def transaction_label(row: pd.Series) -> str:
    desc = str(row.get("description") or "").strip()
    extra = f" | {desc}" if desc else ""

    return f"{row['date']} | {row['person']} | {row['type']} | {row['category']} | {money(row['value'])}{extra}"
