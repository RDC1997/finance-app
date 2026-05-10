import os
from datetime import date
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text


# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Rubi & Gabi Finance",
    layout="wide",
    page_icon="💰"
)


# =========================
# STYLE
# =========================
st.markdown("""
<style>
    :root {
        --bg: #f6f7fb;
        --panel: #ffffff;
        --text: #111827;
        --muted: #6b7280;
        --line: #e5e7eb;
        --accent: #ef4444;
        --green: #16a34a;
        --red: #dc2626;
        --blue: #2563eb;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] * {
        color: #111827 !important;
    }

    .block-container {
        padding-top: 42px;
        padding-bottom: 48px;
        max-width: 1380px;
    }

    h1, h2, h3, label, p, span, div {
        color: #111827;
    }

    .title {
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -0.8px;
        margin-bottom: 4px;
    }

    .subtitle {
        color: var(--muted);
        font-size: 15px;
        margin-bottom: 28px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 800;
        margin-top: 14px;
        margin-bottom: 14px;
    }

    .card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .card-title {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 8px;
    }

    .card-value {
        color: var(--text);
        font-size: 27px;
        font-weight: 850;
        letter-spacing: -0.6px;
    }

    .clean-box {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }

    .movement-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    .movement-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
    }

    .movement-title {
        font-weight: 800;
        font-size: 15px;
    }

    .movement-meta {
        color: var(--muted);
        font-size: 13px;
        margin-top: 4px;
    }

    .income {
        color: var(--green);
        font-size: 17px;
        font-weight: 850;
    }

    .expense {
        color: var(--red);
        font-size: 17px;
        font-weight: 850;
    }

    .pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #f3f4f6;
        color: #374151;
        font-size: 12px;
        font-weight: 700;
    }

    .small-muted {
        color: var(--muted);
        font-size: 13px;
    }

    div[data-testid="stDataFrame"] {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid var(--line);
        padding: 6px;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 16px;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #d1d5db;
        background: #ffffff;
        color: #111827;
        font-weight: 700;
        padding: 9px 16px;
    }

    .stButton > button:hover {
        border-color: #ef4444;
        color: #ef4444;
    }

    div[data-baseweb="select"] > div,
    input,
    textarea {
        background-color: #ffffff !important;
        color: #111827 !important;
        border-radius: 12px !important;
        border-color: #d1d5db !important;
    }

    div[data-baseweb="select"] span {
        color: #111827 !important;
    }

    hr {
        border: none;
        border-top: 1px solid var(--line);
        margin: 28px 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# DATABASE
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = st.secrets["DATABASE_URL"]

DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


engine = get_engine()


# =========================
# CREATE TABLES
# =========================
with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        person TEXT,
        type TEXT,
        category TEXT,
        description TEXT,
        value FLOAT,
        date TEXT
    )
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS goals (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        target_amount FLOAT,
        current_amount FLOAT
    )
    """))


# =========================
# HELPERS
# =========================
def clear_cache():
    load_transactions.clear()
    load_categories.clear()
    load_goals.clear()


def money(value):
    return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def card(title, value):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def clean_title(title, subtitle=""):
    st.markdown(f'<div class="title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def movement_card(row):
    value_class = "income" if str(row["type"]).lower() == "salário" else "expense"
    signal = "+" if str(row["type"]).lower() == "salário" else "-"
    desc = str(row["description"] or "").strip()
    desc_text = f" · {desc}" if desc else ""

    st.markdown(f"""
    <div class="movement-card">
        <div class="movement-top">
            <div>
                <div class="movement-title">{row["category"]}</div>
                <div class="movement-meta">{row["person"]} · {row["type"]} · {row["date"]}{desc_text}</div>
            </div>
            <div class="{value_class}">{signal}{money(row["value"])}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=20)
def load_transactions():
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM transactions ORDER BY id DESC", conn)

    if df.empty:
        return pd.DataFrame(columns=[
            "id", "person", "type", "category", "description",
            "value", "date", "date_dt", "year", "month"
        ])

    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date_dt"].dt.year
    df["month"] = df["date_dt"].dt.month

    return df


@st.cache_data(ttl=60)
def load_categories():
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM categories ORDER BY name", conn)

    if df.empty:
        defaults = [
            "Casa", "Comida", "Transportes", "Lazer",
            "Saúde", "Compras", "Contas", "Outros"
        ]

        with engine.begin() as conn:
            for item in defaults:
                conn.execute(text("""
                    INSERT INTO categories (name)
                    VALUES (:name)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": item})

        return load_categories()

    return df


@st.cache_data(ttl=20)
def load_goals():
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM goals ORDER BY id DESC", conn)

    if df.empty:
        return pd.DataFrame(columns=[
            "id", "name", "description", "target_amount", "current_amount"
        ])

    df["target_amount"] = pd.to_numeric(df["target_amount"], errors="coerce").fillna(0)
    df["current_amount"] = pd.to_numeric(df["current_amount"], errors="coerce").fillna(0)

    return df


def export_excel(dataframe):
    output = BytesIO()
    export_df = dataframe.copy()

    for col in ["date_dt", "year", "month"]:
        if col in export_df.columns:
            export_df = export_df.drop(columns=[col])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Movimentos")

    return output.getvalue()


def filter_data(dataframe):
    if dataframe.empty:
        return dataframe

    filtered = dataframe.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros")

    selected_person = st.sidebar.selectbox("Pessoa", ["Todos", "Ruben", "Gabi"])

    if selected_person != "Todos":
        filtered = filtered[filtered["person"] == selected_person]

    years = sorted(filtered["year"].dropna().astype(int).unique().tolist(), reverse=True)

    if years:
        selected_year = st.sidebar.selectbox("Ano", ["Todos"] + years)

        if selected_year != "Todos":
            filtered = filtered[filtered["year"] == int(selected_year)]

    months = {
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
        "Dezembro": 12
    }

    selected_month = st.sidebar.selectbox("Mês", list(months.keys()))

    if months[selected_month] != 0:
        filtered = filtered[filtered["month"] == months[selected_month]]

    search = st.sidebar.text_input("Pesquisar")

    if search.strip():
        term = search.strip().lower()
        filtered = filtered[
            filtered["description"].fillna("").str.lower().str.contains(term)
            | filtered["category"].fillna("").str.lower().str.contains(term)
            | filtered["type"].fillna("").str.lower().str.contains(term)
            | filtered["person"].fillna("").str.lower().str.contains(term)
        ]

    return filtered


def transaction_label(row):
    desc = str(row["description"] or "").strip()
    extra = f" | {desc}" if desc else ""
    return f"{row['date']} | {row['person']} | {row['type']} | {row['category']} | {money(row['value'])}{extra}"


# =========================
# LOAD DATA
# =========================
df = load_transactions()
categories_df = load_categories()
goals_df = load_goals()

categories = categories_df["name"].tolist()

if "Outros" not in categories:
    categories.append("Outros")


# =========================
# SIDEBAR
# =========================
st.sidebar.title("💰 Rubi & Gabi")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Ruben", "Gabi", "Casal", "Metas", "Categorias", "Exportar"]
)

filtered_df = filter_data(df)


# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    clean_title("Dashboard", "Visão geral simples das vossas contas.")

    receitas = filtered_df[filtered_df["type"].str.lower() == "salário"]["value"].sum() if not filtered_df.empty else 0
    despesas = filtered_df[filtered_df["type"].str.lower() == "despesa"]["value"].sum() if not filtered_df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    with c1:
        card("Receitas", money(receitas))
    with c2:
        card("Despesas", money(despesas))
    with c3:
        card("Saldo disponível", money(saldo))

    if filtered_df.empty:
        st.info("Não existem movimentos para os filtros escolhidos.")
    else:
        despesas_df = filtered_df[filtered_df["type"].str.lower() == "despesa"]

        st.markdown('<div class="section-title">Resumo rápido</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1.1, 0.9])

        with col1:
            st.markdown('<div class="clean-box">', unsafe_allow_html=True)
            st.markdown("#### Para onde foi o dinheiro")

            if despesas_df.empty:
                st.info("Sem despesas.")
            else:
                resumo = despesas_df.groupby("category", as_index=False)["value"].sum()
                resumo = resumo.sort_values("value", ascending=True).tail(5)

                fig = px.bar(
                    resumo,
                    x="value",
                    y="category",
                    orientation="h",
                    text=resumo["value"].apply(money)
                )

                fig.update_traces(
                    textposition="outside",
                    marker_color="#ef4444"
                )

                fig.update_layout(
                    height=260,
                    margin=dict(l=8, r=8, t=8, b=8),
                    xaxis_title="",
                    yaxis_title="",
                    showlegend=False,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(color="#111827")
                )

                st.plotly_chart(fig, use_container_width=True)

            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="clean-box">', unsafe_allow_html=True)
            st.markdown("#### Por pessoa")

            for person in ["Ruben", "Gabi"]:
                person_df = filtered_df[filtered_df["person"] == person]
                person_receitas = person_df[person_df["type"].str.lower() == "salário"]["value"].sum()
                person_despesas = person_df[person_df["type"].str.lower() == "despesa"]["value"].sum()
                person_saldo = person_receitas - person_despesas

                st.markdown(f"""
                <div class="movement-card">
                    <div class="movement-top">
                        <div>
                            <div class="movement-title">{person}</div>
                            <div class="movement-meta">Receitas {money(person_receitas)} · Despesas {money(person_despesas)}</div>
                        </div>
                        <div class="income">{money(person_saldo)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Últimos movimentos</div>', unsafe_allow_html=True)

        for _, row in filtered_df.head(6).iterrows():
            movement_card(row)


# =========================
# PESSOAS / CASAL
# =========================
elif page in ["Ruben", "Gabi", "Casal"]:
    clean_title(page, "Adicionar, consultar, editar e remover movimentos.")

    person_options = ["Ruben", "Gabi"] if page == "Casal" else [page]

    st.markdown('<div class="section-title">Adicionar movimento</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            person = st.selectbox("Pessoa", person_options, key=f"add_person_{page}")

        with col2:
            movement_type = st.selectbox("Tipo", ["Salário", "Despesa"], key=f"add_type_{page}")

        category = "Salário"
        description = ""

        if movement_type == "Despesa":
            category = st.selectbox("Categoria", categories, key=f"add_category_{page}")

            if category == "Outros":
                description = st.text_input("Descrição obrigatória", key=f"add_description_{page}")

        col3, col4 = st.columns(2)

        with col3:
            value = st.number_input("Valor", min_value=0.0, step=1.0, key=f"add_value_{page}")

        with col4:
            movement_date = st.date_input("Data", value=date.today(), max_value=date.today(), key=f"add_date_{page}")

        if st.button("Adicionar movimento", key=f"add_button_{page}"):
            if value <= 0:
                st.error("O valor tem de ser superior a zero.")
            elif movement_type == "Despesa" and category == "Outros" and not description.strip():
                st.error("Na categoria Outros, a descrição é obrigatória.")
            else:
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO transactions
                    (person, type, category, description, value, date)
                    VALUES
                    (:person, :type, :category, :description, :value, :date)
                    """), {
                        "person": person,
                        "type": movement_type,
                        "category": category,
                        "description": description.strip(),
                        "value": value,
                        "date": str(movement_date)
                    })

                clear_cache()
                st.success("Movimento adicionado.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    page_df = filtered_df[filtered_df["person"].isin(person_options)] if not filtered_df.empty else pd.DataFrame()

    receitas = page_df[page_df["type"].str.lower() == "salário"]["value"].sum() if not page_df.empty else 0
    despesas = page_df[page_df["type"].str.lower() == "despesa"]["value"].sum() if not page_df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    with c1:
        card("Receitas", money(receitas))
    with c2:
        card("Despesas", money(despesas))
    with c3:
        card("Saldo", money(saldo))

    st.markdown('<div class="section-title">Movimentos recentes</div>', unsafe_allow_html=True)

    if page_df.empty:
        st.info("Sem movimentos para mostrar.")
    else:
        for _, row in page_df.head(8).iterrows():
            movement_card(row)

        with st.expander("Ver tabela completa"):
            table_df = page_df[["person", "type", "category", "description", "value", "date"]].copy()
            table_df.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True
            )

        st.markdown('<div class="section-title">Editar ou remover movimento</div>', unsafe_allow_html=True)

        options = {
            transaction_label(row): int(row["id"])
            for _, row in page_df.iterrows()
        }

        selected_label = st.selectbox(
            "Escolhe o movimento",
            list(options.keys()),
            key=f"select_transaction_{page}"
        )

        selected_id = options[selected_label]
        selected_row = page_df[page_df["id"] == selected_id].iloc[0]

        st.markdown('<div class="clean-box">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            edit_person = st.selectbox(
                "Pessoa",
                ["Ruben", "Gabi"],
                index=["Ruben", "Gabi"].index(selected_row["person"]) if selected_row["person"] in ["Ruben", "Gabi"] else 0,
                key=f"edit_person_{page}_{selected_id}"
            )

        with col2:
            edit_type = st.selectbox(
                "Tipo",
                ["Salário", "Despesa"],
                index=["Salário", "Despesa"].index(selected_row["type"]) if selected_row["type"] in ["Salário", "Despesa"] else 0,
                key=f"edit_type_{page}_{selected_id}"
            )

        edit_category = "Salário"
        edit_description = ""

        if edit_type == "Despesa":
            edit_category = st.selectbox(
                "Categoria",
                categories,
                index=categories.index(selected_row["category"]) if selected_row["category"] in categories else 0,
                key=f"edit_category_{page}_{selected_id}"
            )

            if edit_category == "Outros":
                edit_description = st.text_input(
                    "Descrição obrigatória",
                    value=str(selected_row["description"] or ""),
                    key=f"edit_description_{page}_{selected_id}"
                )

        col3, col4 = st.columns(2)

        with col3:
            edit_value = st.number_input(
                "Valor",
                min_value=0.0,
                step=1.0,
                value=float(selected_row["value"]),
                key=f"edit_value_{page}_{selected_id}"
            )

        with col4:
            edit_date = st.date_input(
                "Data",
                value=pd.to_datetime(selected_row["date"]).date(),
                max_value=date.today(),
                key=f"edit_date_{page}_{selected_id}"
            )

        col_save, col_delete = st.columns([1, 1])

        with col_save:
            if st.button("Guardar alterações", key=f"save_transaction_{page}_{selected_id}"):
                if edit_value <= 0:
                    st.error("O valor tem de ser superior a zero.")
                elif edit_type == "Despesa" and edit_category == "Outros" and not edit_description.strip():
                    st.error("Na categoria Outros, a descrição é obrigatória.")
                else:
                    with engine.begin() as conn:
                        conn.execute(text("""
                        UPDATE transactions
                        SET person = :person,
                            type = :type,
                            category = :category,
                            description = :description,
                            value = :value,
                            date = :date
                        WHERE id = :id
                        """), {
                            "id": selected_id,
                            "person": edit_person,
                            "type": edit_type,
                            "category": edit_category,
                            "description": edit_description.strip(),
                            "value": edit_value,
                            "date": str(edit_date)
                        })

                    clear_cache()
                    st.success("Movimento atualizado.")
                    st.rerun()

        with col_delete:
            if st.button("Remover movimento", key=f"delete_transaction_{page}_{selected_id}"):
                with engine.begin() as conn:
                    conn.execute(
                        text("DELETE FROM transactions WHERE id = :id"),
                        {"id": selected_id}
                    )

                clear_cache()
                st.success("Movimento removido.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# =========================
# METAS
# =========================
elif page == "Metas":
    clean_title("Metas", "Acompanhar objetivos de forma simples.")

    st.markdown('<div class="section-title">Criar meta</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)

        name = st.text_input("Nome da meta")
        description = st.text_input("Descrição")
        target = st.number_input("Objetivo", min_value=0.0, step=10.0)
        current = st.number_input("Valor atual", min_value=0.0, step=10.0)

        if st.button("Criar meta"):
            if not name.strip():
                st.error("O nome é obrigatório.")
            elif target <= 0:
                st.error("O objetivo tem de ser superior a zero.")
            else:
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO goals
                    (name, description, target_amount, current_amount)
                    VALUES
                    (:name, :description, :target_amount, :current_amount)
                    """), {
                        "name": name.strip(),
                        "description": description.strip(),
                        "target_amount": target,
                        "current_amount": current
                    })

                clear_cache()
                st.success("Meta criada.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Metas existentes</div>', unsafe_allow_html=True)

    if goals_df.empty:
        st.info("Ainda não existem metas.")
    else:
        for _, goal in goals_df.iterrows():
            target = float(goal["target_amount"])
            current = float(goal["current_amount"])
            progress = min(current / target, 1) if target > 0 else 0

            st.markdown(f"""
            <div class="clean-box">
                <div class="movement-top">
                    <div>
                        <div class="movement-title">{goal['name']}</div>
                        <div class="movement-meta">{goal['description']}</div>
                    </div>
                    <div class="income">{money(current)} / {money(target)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.progress(progress)

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                amount = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=5.0,
                    key=f"goal_amount_{goal['id']}"
                )

            with col2:
                if st.button("Adicionar", key=f"add_goal_{goal['id']}"):
                    if amount > 0:
                        with engine.begin() as conn:
                            conn.execute(text("""
                            UPDATE goals
                            SET current_amount = current_amount + :amount
                            WHERE id = :id
                            """), {
                                "amount": amount,
                                "id": int(goal["id"])
                            })

                        clear_cache()
                        st.success("Valor adicionado.")
                        st.rerun()

            with col3:
                if st.button("Retirar", key=f"remove_goal_value_{goal['id']}"):
                    if amount > 0:
                        new_value = max(current - amount, 0)

                        with engine.begin() as conn:
                            conn.execute(text("""
                            UPDATE goals
                            SET current_amount = :value
                            WHERE id = :id
                            """), {
                                "value": new_value,
                                "id": int(goal["id"])
                            })

                        clear_cache()
                        st.success("Valor retirado.")
                        st.rerun()

            with col4:
                if st.button("Remover", key=f"delete_goal_{goal['id']}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("DELETE FROM goals WHERE id = :id"),
                            {"id": int(goal["id"])}
                        )

                    clear_cache()
                    st.success("Meta removida.")
                    st.rerun()


# =========================
# CATEGORIAS
# =========================
elif page == "Categorias":
    clean_title("Categorias", "Gerir categorias usadas nas despesas.")

    st.markdown('<div class="clean-box">', unsafe_allow_html=True)

    new_category = st.text_input("Nova categoria")

    if st.button("Adicionar categoria"):
        if not new_category.strip():
            st.error("Escreve o nome da categoria.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO categories (name) VALUES (:name)"),
                        {"name": new_category.strip()}
                    )

                clear_cache()
                st.success("Categoria adicionada.")
                st.rerun()

            except Exception:
                st.error("Essa categoria já existe.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Categorias existentes</div>', unsafe_allow_html=True)

    for _, category in categories_df.iterrows():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"""
            <div class="movement-card">
                <div class="movement-title">{category["name"]}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if category["name"].lower() == "outros":
                st.caption("Protegida")
            else:
                if st.button("Remover", key=f"remove_cat_{category['id']}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("DELETE FROM categories WHERE id = :id"),
                            {"id": int(category["id"])}
                        )

                    clear_cache()
                    st.success("Categoria removida.")
                    st.rerun()


# =========================
# EXPORTAR
# =========================
elif page == "Exportar":
    clean_title("Exportar", "Descarregar movimentos em Excel.")

    if filtered_df.empty:
        st.info("Não existem dados para exportar.")
    else:
        export_columns = ["person", "type", "category", "description", "value", "date"]

        export_view = filtered_df[export_columns].copy()
        export_view.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]

        st.dataframe(
            export_view,
            use_container_width=True,
            hide_index=True
        )

        excel_file = export_excel(filtered_df[["id"] + export_columns])

        st.download_button(
            label="Descarregar Excel",
            data=excel_file,
            file_name="movimentos_financeiros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )