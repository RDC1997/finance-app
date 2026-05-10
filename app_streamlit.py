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
    .main-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #64748b;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .card {
        padding: 22px;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827, #1e293b);
        border: 1px solid #334155;
        margin-bottom: 15px;
    }

    .card-title {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .card-value {
        color: #f8fafc;
        font-size: 28px;
        font-weight: 800;
    }

    .section-box {
        padding: 18px;
        border-radius: 15px;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-bottom: 14px;
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
        df = pd.read_sql("SELECT * FROM transactions ORDER BY id DESC", conn)

    if df.empty:
        return pd.DataFrame(columns=[
            "id", "person", "type", "category", "description", "value", "date"
        ])

    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date_dt"].dt.year
    df["month"] = df["date_dt"].dt.month

    return df


def load_categories():
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM categories ORDER BY name", conn)

    if df.empty:
        default_categories = [
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
            for cat in default_categories:
                conn.execute(
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

    if "date_dt" in export_df.columns:
        export_df = export_df.drop(columns=["date_dt"])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Movimentos")

    return output.getvalue()


def card(title, value):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def apply_filters(dataframe):
    if dataframe.empty:
        return dataframe

    filtered = dataframe.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros")

    pessoas = ["Todos"] + sorted(filtered["person"].dropna().unique().tolist())
    pessoa = st.sidebar.selectbox("Pessoa", pessoas)

    if pessoa != "Todos":
        filtered = filtered[filtered["person"] == pessoa]

    years = sorted(filtered["year"].dropna().astype(int).unique().tolist(), reverse=True)

    if years:
        ano = st.sidebar.selectbox("Ano", ["Todos"] + years)
        if ano != "Todos":
            filtered = filtered[filtered["year"] == int(ano)]

    months_map = {
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

    mes_nome = st.sidebar.selectbox("Mês", list(months_map.keys()))

    if months_map[mes_nome] != 0:
        filtered = filtered[filtered["month"] == months_map[mes_nome]]

    pesquisa = st.sidebar.text_input("Pesquisar")

    if pesquisa.strip():
        termo = pesquisa.strip().lower()
        filtered = filtered[
            filtered["description"].fillna("").str.lower().str.contains(termo)
            | filtered["category"].fillna("").str.lower().str.contains(termo)
            | filtered["type"].fillna("").str.lower().str.contains(termo)
            | filtered["person"].fillna("").str.lower().str.contains(termo)
        ]

    return filtered


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
        "Casal",
        "Metas",
        "Categorias",
        "Exportar"
    ]
)

filtered_df = apply_filters(df)


# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    st.markdown('<div class="main-title">Dashboard Financeiro</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Visão geral das receitas, despesas e saldo.</div>', unsafe_allow_html=True)

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
        st.info("Sem movimentos para os filtros selecionados.")
    else:
        col1, col2 = st.columns(2)

        despesas_df = filtered_df[filtered_df["type"].str.lower() == "despesa"]

        with col1:
            if not despesas_df.empty:
                resumo_cat = despesas_df.groupby("category", as_index=False)["value"].sum()
                fig = px.pie(
                    resumo_cat,
                    values="value",
                    names="category",
                    title="Despesas por Categoria"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem despesas para gráfico de categorias.")

        with col2:
            resumo_pessoa = filtered_df.groupby(["person", "type"], as_index=False)["value"].sum()
            fig = px.bar(
                resumo_pessoa,
                x="person",
                y="value",
                color="type",
                barmode="group",
                title="Resumo por Pessoa"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Últimos movimentos")
        st.dataframe(
            filtered_df[["person", "type", "category", "description", "value", "date"]],
            use_container_width=True,
            hide_index=True
        )


# =========================
# PERSON PAGE
# =========================
elif page in ["Ruben", "Gabi", "Casal"]:
    st.markdown(f'<div class="main-title">{page}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Adicionar, consultar, editar e remover movimentos.</div>', unsafe_allow_html=True)

    person_options = ["Ruben", "Gabi"] if page == "Casal" else [page]

    st.subheader("Adicionar movimento")

    with st.form(f"form_add_{page}"):
        c1, c2, c3 = st.columns(3)

        with c1:
            person = st.selectbox("Pessoa", person_options)

        with c2:
            tipo = st.selectbox("Tipo", ["Salário", "Despesa"])

        with c3:
            categoria = st.selectbox("Categoria", categories)

        descricao = st.text_input("Descrição")

        c4, c5 = st.columns(2)

        with c4:
            valor = st.number_input("Valor", min_value=0.0, step=1.0)

        with c5:
            data_movimento = st.date_input("Data", value=date.today(), max_value=date.today())

        submit = st.form_submit_button("Adicionar movimento")

        if submit:
            if valor <= 0:
                st.error("O valor tem de ser superior a zero.")
            elif tipo == "Despesa" and categoria == "Outros" and not descricao.strip():
                st.error("Quando a categoria é Outros, a descrição é obrigatória.")
            else:
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO transactions
                    (person, type, category, description, value, date)
                    VALUES
                    (:person, :type, :category, :description, :value, :date)
                    """), {
                        "person": person,
                        "type": tipo,
                        "category": categoria,
                        "description": descricao.strip(),
                        "value": valor,
                        "date": str(data_movimento)
                    })

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
        st.info("Sem movimentos para os filtros selecionados.")
    else:
        st.dataframe(
            page_df[["id", "person", "type", "category", "description", "value", "date"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("Editar movimento")

        movimento_id = st.selectbox(
            "Escolhe o ID do movimento",
            page_df["id"].tolist(),
            key=f"edit_select_{page}"
        )

        movimento = page_df[page_df["id"] == movimento_id].iloc[0]

        with st.form(f"edit_form_{page}"):
            c1, c2, c3 = st.columns(3)

            with c1:
                edit_person = st.selectbox(
                    "Pessoa",
                    ["Ruben", "Gabi"],
                    index=["Ruben", "Gabi"].index(movimento["person"]) if movimento["person"] in ["Ruben", "Gabi"] else 0
                )

            with c2:
                edit_tipo = st.selectbox(
                    "Tipo",
                    ["Salário", "Despesa"],
                    index=["Salário", "Despesa"].index(movimento["type"]) if movimento["type"] in ["Salário", "Despesa"] else 0
                )

            with c3:
                edit_categoria = st.selectbox(
                    "Categoria",
                    categories,
                    index=categories.index(movimento["category"]) if movimento["category"] in categories else 0
                )

            edit_descricao = st.text_input(
                "Descrição",
                value=str(movimento["description"] or "")
            )

            c4, c5 = st.columns(2)

            with c4:
                edit_valor = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=1.0,
                    value=float(movimento["value"])
                )

            with c5:
                current_date = pd.to_datetime(movimento["date"]).date()
                edit_date = st.date_input(
                    "Data",
                    value=current_date,
                    max_value=date.today()
                )

            atualizar = st.form_submit_button("Guardar alterações")

            if atualizar:
                if edit_valor <= 0:
                    st.error("O valor tem de ser superior a zero.")
                elif edit_tipo == "Despesa" and edit_categoria == "Outros" and not edit_descricao.strip():
                    st.error("Quando a categoria é Outros, a descrição é obrigatória.")
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
                            "id": int(movimento_id),
                            "person": edit_person,
                            "type": edit_tipo,
                            "category": edit_categoria,
                            "description": edit_descricao.strip(),
                            "value": edit_valor,
                            "date": str(edit_date)
                        })

                    st.success("Movimento atualizado.")
                    st.rerun()

        if st.button("Remover movimento selecionado", key=f"remove_{page}"):
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM transactions WHERE id = :id"),
                    {"id": int(movimento_id)}
                )

            st.success("Movimento removido.")
            st.rerun()


# =========================
# METAS
# =========================
elif page == "Metas":
    st.markdown('<div class="main-title">Metas Financeiras</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Cria metas e atualiza o progresso com entradas ou retiradas.</div>', unsafe_allow_html=True)

    st.subheader("Criar nova meta")

    with st.form("goal_form"):
        nome = st.text_input("Nome da meta")
        descricao = st.text_input("Descrição")
        objetivo = st.number_input("Objetivo", min_value=0.0, step=10.0)
        atual = st.number_input("Valor atual", min_value=0.0, step=10.0)

        submit = st.form_submit_button("Criar meta")

        if submit:
            if not nome.strip():
                st.error("O nome da meta é obrigatório.")
            elif objetivo <= 0:
                st.error("O objetivo tem de ser superior a zero.")
            else:
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO goals
                    (name, description, target_amount, current_amount)
                    VALUES
                    (:name, :description, :target_amount, :current_amount)
                    """), {
                        "name": nome.strip(),
                        "description": descricao.strip(),
                        "target_amount": objetivo,
                        "current_amount": atual
                    })

                st.success("Meta criada.")
                st.rerun()

    st.markdown("---")

    if goals_df.empty:
        st.info("Ainda não existem metas.")
    else:
        for _, g in goals_df.iterrows():
            target = float(g["target_amount"])
            current = float(g["current_amount"])
            progress = min(current / target, 1) if target > 0 else 0

            st.markdown(f"### {g['name']}")
            st.write(g["description"])
            st.write(f"{money(current)} / {money(target)}")
            st.progress(progress)

            c1, c2, c3 = st.columns([2, 2, 1])

            with c1:
                valor_meta = st.number_input(
                    f"Valor para atualizar #{g['id']}",
                    min_value=0.0,
                    step=5.0,
                    key=f"goal_value_{g['id']}"
                )

            with c2:
                if st.button(f"Adicionar à meta #{g['id']}"):
                    with engine.begin() as conn:
                        conn.execute(text("""
                        UPDATE goals
                        SET current_amount = current_amount + :value
                        WHERE id = :id
                        """), {
                            "value": float(valor_meta),
                            "id": int(g["id"])
                        })

                    st.success("Valor adicionado à meta.")
                    st.rerun()

                if st.button(f"Retirar da meta #{g['id']}"):
                    novo_valor = max(current - float(valor_meta), 0)

                    with engine.begin() as conn:
                        conn.execute(text("""
                        UPDATE goals
                        SET current_amount = :value
                        WHERE id = :id
                        """), {
                            "value": novo_valor,
                            "id": int(g["id"])
                        })

                    st.success("Valor retirado da meta.")
                    st.rerun()

            with c3:
                if st.button(f"Remover #{g['id']}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("DELETE FROM goals WHERE id = :id"),
                            {"id": int(g["id"])}
                        )

                    st.success("Meta removida.")
                    st.rerun()

            st.markdown("---")


# =========================
# CATEGORIAS
# =========================
elif page == "Categorias":
    st.markdown('<div class="main-title">Categorias</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Cria e remove categorias de despesas.</div>', unsafe_allow_html=True)

    nova = st.text_input("Nova categoria")

    if st.button("Adicionar categoria"):
        if not nova.strip():
            st.error("Escreve o nome da categoria.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO categories (name) VALUES (:name)"),
                        {"name": nova.strip()}
                    )

                st.success("Categoria adicionada.")
                st.rerun()

            except Exception:
                st.error("Categoria já existe.")

    st.markdown("---")

    for _, c in categories_df.iterrows():
        c1, c2 = st.columns([4, 1])

        with c1:
            st.markdown(f"### {c['name']}")

        with c2:
            if c["name"].lower() == "outros":
                st.caption("Protegida")
            else:
                if st.button("Remover", key=f"cat_{c['id']}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("DELETE FROM categories WHERE id = :id"),
                            {"id": int(c["id"])}
                        )

                    st.success("Categoria removida.")
                    st.rerun()


# =========================
# EXPORTAR
# =========================
elif page == "Exportar":
    st.markdown('<div class="main-title">Exportar Dados</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Exporta os movimentos filtrados para Excel.</div>', unsafe_allow_html=True)

    if filtered_df.empty:
        st.info("Não existem dados para exportar.")
    else:
        st.dataframe(
            filtered_df[["id", "person", "type", "category", "description", "value", "date"]],
            use_container_width=True,
            hide_index=True
        )

        excel_data = export_excel(
            filtered_df[["id", "person", "type", "category", "description", "value", "date"]]
        )

        st.download_button(
            label="Descarregar Excel",
            data=excel_data,
            file_name="movimentos_financeiros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )