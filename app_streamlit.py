import streamlit as st
import requests
import pandas as pd
from datetime import date

API = st.secrets.get("API", "http://127.0.0.1:8000")


# =========================
# DATA
# =========================
def get_transactions():
    try:
        r = requests.get(f"{API}/transactions")
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
            return df
    except Exception as e:
        st.error(f"Erro GET transactions: {e}")
    return pd.DataFrame()


def get_categories():
    try:
        r = requests.get(f"{API}/categories")
        if r.ok:
            cats = [c["name"] for c in r.json()]
            if "Outros" not in cats:
                cats.append("Outros")
            return cats
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


def add_transaction(payload):
    return requests.post(f"{API}/transaction", json=payload)


def update_transaction(tid, data):
    return requests.put(f"{API}/transaction/{tid}", json=data)


def delete_transaction(tid):
    return requests.delete(f"{API}/transaction/{tid}")


def add_goal(data):
    return requests.post(f"{API}/goal", json=data)


def delete_goal(gid):
    return requests.delete(f"{API}/goal/{gid}")


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Finance App", layout="wide")

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
# RUBEN / GABI
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
            descricao = st.text_area("Descrição obrigatória")

    col1, col2 = st.columns(2)
    valor = col1.number_input("Valor", min_value=0.0)
    data = col2.date_input("Data")

    if st.button("Adicionar"):

        payload = {
            "person": person,
            "type": tipo,
            "category": categoria,
            "description": descricao,
            "value": valor,
            "date": str(data)
        }

        r = add_transaction(payload)

        if r.status_code == 200:
            st.success("Adicionado com sucesso")
            st.rerun()
        else:
            st.error("Erro ao adicionar")
            st.write("Status:", r.status_code)
            st.write("Resposta:", r.text)


    st.divider()
    st.subheader("Movimentos")

    df_p = df[df["person"] == person] if not df.empty else pd.DataFrame()

    for _, row in df_p.iterrows():

        with st.expander(f"{row['type']} - {row['value']} €"):

            st.write("Data:", row["date"])

            if row["type"].lower() == "despesa":
                st.write("Categoria:", row["category"])

                if row["category"] == "Outros":
                    st.write("Descrição:", row.get("description", ""))

            # EDITAR
            with st.form(f"edit_{row['id']}"):

                new_type = st.selectbox(
                    "Tipo",
                    ["Salario", "Despesa"],
                    index=0 if row["type"] == "Salario" else 1
                )

                new_category = st.selectbox("Categoria", categories)

                new_description = st.text_input(
                    "Descrição",
                    value=row.get("description", "")
                )

                new_value = st.number_input(
                    "Valor",
                    value=float(row["value"])
                )

                new_date = st.date_input(
                    "Data",
                    value=pd.to_datetime(row["date"])
                )

                if st.form_submit_button("Guardar"):

                    update_transaction(row["id"], {
                        "person": person,
                        "type": new_type,
                        "category": new_category,
                        "description": new_description,
                        "value": new_value,
                        "date": str(new_date)
                    })

                    st.rerun()

            if st.button("Eliminar", key=f"del_{row['id']}"):
                delete_transaction(row["id"])
                st.rerun()


# =========================
# METAS
# =========================
if page == "Metas":

    st.title("Metas")

    nome = st.text_input("Nome da meta")
    objetivo = st.number_input("Objetivo (€)", min_value=0.0)

    if st.button("Criar meta"):

        if nome.strip():
            r = add_goal({
                "name": nome,
                "target_amount": objetivo,
                "current_amount": 0
            })

            if r.status_code == 200:
                st.success("Meta criada")
                st.rerun()
            else:
                st.error("Erro ao criar meta")
                st.write(r.text)

    st.divider()

    saldo = df["value"].sum() if not df.empty else 0

    for g in goals:

        target = g.get("target_amount", 0)
        progresso = min((saldo / target) * 100 if target else 0, 100)

        st.write(f"**{g['name']}**")
        st.progress(progresso / 100)

        if st.button("Eliminar meta", key=f"goal_{g['id']}"):
            delete_goal(g["id"])
            st.rerun()


# =========================
# CATEGORIAS
# =========================
if page == "Categorias":

    st.title("Categorias")

    nova = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        if nova.strip() and nova.lower() != "outros":
            requests.post(f"{API}/categories", json={"name": nova})
            st.rerun()

    st.divider()

    for c in categories:

        col1, col2 = st.columns([3, 1])

        col1.write(c)

        if c != "Outros":
            if col2.button("Eliminar", key=f"cat_{c}"):
                requests.delete(f"{API}/categories/{c}")
                st.rerun()
