import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Rubi & Gabi Finance",
    layout="wide",
    page_icon="💰"
)

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

engine = create_engine(DATABASE_URL)

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
def money(v):
    return f"{float(v):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def load_transactions():

    with engine.begin() as conn:
        df = pd.read_sql(
            "SELECT * FROM transactions ORDER BY id DESC",
            conn
        )

    if df.empty:
        return pd.DataFrame(columns=[
            "id",
            "person",
            "type",
            "category",
            "description",
            "value",
            "date"
        ])

    return df


def load_categories():

    with engine.begin() as conn:
        df = pd.read_sql(
            "SELECT * FROM categories ORDER BY name",
            conn
        )

    if df.empty:

        default_categories = [
            "Casa",
            "Comida",
            "Transportes",
            "Lazer",
            "Outros"
        ]

        with engine.begin() as conn2:

            for cat in default_categories:

                conn2.execute(
                    text("""
                    INSERT INTO categories (name)
                    VALUES (:name)
                    ON CONFLICT (name) DO NOTHING
                    """),
                    {"name": cat}
                )

        return load_categories()

    return df


def load_goals():

    with engine.begin() as conn:
        df = pd.read_sql(
            "SELECT * FROM goals ORDER BY id DESC",
            conn
        )

    return df


# =========================
# LOAD DATA
# =========================
df = load_transactions()

categories_df = load_categories()

goals_df = load_goals()

categories = categories_df["name"].tolist()

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
        "Metas",
        "Categorias"
    ]
)

# =========================
# DASHBOARD
# =========================
if page == "Dashboard":

    st.title("Dashboard Financeiro")

    receitas = 0
    despesas = 0

    if not df.empty:

        receitas = df[
            df["type"].str.lower() == "salário"
        ]["value"].sum()

        despesas = df[
            df["type"].str.lower() == "despesa"
        ]["value"].sum()

    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    c1.metric("Receitas", money(receitas))

    c2.metric("Despesas", money(despesas))

    c3.metric("Saldo", money(saldo))

    st.markdown("---")

    if not df.empty:

        despesas_df = df[
            df["type"].str.lower() == "despesa"
        ]

        if not despesas_df.empty:

            resumo = despesas_df.groupby(
                "category",
                as_index=False
            )["value"].sum()

            fig = px.pie(
                resumo,
                values="value",
                names="category",
                title="Despesas por Categoria"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    st.markdown("---")

    st.subheader("Últimos Movimentos")

    if df.empty:

        st.info("Sem movimentos.")

    else:

        st.dataframe(
            df[
                [
                    "person",
                    "type",
                    "category",
                    "description",
                    "value",
                    "date"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

# =========================
# RUBEN / GABI
# =========================
elif page in ["Ruben", "Gabi"]:

    person = page

    st.title(person)

    with st.form(f"form_{person}"):

        tipo = st.selectbox(
            "Tipo",
            [
                "Salário",
                "Despesa"
            ]
        )

        categoria = st.selectbox(
            "Categoria",
            categories
        )

        descricao = st.text_input(
            "Descrição"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            step=1.0
        )

        data_movimento = st.date_input(
            "Data",
            value=date.today(),
            max_value=date.today()
        )

        submit = st.form_submit_button(
            "Adicionar Movimento"
        )

        if submit:

            if valor <= 0:

                st.error(
                    "Valor inválido."
                )

            elif (
                tipo == "Despesa"
                and categoria == "Outros"
                and not descricao.strip()
            ):

                st.error(
                    "Descrição obrigatória em Outros."
                )

            else:

                with engine.begin() as conn:

                    conn.execute(text("""
                    INSERT INTO transactions
                    (
                        person,
                        type,
                        category,
                        description,
                        value,
                        date
                    )
                    VALUES
                    (
                        :person,
                        :type,
                        :category,
                        :description,
                        :value,
                        :date
                    )
                    """), {
                        "person": person,
                        "type": tipo,
                        "category": categoria,
                        "description": descricao.strip(),
                        "value": valor,
                        "date": str(data_movimento)
                    })

                st.success(
                    "Movimento adicionado."
                )

                st.rerun()

    st.markdown("---")

    person_df = df[
        df["person"].str.lower() == person.lower()
    ] if not df.empty else pd.DataFrame()

    receitas = person_df[
        person_df["type"].str.lower() == "salário"
    ]["value"].sum() if not person_df.empty else 0

    despesas = person_df[
        person_df["type"].str.lower() == "despesa"
    ]["value"].sum() if not person_df.empty else 0

    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Receitas",
        money(receitas)
    )

    c2.metric(
        "Despesas",
        money(despesas)
    )

    c3.metric(
        "Saldo",
        money(saldo)
    )

    st.markdown("---")

    st.subheader("Movimentos")

    if person_df.empty:

        st.info("Sem movimentos.")

    else:

        st.dataframe(
            person_df[
                [
                    "type",
                    "category",
                    "description",
                    "value",
                    "date"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        remover = st.selectbox(
            "Seleciona movimento para remover",
            person_df["id"].tolist()
        )

        if st.button(
            "Remover Movimento"
        ):

            with engine.begin() as conn:

                conn.execute(
                    text("""
                    DELETE FROM transactions
                    WHERE id = :id
                    """),
                    {"id": int(remover)}
                )

            st.success(
                "Movimento removido."
            )

            st.rerun()

# =========================
# METAS
# =========================
elif page == "Metas":

    st.title("Metas")

    with st.form("goal_form"):

        nome = st.text_input(
            "Nome da Meta"
        )

        descricao = st.text_input(
            "Descrição"
        )

        objetivo = st.number_input(
            "Objetivo",
            min_value=0.0,
            step=10.0
        )

        atual = st.number_input(
            "Valor Atual",
            min_value=0.0,
            step=10.0
        )

        submit = st.form_submit_button(
            "Criar Meta"
        )

        if submit:

            if not nome.strip():

                st.error(
                    "O nome da meta é obrigatório."
                )

            elif objetivo <= 0:

                st.error(
                    "O objetivo tem de ser superior a zero."
                )

            else:

                with engine.begin() as conn:

                    conn.execute(text("""
                    INSERT INTO goals
                    (
                        name,
                        description,
                        target_amount,
                        current_amount
                    )
                    VALUES
                    (
                        :name,
                        :description,
                        :target_amount,
                        :current_amount
                    )
                    """), {
                        "name": nome.strip(),
                        "description": descricao.strip(),
                        "target_amount": objetivo,
                        "current_amount": atual
                    })

                st.success(
                    "Meta criada."
                )

                st.rerun()

    st.markdown("---")

    if goals_df.empty:

        st.info("Sem metas.")

    else:

        for _, g in goals_df.iterrows():

            target = float(
                g["target_amount"]
            )

            current = float(
                g["current_amount"]
            )

            progress = 0

            if target > 0:

                progress = min(
                    current / target,
                    1
                )

            st.markdown(f"""
            ### {g['name']}

            {g['description']}

            {money(current)} / {money(target)}
            """)

            st.progress(progress)

            if st.button(
                f"Remover Meta {g['id']}"
            ):

                with engine.begin() as conn:

                    conn.execute(
                        text("""
                        DELETE FROM goals
                        WHERE id = :id
                        """),
                        {"id": int(g["id"])}
                    )

                st.success(
                    "Meta removida."
                )

                st.rerun()

# =========================
# CATEGORIAS
# =========================
elif page == "Categorias":

    st.title("Categorias")

    nova = st.text_input(
        "Nova Categoria"
    )

    if st.button(
        "Adicionar Categoria"
    ):

        if not nova.strip():

            st.error(
                "Escreve o nome da categoria."
            )

        else:

            try:

                with engine.begin() as conn:

                    conn.execute(
                        text("""
                        INSERT INTO categories (name)
                        VALUES (:name)
                        """),
                        {"name": nova.strip()}
                    )

                st.success(
                    "Categoria adicionada."
                )

                st.rerun()

            except Exception:

                st.error(
                    "Categoria já existe."
                )

    st.markdown("---")

    for _, c in categories_df.iterrows():

        c1, c2 = st.columns([4, 1])

        with c1:

            st.markdown(
                f"### {c['name']}"
            )

        with c2:

            if c["name"].lower() == "outros":

                st.caption(
                    "Protegida"
                )

            else:

                if st.button(
                    "Remover",
                    key=f"cat_{c['id']}"
                ):

                    with engine.begin() as conn:

                        conn.execute(
                            text("""
                            DELETE FROM categories
                            WHERE id = :id
                            """),
                            {"id": int(c["id"])}
                        )

                    st.success(
                        "Categoria removida."
                    )

                    st.rerun()