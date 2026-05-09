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


# =========================
# MENU
# =========================
st.sidebar.title("Finance App")

page = st.sidebar.radio(
    "Menu",
    ["Ruben", "Gabi"]
)


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

    # =========================
    # INPUT DINÂMICO
    # =========================
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


# =========================
# MOVIMENTOS (SEM st.divider)
# =========================
st.markdown("---")
st.subheader("Movimentos")

df_p = df[df["person"] == person] if not df.empty else pd.DataFrame()

for _, row in df_p.iterrows():

    titulo = f"{row['type']} • {row['value']} €"

    with st.expander(titulo):

        st.write("Tipo:", row["type"])

        if row["type"].lower() == "despesa":
            st.write("Categoria:", row["category"])

            if row["category"] == "Outros":
                st.write("Descrição:", row.get("description", ""))

        st.write("Data:", row["date"])

        # =========================
        # EDITAR
        # =========================
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

            if st.form_submit_button("Guardar alterações"):

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
