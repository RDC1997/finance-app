from html import escape

import pandas as pd
import streamlit as st

PEOPLE = ["Ruben", "Gabi"]
MOVEMENT_TYPES = ["Salário", "Subsídio de Alimentação", "Despesa"]
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
        --bg: #f4f6f9;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --surface-muted: #eef2f7;
        --text: #0f172a;
        --muted: #64748b;
        --line: #d8e0ea;
        --line-strong: #cbd5e1;
        --green: #059669;
        --green-soft: #ecfdf5;
        --red: #dc2626;
        --red-soft: #fff1f2;
        --blue: #2563eb;
        --blue-soft: #eff6ff;
        --amber: #d97706;
        --shadow: 0 10px 26px rgba(15, 23, 42, .06);
        --shadow-soft: 0 4px 12px rgba(15, 23, 42, .045);
        --radius: 1rem;
        --radius-sm: .8rem;
    }

    *, *::before, *::after { box-sizing: border-box; color-scheme: light !important; }

    html, body, [data-testid="stAppViewContainer"], .stApp, .stMain, .main {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"], .block-container {
        max-width: 1180px !important;
        padding-top: 2.25rem !important;
        padding-bottom: 2.8rem !important;
    }

    [data-testid="stSidebar"], [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"], [data-testid="stSidebarHeader"] {
        background: #fbfdff !important;
        color: var(--text) !important;
    }
    [data-testid="stSidebar"] { border-right: 1px solid var(--line) !important; box-shadow: 8px 0 24px rgba(15, 23, 42, .035) !important; }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stSidebar"] [role="radiogroup"] { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label { border: 1px solid transparent !important; border-radius: .9rem !important; margin: .18rem 0 !important; min-height: 2.65rem !important; padding: .2rem .55rem !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--blue-soft) !important; border-color: #bfdbfe !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #1d4ed8 !important; font-weight: 900 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label p { color: #334155 !important; font-weight: 800 !important; }

    h1, h2, h3, h4, h5, h6, label, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p { color: var(--text) !important; }

    .hero { margin: 0 0 1.35rem; }
    .title { color: var(--text) !important; font-size: clamp(1.85rem, 4.4vw, 2.65rem); font-weight: 950; letter-spacing: -.045em; line-height: 1.04; }
    .subtitle { color: var(--muted) !important; font-size: 1rem; line-height: 1.55; margin-top: .45rem; max-width: 780px; }
    .section-title { color: var(--text) !important; font-size: 1.18rem; font-weight: 900; letter-spacing: -.025em; margin: 1.55rem 0 .72rem; }
    .sidebar-brand { background: var(--surface); border: 1px solid var(--line); border-radius: 1.15rem; box-shadow: var(--shadow-soft); margin: .35rem 0 1rem; padding: 1rem; }
    .sidebar-brand-title { color: var(--text) !important; font-size: 1.35rem !important; font-weight: 950 !important; letter-spacing: -.04em; }
    .sidebar-brand-subtitle { color: var(--muted) !important; font-size: .84rem !important; font-weight: 700 !important; margin-top: .15rem; }
    .sidebar-section-label { color: #334155 !important; font-size: .75rem; font-weight: 950; letter-spacing: .05em; margin-bottom: .45rem; text-transform: uppercase; }

    [data-testid="stHorizontalBlock"] { gap: 1.25rem !important; }
    [data-testid="stVerticalBlock"] { gap: .85rem !important; }

    .card, .clean-box, .movement-card, .compact-finance-card, .quick-summary-card, .goal-card, .goal-progress-wrap, .export-period-card, .selected-category-panel, .category-list-panel, .export-empty-state, [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"], details {
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        color: var(--text) !important;
    }
    .card { min-height: 6rem; padding: 1rem; margin-bottom: .65rem; }
    .card-head, .movement-top, .compact-card-row, .goal-title-row { align-items: center; display: flex; gap: .85rem; justify-content: space-between; }
    .card-title, .family-label, .hero-micro { color: var(--muted) !important; font-size: .78rem; font-weight: 850; letter-spacing: .045em; text-transform: uppercase; }
    .card-value, .family-value { color: var(--text) !important; font-size: clamp(1.28rem, 3vw, 1.75rem); font-weight: 950; line-height: 1.12; margin-top: .35rem; font-variant-numeric: tabular-nums; }
    .family-note { color: var(--muted) !important; font-size: .78rem !important; font-weight: 700; margin-top: .35rem; }
    .compact-finance-card { min-height: 6.6rem !important; padding: 1rem !important; display: flex; flex-direction: column; justify-content: center; }
    .income-card { background: var(--green-soft) !important; border-color: #bbf7d0 !important; }
    .expense-card { background: var(--red-soft) !important; border-color: #fecaca !important; }
    .available-card, .mint-card { background: var(--blue-soft) !important; border-color: #bfdbfe !important; }
    .income { color: var(--green) !important; font-weight: 950; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .expense { color: var(--red) !important; font-weight: 950; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .neutral { color: var(--text) !important; font-weight: 950; }

    .finance-hero-card { align-items: center; background: var(--surface) !important; border: 1px solid var(--line) !important; border-radius: 1.2rem !important; box-shadow: var(--shadow) !important; display: flex; gap: 1.1rem; justify-content: space-between; margin: .15rem 0 1.2rem; padding: 1.2rem 1.25rem; }
    .finance-hero-card.positive-card { border-left: 5px solid var(--green) !important; }
    .finance-hero-card.negative-card { border-left: 5px solid var(--red) !important; }
    .hero-title { color: var(--text) !important; font-size: clamp(1.12rem, 4vw, 1.55rem); font-weight: 950; letter-spacing: -.03em; margin-top: .18rem; }
    .hero-subtitle, .hero-amount-subtitle { color: #475569 !important; font-weight: 700; }
    .hero-amount-block { text-align: right; }
    .hero-amount { color: var(--blue) !important; font-size: clamp(1.55rem, 7vw, 2.4rem); font-weight: 950; white-space: nowrap; }
    .positive-card .hero-amount { color: var(--green) !important; }
    .negative-card .hero-amount { color: var(--red) !important; }

    .quick-summary-card, .export-period-card, .selected-category-panel, .category-list-panel, .export-empty-state { padding: .9rem 1rem; }
    .quick-summary-row { align-items: center; border-bottom: 1px solid #e6edf5; display: flex; gap: .9rem; justify-content: space-between; padding: .72rem 0; }
    .quick-summary-row:last-child { border-bottom: 0; }
    .quick-summary-row span { color: #334155 !important; font-weight: 800; }
    .quick-summary-row strong { color: var(--text) !important; font-weight: 950; text-align: right; }

    .movement-card { padding: .68rem .78rem; margin-bottom: .5rem; box-shadow: var(--shadow-soft) !important; }
    .income-movement { border-left: 4px solid var(--green) !important; }
    .expense-movement { border-left: 4px solid var(--red) !important; }
    .movement-title { color: var(--text) !important; font-size: .92rem !important; font-weight: 900; line-height: 1.2; }
    .movement-meta, .small-muted { color: var(--muted) !important; font-size: .78rem !important; font-weight: 700; margin-top: .2rem; }
    .compact-card-main { min-width: 0; }
    .compact-card-value { font-size: 1rem !important; }
    .form-shell-title { color: var(--text) !important; font-size: 1.05rem; font-weight: 900; margin: 1.55rem 0 .72rem; }
    .clean-box { padding: 1rem; }
    .empty-mini-card { background: var(--surface) !important; border: 1px dashed var(--line-strong) !important; border-radius: var(--radius-sm) !important; color: var(--muted) !important; font-size: .9rem; font-weight: 750; padding: .85rem 1rem; }

    .goal-card { margin: .8rem 0 .35rem; padding: 1rem !important; }
    .goal-title { color: var(--text) !important; font-size: 1.05rem; font-weight: 950; }
    .goal-bottom-row { color: var(--muted) !important; font-size: .84rem; font-weight: 750; margin-top: .18rem; }
    .goal-amount { color: var(--blue) !important; font-size: 1.35rem; font-weight: 950; }
    .goal-stats-grid { display: grid; gap: .75rem; grid-template-columns: repeat(5, minmax(0, 1fr)); margin-top: 1rem; }
    .goal-stats-grid div { background: var(--surface-soft); border: 1px solid #e2e8f0; border-radius: .85rem; padding: .66rem .7rem; }
    .goal-stats-grid span { color: var(--muted) !important; display: block; font-size: .72rem; font-weight: 850; margin-bottom: .2rem; }
    .goal-stats-grid strong { color: var(--text) !important; font-size: .92rem; font-weight: 950; }
    .goal-progress-wrap { box-shadow: none !important; margin-top: 1rem; padding: .75rem; }
    .goal-progress-meta { align-items: center; display: flex; justify-content: space-between; margin-bottom: .5rem; }
    .goal-progress-label, .goal-progress-percent { color: var(--muted) !important; font-size: .78rem; font-weight: 900; }
    .goal-progress-track { background: #e2e8f0; border-radius: 999px; height: .62rem; overflow: hidden; }
    .goal-progress-fill { border-radius: inherit; height: 100%; }
    .goal-action-row .stButton > button, .goal-action-row button { min-height: 2.35rem !important; }

    .category-list-panel { margin-bottom: 1rem; }
    .category-list-row { align-items: center; border-bottom: 1px solid #e6edf5; display: flex; gap: .75rem; justify-content: space-between; padding: .62rem 0; }
    .category-list-row:last-child { border-bottom: 0; }
    .category-name { color: var(--text) !important; font-size: .92rem; font-weight: 900; }
    .category-muted { color: var(--muted) !important; font-size: .78rem; font-weight: 750; margin-top: .15rem; }
    .category-lock { background: var(--surface-muted); border: 1px solid var(--line); border-radius: 999px; color: #334155 !important; font-size: .72rem; font-weight: 850; padding: .22rem .55rem; white-space: nowrap; }
    .protected-category .category-lock { background: #f1f5f9; color: var(--muted) !important; }
    .selected-movement-eyebrow { color: var(--muted) !important; font-size: .75rem; font-weight: 900; letter-spacing: .05em; text-transform: uppercase; }
    .selected-movement-title { color: var(--text) !important; font-size: 1.18rem; font-weight: 950; margin-top: .15rem; }

    .export-empty-state { align-items: center; border-style: dashed !important; display: flex; gap: 1rem; justify-content: space-between; margin-top: .75rem; }
    .export-empty-icon { align-items: center; background: var(--blue-soft); border: 1px solid #bfdbfe; border-radius: .95rem; color: var(--blue) !important; display: flex; font-size: 1.5rem; font-weight: 950; height: 3rem; justify-content: center; width: 3rem; }
    .export-empty-title { color: var(--text) !important; font-size: 1.05rem; font-weight: 950; }
    .export-empty-text { color: var(--muted) !important; font-size: .9rem; font-weight: 700; margin-top: .18rem; }

    [data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stNumberInput"] [data-baseweb="input"], [data-testid="stDateInput"] [data-baseweb="input"], [data-testid="stTextArea"] [data-baseweb="textarea"], [data-testid="stSelectbox"] [data-baseweb="select"], [data-baseweb="select"], [data-baseweb="input"], [data-baseweb="textarea"] { background: var(--surface) !important; border-color: var(--line-strong) !important; border-radius: .85rem !important; box-shadow: none !important; color: var(--text) !important; }
    input, textarea, [data-baseweb="select"] input, [data-baseweb="select"] span { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background: var(--surface) !important; color: var(--text) !important; }
    [role="option"], [role="option"] * { color: var(--text) !important; }
    [role="option"]:hover, [aria-selected="true"] { background: var(--blue-soft) !important; }

    .stButton > button, .stDownloadButton > button, button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"], button[kind="secondary"], button[kind="primary"] { background: var(--surface) !important; border: 1px solid var(--line-strong) !important; border-radius: .82rem !important; box-shadow: var(--shadow-soft) !important; color: var(--text) !important; font-weight: 850 !important; min-height: 2.35rem !important; padding: .45rem .82rem !important; }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--blue) !important; color: var(--blue) !important; }
    button[data-testid="baseButton-primary"], button[kind="primary"] { background: var(--blue) !important; border-color: #1d4ed8 !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    .stDownloadButton > button { background: var(--green) !important; border-color: #047857 !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div:has(.danger-action-marker) + div button { background: var(--red) !important; border-color: #b91c1c !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div:has(.success-action-marker) + div button { background: var(--green) !important; border-color: #047857 !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div:has(.info-action-marker) + div button { background: var(--blue-soft) !important; border-color: #93c5fd !important; color: #1d4ed8 !important; -webkit-text-fill-color: #1d4ed8 !important; }
    .stButton > button *, .stDownloadButton > button *, button[data-testid^="baseButton"] * { color: inherit !important; -webkit-text-fill-color: inherit !important; }

    [data-testid="stAlert"], [data-testid="stDataFrame"] { background: var(--surface) !important; border: 1px solid var(--line) !important; border-radius: 1rem !important; color: var(--text) !important; box-shadow: var(--shadow-soft) !important; }

    @media (max-width: 760px) {
        [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"], .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.65rem !important; }
        [data-testid="stHorizontalBlock"] { gap: 1rem !important; }
        .finance-hero-card, .export-empty-state { align-items: flex-start; flex-direction: column; }
        .hero-amount-block { text-align: left; }
        .hero-amount { white-space: normal; }
        .quick-summary-row { align-items: flex-start; flex-direction: column; gap: .22rem; }
        .quick-summary-row strong { text-align: left; }
        .goal-stats-grid { grid-template-columns: 1fr 1fr; }
        .category-list-row { align-items: flex-start; flex-direction: column; }
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
    signal = "+" if is_income else "-"
    description = str(row.get("description") or "").strip()
    category_raw = str(row["category"])
    category_text = category_label(category_raw)
    category_tone = category_tone_class(category_raw)
    icon_map = {"Comida": "🍽️", "Casa": "🏠", "Compras": "🛍️", "Contas": "🧾", "Transportes": "🚗", "Saúde": "💊", "Lazer": "🎯", "Outros": "✨", "Salário": "💼", "Subsídio Alimentação": "🥗"}
    movement_icon = icon_map.get(category_text, "•")
    movement_type = "Entrada" if is_income else "Despesa"
    desc_text = f" · {escape(description)}" if description else ""

    st.markdown(
        f"""
        <div class="movement-card {movement_class}">
            <div class="movement-top">
                <div>
                    <div class="movement-heading">
                        <span class="category-dot {category_tone}" aria-hidden="true"></span>
                        <div class="movement-title">{escape(movement_icon)} {escape(category_text)} · <span class="small-muted">{escape(movement_type)}</span></div>
                        
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
