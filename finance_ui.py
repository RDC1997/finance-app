from html import escape

import pandas as pd
import plotly.express as px
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
        --red: #dc2626;
        --blue: #2563eb;
        --shadow: 0 18px 45px rgba(15, 23, 42, .08);
        --shadow-soft: 0 10px 28px rgba(15, 23, 42, .06);
        --radius: 1.1rem;
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
        padding-top: 2.35rem;
        padding-bottom: 3rem;
        max-width: 1340px;
    }

    /* Streamlit header / top toolbar: remove dark native band completely. */
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

    /* Sidebar and navigation. */
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

    /* Typography: keep native labels readable without forcing chart internals. */
    h1, h2, h3, h4, h5, h6,
    label,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: var(--text) !important;
        letter-spacing: -.015em;
    }

    .hero { margin-bottom: 1.6rem; }
    .title {
        color: var(--text) !important;
        font-size: clamp(2rem, 4vw, 3.15rem);
        font-weight: 900;
        letter-spacing: -1.35px;
        line-height: 1.02;
    }
    .subtitle {
        color: var(--muted) !important;
        font-size: 1rem;
        line-height: 1.55;
        margin-top: .55rem;
    }
    .section-title {
        color: var(--text) !important;
        font-size: 1.22rem;
        font-weight: 850;
        margin: 1.45rem 0 .85rem;
        letter-spacing: -.35px;
    }

    /* Cards, dashboard blocks and expanders. */
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
        padding: 1.15rem 1.2rem;
        margin-bottom: .85rem;
        min-height: 116px;
    }
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
        font-size: 1.72rem;
        font-weight: 900;
        letter-spacing: -.7px;
        margin-top: .45rem;
    }
    .clean-box {
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow) !important;
    }
    .movement-card {
        padding: .95rem 1.05rem;
        margin-bottom: .75rem;
    }
    .movement-top {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
    }
    .movement-title { color: var(--text) !important; font-weight: 850; font-size: .98rem; }
    .movement-meta, .small-muted { color: var(--muted) !important; font-size: .84rem; margin-top: .25rem; }
    .income, .expense { font-size: 1rem; font-weight: 900; white-space: nowrap; }
    .income { color: var(--green) !important; }
    .expense { color: var(--red) !important; }
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

    /* Inputs: target Streamlit wrappers and BaseWeb internals explicitly. */
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

    /* Dropdowns, select options, Streamlit menus and BaseWeb popovers. */
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

    /* Date picker calendar internals. */
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

    /* Buttons and download buttons. */
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
        padding: .58rem 1rem !important;
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

    .stButton > button *,
    .stDownloadButton > button *,
    button[data-testid^="baseButton"] * {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
    }

    /* Radio, expanders, alerts and misc native containers. */
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
</style>
"""


def apply_style() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def money(value) -> str:
    return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{escape(title)}</div>
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


def movement_card(row: pd.Series) -> None:
    is_income = str(row["type"]).lower() == "salário"
    value_class = "income" if is_income else "expense"
    signal = "+" if is_income else "-"
    description = str(row.get("description") or "").strip()
    desc_text = f" · {escape(description)}" if description else ""

    st.markdown(
        f"""
        <div class="movement-card">
            <div class="movement-top">
                <div>
                    <div class="movement-title">{escape(str(row['category']))}</div>
                    <div class="movement-meta">{escape(str(row['person']))} · {escape(str(row['type']))} · {escape(str(row['date']))}{desc_text}</div>
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
    st.sidebar.subheader("Filtros")

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


def summary_cards(dataframe: pd.DataFrame, balance_label: str = "Saldo") -> None:
    income, expense, balance = financial_summary(dataframe)
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Receitas", money(income))
    with c2:
        card("Despesas", money(expense))
    with c3:
        card(balance_label, money(balance))


def transaction_label(row: pd.Series) -> str:
    desc = str(row.get("description") or "").strip()
    extra = f" | {desc}" if desc else ""
    return f"{row['date']} | {row['person']} | {row['type']} | {row['category']} | {money(row['value'])}{extra}"


def expense_bar_chart(expenses: pd.DataFrame):
    summary = expenses.groupby("category", as_index=False)["value"].sum().sort_values("value", ascending=True).tail(5)
    fig = px.bar(summary, x="value", y="category", orientation="h", text=summary["value"].apply(money))
    fig.update_traces(textposition="outside", marker_color="#ef4444", hovertemplate="%{y}<br>%{text}<extra></extra>")
    fig.update_layout(
        height=280,
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
    )
    return fig
