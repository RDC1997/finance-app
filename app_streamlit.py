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
    except:
        pass
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


def add_transaction(data):
    return requests.post(f"{API}/transaction", json=data)


def update_transaction(tid, data):
    return requests.put(f"{API}/transaction/{tid}", json=data)


def delete_transaction(tid):
    return requests.delete(f"{API}/transaction/{tid}")


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Finance App", layout="wide")

df = get_transactions()
categories = get_categories()
goals = get_goals()


# =========================
# MENU
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

    st.title("Dashboard Financeiro")

    receitas = df[df["type"].str.lower() == "salario"]["value"].sum() if not df.empty else 0
    despesas = df[df["type"].str.lower() == "despesa"]["value"].sum() if not df.empty else 0
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    c1.metric("Receitas", f"{receitas:.2f} €")
    c2.metric("Despesas", f"{despesas:.2f} €")
    c3.metric("Saldo", f"{saldo:.2f} €")

    st.markdown("---")

    st.subheader("Últimos movimentos")

    if df.empty:
        st.info("Sem dados")
    else:
        for _, row in df.tail(8).iterrows():
            st.markdown(f"""
            <div style="padding:10px; border:1px solid #333; border-radius:10px; margin-bottom:8px;">
                <b>{row['type']}</b> • {row['value']} € <br>
                {row['date']}
            </div>
            """, unsafe_allow_html=True)


# =========================
# RUBEN / GABI
# =========================
if page in ["Ruben", "Gabi"]:

    person = page
    st.title(person)

    st.markdown("## Adicionar movimento")

    tipo = st.selectbox("Tipo", ["Salario", "Despesa"])

    categoria = "Salario"
    descricao = ""

    if tipo == "Despesa":
        categoria = st.selectbox("Categoria", categories)

        if categoria == "Outros":
            descricao = st.text_area("Descrição obrigatória")

    valor = st.number_input("Valor", min_value=0.0)
    data = st.date_input("Data")

    if st.button("Adicionar"):

        if data > date.today():
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

    st.markdown("---")
    st.subheader("Movimentos")

    df_p = df[df["person"] == person] if not df.empty else pd.DataFrame()

    for _, row in df_p.iterrows():

        with st.expander(f"{row['type']} • {row['value']} €"):

            st.write("Tipo:", row["type"])

            if row["type"].lower() == "despesa":
                st.write("Categoria:", row["category"])

                if row["category"] == "Outros":
                    st.write("Descrição:", row.get("description", ""))

            st.write("Data:", row["date"])

            st.markdown("### Editar")

            with st.form(f"edit_{row['id']}"):

                new_type = st.selectbox(
                    "Tipo",
                    ["Salario", "Despesa"],
                    index=0 if row["type"] == "Salario" else 1
                )

                new_category = "Salario"
                new_description = ""

                if new_type == "Despesa":
                    new_category = st.selectbox("Categoria", categories)

                    if new_category == "Outros":
                        new_description = st.text_area(
                            "Descrição obrigatória",
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

                    if new_type == "Despesa" and new_category == "Outros" and not new_description.strip():
                        st.error("Descrição obrigatória")
                        st.stop()

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

    st.markdown("---")

    saldo = df["value"].sum() if not df.empty else 0

    for g in goals:

        target = g.get("target_amount", 0)
        progresso = min((saldo / target) * 100 if target else 0, 100)

        st.markdown(f"""
        <div style="padding:10px; border:1px solid #333; border-radius:10px; margin-bottom:8px;">
            <b>{g['name']}</b><br>
            {g.get('description','')}<br>
            Progresso: {progresso:.1f}%
        </div>
        """, unsafe_allow_html=True)

        st.progress(progresso / 100)


# =========================
# CATEGORIAS
# =========================
if page == "Categorias":

    st.title("Categorias")

    nova = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        if nova.strip():
            requests.post(f"{API}/categories", json={"name": nova})
            st.rerun()

    st.markdown("---")

    for c in categories:
        st.markdown(f"<div style='padding:8px; border:1px solid #333; border-radius:8px;'>{c}</div>", unsafe_allow_html=True)
