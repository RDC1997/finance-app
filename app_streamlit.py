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
    .title {
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 18px;
    }

    .card {
        padding: 16px;
        border-radius: 14px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
    }

    .card-title {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 5px;
    }

    .card-value {
        color: #0f172a;
        font-size: 24px;
        font-weight: 800;
    }

    .simple-box {
        padding: 14px;
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .small-text {
        color: #64748b;
        font-size: 13px;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# DATABASE
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = st.secrets["DATABASE_URL"]

DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg://"
)


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


@st.cache_data(ttl=20)
def load_transactions():
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM transactions ORDER BY id DESC", conn)

    if df.empty:
        return pd.DataFrame(columns=[
            "id", "person", "type", "category", "description", "value", "date",
            "date_dt", "year", "month"
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
            "Casa",
            "Comida",
            "Transportes",
            "Lazer",
            "Saúde",
            "Compras",
            "Contas",
            "Outros"
        ]

        with engine.begin() as conn:
            for item in defaults:
                conn.execute(
                    text("""
                    INSERT INTO categories (name)
                    VALUES (:name)
                    ON CONFLICT (name) DO NOTHING
                    """),
                    {"name": item}
                )

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
    return f"{row['id']} | {row['date']} | {row['person']} | {row['type']} | {row['category']} | {money(row['value'])}"


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
    [
        "Dashboard",
        "Ruben",
        "Gabi",
        "Casal",
        "Metas",
        "Categorias",
        "Exportar"
    ]
)

filtered_df = filter_data(df)


# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    st.markdown('<div class="title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Resumo simples e direto das vossas finanças.</div>', unsafe_allow_html=True)

    receitas = filtered_df[filtered_df["type"].str.lower() == "salário"]["value"].sum() if not filtered_df.empty else 0
    despesas = filtered_df[filtered_df["type"].str.lower() == "despesa"]["value"].sum() if not filtered_df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    with c1:
        card("Receitas", money(receitas))

    with c2:
        card("Despesas", money(despesas))

    with c3:
        card("Saldo", money(saldo))

    st.markdown("---")

    if filtered_df.empty:
        st.info("Não existem movimentos para os filtros escolhidos.")
    else:
        despesas_df = filtered_df[filtered_df["type"].str.lower() == "despesa"]

        c1, c2 = st.columns([1, 1])

        with c1:
            st.subheader("Principais despesas")

            if despesas_df.empty:
                st.info("Sem despesas.")
            else:
                resumo = despesas_df.groupby("category", as_index=False)["value"].sum()
                resumo = resumo.sort_values("value", ascending=False).head(5)

                fig = px.bar(
                    resumo,
                    x="value",
                    y="category",
                    orientation="h",
                    text="value"
                )

                fig.update_traces(
                    texttemplate="%{text:.2f}€",
                    textposition="outside"
                )

                fig.update_layout(
                    height=260,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title="",
                    yaxis_title="",
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("Resumo por pessoa")

            resumo_pessoa = filtered_df.groupby("person", as_index=False)["value"].sum()

            if resumo_pessoa.empty:
                st.info("Sem dados.")
            else:
                for _, row in resumo_pessoa.iterrows():
                    st.markdown(f"""
                    <div class="simple-box">
                        <strong>{row['person']}</strong><br>
                        <span class="small-text">Total movimentado</span><br>
                        <strong>{money(row['value'])}</strong>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("Últimos movimentos")

        st.dataframe(
            filtered_df[["person", "type", "category", "description", "value", "date"]].head(10),
            use_container_width=True,
            hide_index=True
        )


# =========================
# PESSOAS / CASAL
# =========================
elif page in ["Ruben", "Gabi", "Casal"]:
    st.markdown(f'<div class="title">{page}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Adicionar, editar e remover movimentos.</div>', unsafe_allow_html=True)

    person_options = ["Ruben", "Gabi"] if page == "Casal" else [page]

    st.subheader("Adicionar movimento")

    with st.form(f"add_form_{page}"):
        col1, col2 = st.columns(2)

        with col1:
            person = st.selectbox("Pessoa", person_options)

        with col2:
            movement_type = st.selectbox("Tipo", ["Salário", "Despesa"])

        category = "Salário"
        description = ""

        if movement_type == "Despesa":
            category = st.selectbox("Categoria", categories)

            if category == "Outros":
                description = st.text_input("Descrição obrigatória")

        col3, col4 = st.columns(2)

        with col3:
            value = st.number_input("Valor", min_value=0.0, step=1.0)

        with col4:
            movement_date = st.date_input("Data", value=date.today(), max_value=date.today())

        submit = st.form_submit_button("Adicionar")

        if submit:
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

    st.markdown("---")

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

    st.markdown("---")

    st.subheader("Movimentos")

    if page_df.empty:
        st.info("Sem movimentos para mostrar.")
    else:
        st.dataframe(
            page_df[["id", "person", "type", "category", "description", "value", "date"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("Editar ou remover")

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

        with st.form(f"edit_form_{page}"):
            col1, col2 = st.columns(2)

            with col1:
                edit_person = st.selectbox(
                    "Pessoa",
                    ["Ruben", "Gabi"],
                    index=["Ruben", "Gabi"].index(selected_row["person"]) if selected_row["person"] in ["Ruben", "Gabi"] else 0
                )

            with col2:
                edit_type = st.selectbox(
                    "Tipo",
                    ["Salário", "Despesa"],
                    index=["Salário", "Despesa"].index(selected_row["type"]) if selected_row["type"] in ["Salário", "Despesa"] else 0
                )

            edit_category = "Salário"
            edit_description = ""

            if edit_type == "Despesa":
                edit_category = st.selectbox(
                    "Categoria",
                    categories,
                    index=categories.index(selected_row["category"]) if selected_row["category"] in categories else 0
                )

                if edit_category == "Outros":
                    edit_description = st.text_input(
                        "Descrição obrigatória",
                        value=str(selected_row["description"] or "")
                    )

            col3, col4 = st.columns(2)

            with col3:
                edit_value = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=1.0,
                    value=float(selected_row["value"])
                )

            with col4:
                edit_date = st.date_input(
                    "Data",
                    value=pd.to_datetime(selected_row["date"]).date(),
                    max_value=date.today()
                )

            update = st.form_submit_button("Guardar alterações")

            if update:
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

        if st.button("Remover movimento selecionado", key=f"delete_transaction_{page}"):
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM transactions WHERE id = :id"),
                    {"id": selected_id}
                )

            clear_cache()
            st.success("Movimento removido.")
            st.rerun()


# =========================
# METAS
# =========================
elif page == "Metas":
    st.markdown('<div class="title">Metas</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Acompanhar objetivos de forma simples.</div>', unsafe_allow_html=True)

    st.subheader("Criar meta")

    with st.form("goal_form"):
        name = st.text_input("Nome da meta")
        description = st.text_input("Descrição")
        target = st.number_input("Objetivo", min_value=0.0, step=10.0)
        current = st.number_input("Valor atual", min_value=0.0, step=10.0)

        submit = st.form_submit_button("Criar")

        if submit:
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

    st.markdown("---")

    if goals_df.empty:
        st.info("Ainda não existem metas.")
    else:
        for _, goal in goals_df.iterrows():
            target = float(goal["target_amount"])
            current = float(goal["current_amount"])
            progress = min(current / target, 1) if target > 0 else 0

            st.markdown(f"""
            <div class="simple-box">
                <h3>{goal['name']}</h3>
                <p class="small-text">{goal['description']}</p>
                <strong>{money(current)} / {money(target)}</strong>
            </div>
            """, unsafe_allow_html=True)

            st.progress(progress)

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                amount = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=5.0,
                    key=f"goal_amount_{goal['id']}"
                )

            with col2:
                if st.button(f"Adicionar #{goal['id']}"):
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
                if st.button(f"Retirar #{goal['id']}"):
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

            if st.button(f"Remover meta #{goal['id']}"):
                with engine.begin() as conn:
                    conn.execute(
                        text("DELETE FROM goals WHERE id = :id"),
                        {"id": int(goal["id"])}
                    )

                clear_cache()
                st.success("Meta removida.")
                st.rerun()

            st.markdown("---")


# =========================
# CATEGORIAS
# =========================
elif page == "Categorias":
    st.markdown('<div class="title">Categorias</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Gerir categorias usadas nas despesas.</div>', unsafe_allow_html=True)

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

    st.markdown("---")

    for _, category in categories_df.iterrows():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(category["name"])

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
    st.markdown('<div class="title">Exportar</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Descarregar movimentos em Excel.</div>', unsafe_allow_html=True)

    if filtered_df.empty:
        st.info("Não existem dados para exportar.")
    else:
        export_columns = ["id", "person", "type", "category", "description", "value", "date"]

        st.dataframe(
            filtered_df[export_columns],
            use_container_width=True,
            hide_index=True
        )

        excel_file = export_excel(filtered_df[export_columns])

        st.download_button(
            label="Descarregar Excel",
            data=excel_file,
            file_name="movimentos_financeiros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )