import streamlit as st
import requests
import pandas as pd
from datetime import date

API = st.secrets.get("API", "http://127.0.0.1:8000")

# =========================
# DATA LAYER
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
    requests.post(f"{API}/transaction", json=data)


def update_transaction(tid, data):
    requests.put(f"{API}/transaction/{tid}", json=data)


def delete_transaction(tid):
    requests.delete(f"{API}/transaction/{tid}")


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
            st.warning("Descrição obrigatória para 'Outros'")
            descricao = st.text_area("Descrição")

    col1, col2 = st.columns(2)
    valor = col1.number_input("Valor", min_value=0.0)
    data = col2.date_input("Data")

    if st.button("Adicionar"):

        if data > date.today():
            st.error("Não podes usar datas futuras")
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

        with st.expander(f"{row['type']} - {row['value']} €"):

            st.write("Data:", row["date"])

            if row["type"].lower() == "despesa":
                st.write("Categoria:", row["category"])

                if row["category"] == "Outros":
                    st.write("Descrição:", row.get("description", ""))

            col1, col2 = st.columns(2)

            # ================= EDIT =================
            with col1:

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

                    if st.form_submit_button("Guardar alterações"):

                        update_transaction(row["id"], {
                            "person": person,
                            "type": new_type,
                            "category": new_category,
                            "description": new_description,
                            "value": new_value,
                            "date": str(new_date)
                        })

                        st.rerun()

            # ================= DELETE =================
            with col2:
                if st.button("Eliminar", key=f"del_{row['id']}"):
                    delete_transaction(row["id"])
                    st.rerun()


# =========================
# METAS
# =========================
if page == "Metas":

    st.title("Metas")

    if not goals:
        st.info("Ainda não tens metas criadas.")
    else:
        for g in goals:

            target = g.get("target_amount", 0)
            current = g.get("current_amount", 0)

            progresso = (current / target * 100) if target else 0
            progresso = min(progresso, 100)

            st.markdown(f"""
            **{g['name']}**  
            {progresso:.1f}% concluído
            """)

            st.progress(progresso / 100)


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
