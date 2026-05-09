import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

API = "http://127.0.0.1:8000"


# =========================
# FUNÇÕES
# =========================
def calculate_savings(df):
    if df.empty:
        return 0

    receitas = df[df["type"].str.lower() == "salario"]["value"].sum()
    despesas = df[df["type"].str.lower() == "despesa"]["value"].sum()

    return receitas - despesas


def get_transactions():
    try:
        r = requests.get(f"{API}/transactions")
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
                df["date"] = pd.to_datetime(df["date"])
            return df
    except:
        pass
    return pd.DataFrame()


def add_transaction(data):
    requests.post(f"{API}/transaction", json=data)


def get_categories():
    try:
        r = requests.get(f"{API}/categories")
        if r.ok:
            return [c["name"] for c in r.json()]
    except:
        pass
    return ["Comida", "Casa", "Transportes", "Outros"]


def get_goals():
    try:
        r = requests.get(f"{API}/goals")
        if r.ok:
            return r.json()
    except:
        pass
    return []


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Finance App", layout="wide")

API = "https://finance-app-backend-xvo2.onrender.com"


# =========================
# STYLE
# =========================
st.markdown("""
<style>

.block-container {
    padding: 2rem;
}

.card {
    padding: 15px;
    border-radius: 12px;
    background: #111827;
    margin-bottom: 10px;
    border: 1px solid #1f2937;
    color: white;
}

.stButton button {
    border-radius: 10px;
    background: #1f2937;
    color: white;
    border: 1px solid #374151;
}

.stButton button:hover {
    border: 1px solid #60a5fa;
    transform: scale(1.02);
}

</style>
""", unsafe_allow_html=True)


# =========================
# DATA
# =========================
df = get_transactions()
categories = get_categories()
goals = get_goals()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("💰 Finance App")

page = st.sidebar.radio(
    "Menu",
    ["🏠 Dashboard", "👨 Ruben", "👩 Gabi", "🎯 Metas", "🏷 Categorias"]
)


# =========================
# DASHBOARD
# =========================
if page == "🏠 Dashboard":

    st.title("Dashboard Financeiro")

    receitas = df[df["type"].str.lower() == "salario"]["value"].sum() if not df.empty else 0
    despesas = df[df["type"].str.lower() == "despesa"]["value"].sum() if not df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    c1.metric("Receitas", f"{receitas:.2f} €")
    c2.metric("Despesas", f"{despesas:.2f} €")
    c3.metric("Saldo", f"{saldo:.2f} €")

    st.divider()

    # =========================
    # GRÁFICO 1 - EVOLUÇÃO
    # =========================
    st.subheader("Evolução financeira")

    if not df.empty:

        df_sorted = df.sort_values("date")

        df_sorted["mov"] = df_sorted.apply(
            lambda x: x["value"] if x["type"].lower() == "salario" else -x["value"],
            axis=1
        )

        df_sorted["saldo"] = df_sorted["mov"].cumsum()

        fig, ax = plt.subplots()
        ax.plot(df_sorted["date"], df_sorted["saldo"])
        ax.set_title("Evolução do saldo")
        ax.set_xlabel("Data")
        ax.set_ylabel("Saldo (€)")

        st.pyplot(fig)

    # =========================
    # GRÁFICO 2 - CATEGORIAS
    # =========================
    st.subheader("Gastos por categoria")

    if not df.empty:

        despesas = df[df["type"].str.lower() == "despesa"]

        if not despesas.empty:

            categorias = despesas.groupby("category")["value"].sum()

            fig2, ax2 = plt.subplots()
            ax2.bar(categorias.index, categorias.values)

            ax2.set_title("Despesas por categoria")
            ax2.set_ylabel("€")

            st.pyplot(fig2)

    st.divider()

    st.subheader("Últimos movimentos")

    if df.empty:
        st.info("Sem dados ainda")
    else:
        for _, row in df.tail(8).iterrows():
            st.markdown(f"""
            <div class="card">
                <b>{row['type']}</b> • {row['category']} <br>
                {row['value']} € • {row['date']}
            </div>
            """, unsafe_allow_html=True)


# =========================
# RUBEN / GABI
# =========================
if page in ["👨 Ruben", "👩 Gabi"]:

    person = "Ruben" if "Ruben" in page else "Gabi"

    st.title(person)

    tipo = st.selectbox("Tipo", ["Salario", "Despesa"])

    categoria = None
    descricao = ""

    if tipo == "Despesa":
        categoria = st.selectbox("Categoria", categories)

        if categoria == "Outros":
            st.warning("Categoria 'Outros' obriga descrição")
            descricao = st.text_area("Descrição obrigatória")

    col1, col2 = st.columns(2)

    valor = col1.number_input("Valor", min_value=0.0)
    data = col2.date_input("Data")

    if data > date.today():
        st.error("Data inválida")
        st.stop()

    if st.button("Adicionar"):

        if tipo == "Despesa" and categoria == "Outros" and not descricao.strip():
            st.error("Descrição obrigatória para 'Outros'")
            st.stop()

        add_transaction({
            "person": person,
            "type": tipo,
            "category": categoria,
            "description": descricao,
            "value": valor,
            "date": str(data)
        })

        st.rerun()

    st.divider()

    st.subheader("Movimentos")

    if not df.empty:
        df_p = df[df["person"] == person]

        for _, row in df_p.tail(10).iterrows():
            st.markdown(f"""
            <div class="card">
                <b>{row['type']}</b> - {row['category']} <br>
                {row['value']} € | {row['date']}
            </div>
            """, unsafe_allow_html=True)


# =========================
# METAS
# =========================
if page == "🎯 Metas":

    st.title("Metas Financeiras")

    nome = st.text_input("Nome da meta")
    desc = st.text_input("Descrição")
    objetivo = st.number_input("Objetivo (€)", min_value=0.0)

    if st.button("Criar meta"):

        if nome.strip():
            requests.post(f"{API}/goal", json={
                "name": nome,
                "description": desc,
                "target_amount": objetivo,
                "current_amount": 0
            })

            st.rerun()

    st.divider()

    saldo = calculate_savings(df)

    for g in goals:

        target = g.get("target_amount", 0)

        if target > 0:
            progresso = min((saldo / target) * 100, 100)
        else:
            progresso = 0

        st.markdown(f"""
        <div class="card">
            <b>{g['name']}</b><br>
            {g.get('description','')}<br><br>
            Progresso: {progresso:.1f}%
        </div>
        """, unsafe_allow_html=True)

        st.progress(progresso / 100)


# =========================
# CATEGORIAS
# =========================
if page == "🏷 Categorias":

    st.title("Categorias")

    nova = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        if nova.strip():
            requests.post(f"{API}/categories", json={"name": nova})
            st.rerun()

    st.divider()

    for c in categories:
        st.markdown(f"<div class='card'>{c}</div>", unsafe_allow_html=True)