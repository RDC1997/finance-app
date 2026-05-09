
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# =========================
# API
# =========================
API = st.secrets.get("API", "http://127.0.0.1:8000")

# =========================
# DATA HELPERS
# =========================
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


def delete_transaction(tid):
    requests.delete(f"{API}/transaction/{tid}")


def update_transaction(tid, data):
    requests.put(f"{API}/transaction/{tid}", json=data)


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

st.markdown("""
<style>
.card {
    padding: 12px;
    border-radius: 12px;
    background: #111827;
    color: white;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# LOAD DATA
# =========================
df = get_transactions()
categories = get_categories()
goals = get_goals()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("Finance App")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Ruben", "Gabi", "Metas", "Categorias"]
)


# =========================
# VALIDATION
# =========================
def validate_date(d):
    return d <= date.today()


# =========================
# DASHBOARD
# =========================
if page == "Dashboard":

    st.title("Dashboard")

    if not df.empty:
        receitas = df[df["type"].str.lower() == "salario"]["value"].sum()
        despesas = df[df["type"].str.lower() == "despesa"]["value"].sum()
    else:
        receitas = despesas = 0

    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"{receitas:.2f} €")
    c2.metric("Despesas", f"{despesas:.2f} €")
    c3.metric("Saldo", f"{saldo:.2f} €")


# =========================
# RUBEN / GABI (CRUD COMPLETO)
# =========================
if page in ["Ruben", "Gabi"]:

    person = page

    st.title(person)

    tipo = st.selectbox("Tipo", ["Salario", "Despesa"])

    categoria = None
    descricao = ""

    if tipo == "Despesa":
        categoria = st.selectbox("Categoria", categories)

        if categoria == "Outros":
            st.warning("Descrição obrigatória")
            descricao = st.text_area("Descrição")

    col1, col2 = st.columns(2)
    valor = col1.number_input("Valor", min_value=0.0)
    data = col2.date_input("Data")

    if st.button("Adicionar"):

        if not validate_date(data):
            st.error("Data inválida")
            st.stop()

        if tipo == "Despesa" and categoria == "Outros" and not descricao.strip():
            st.error("Descrição obrigatória")
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

    df_p = df[df["person"] == person] if not df.empty else pd.DataFrame()

    for _, row in df_p.iterrows():

        with st.expander(f"{row['type']} - {row['value']} € ({row['date']})"):

            st.write("Categoria:", row["category"])
            st.write("Descrição:", row["description"])

            # ================= EDIT =================
            with st.form(f"edit_{row['id']}"):
                new_type = st.selectbox("Tipo", ["Salario", "Despesa"], index=0)
                new_value = st.number_input("Valor", value=float(row["value"]))
                new_cat = st.selectbox("Categoria", categories)
                new_desc = st.text_input("Descrição", value=row.get("description", ""))
                new_date = st.date_input("Data", value=row["date"])

                if st.form_submit_button("Guardar alterações"):
                    update_transaction(row["id"], {
                        "person": person,
                        "type": new_type,
                        "category": new_cat,
                        "description": new_desc,
                        "value": new_value,
                        "date": str(new_date)
                    })
                    st.rerun()

            # ================= DELETE =================
            if st.button(f"Eliminar {row['id']}"):
                delete_transaction(row["id"])
                st.rerun()


# =========================
# METAS (simplificado aqui)
# =========================
if page == "Metas":

    st.title("Metas")

    for g in goals:
        st.write(g)


# =========================
# CATEGORIAS
# =========================
if page == "Categorias":

    st.title("Categorias")

    nova = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        requests.post(f"{API}/categories", json={"name": nova})
        st.rerun()

    for c in categories:
        st.write(c)
