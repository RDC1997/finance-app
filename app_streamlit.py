import streamlit as st
import requests
import pandas as pd
from datetime import date

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="Finance App", layout="wide")


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
# API
# =========================
def get_transactions():
    r = requests.get(f"{API}/transactions")
    df = pd.DataFrame(r.json() if r.ok else [])
    if not df.empty:
        df.columns = [c.lower() for c in df.columns]
    return df


def add_transaction(data):
    requests.post(f"{API}/transaction", json=data)


def delete_transaction(id):
    requests.delete(f"{API}/transaction/{id}")


def get_categories():
    r = requests.get(f"{API}/categories")
    return [c["name"] for c in r.json()] if r.ok else ["Comida", "Casa", "Transportes", "Outros"]


def get_goals():
    r = requests.get(f"{API}/goals")
    return r.json() if r.ok else []


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

    receitas = df[df["type"].str.contains("Sal")]["value"].sum() if not df.empty else 0
    despesas = df[df["type"].str.contains("Desp")]["value"].sum() if not df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    c1.metric("Receitas", f"{receitas:.2f} €")
    c2.metric("Despesas", f"{despesas:.2f} €")
    c3.metric("Saldo", f"{saldo:.2f} €")

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
# RUBEN / GABI (FIX FINAL OUTROS)
# =========================
if page in ["👨 Ruben", "👩 Gabi"]:

    person = "Ruben" if "Ruben" in page else "Gabi"

    st.title(person)

    tipo = st.selectbox("Tipo", ["Salário", "Despesa"])

    categoria = None
    descricao = ""

    if tipo == "Despesa":

        categoria = st.selectbox("Categoria", categories)

        # 🔥 REGRA FIXA (NÃO DESAPARECE MAIS)
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

        if tipo == "Despesa" and categoria == "Outros" and (not descricao or descricao.strip() == ""):
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

        if nome:
            requests.post(f"{API}/goal", json={
                "name": nome,
                "description": desc,
                "target": objetivo
            })
            st.rerun()

    st.divider()

    saldo = df["value"].sum() if not df.empty else 0

    for g in goals:

        progresso = min((saldo / g["target"]) * 100 if g["target"] else 0, 100)

        st.markdown(f"""
        <div class="card">
            <b>{g['name']}</b><br>
            {g['description']}<br><br>
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
        requests.post(f"{API}/categories", json={"name": nova})
        st.rerun()

    st.divider()

    for c in categories:
        st.markdown(f"<div class='card'>{c}</div>", unsafe_allow_html=True)