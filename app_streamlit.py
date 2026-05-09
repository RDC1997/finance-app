
# =========================
# MOVIMENTOS (CORRIGIDO UI)
# =========================
st.divider()
st.subheader("Movimentos")

df_p = df[df["person"] == person] if not df.empty else pd.DataFrame()

for _, row in df_p.iterrows():

    titulo = f"{row['type']} • {row['value']} €"

    with st.expander(titulo):

        # =========================
        # RESUMO SIMPLES
        # =========================
        st.write("Tipo:", row["type"])

        # =========================
        # EDITAR (LÓGICA LIMPA)
        # =========================
        st.markdown("### Editar")

        with st.form(f"edit_{row['id']}"):

            new_type = st.selectbox(
                "Tipo",
                ["Salario", "Despesa"],
                index=0 if row["type"] == "Salario" else 1
            )

            # =========================
            # SALÁRIO
            # =========================
            if new_type == "Salario":

                new_value = st.number_input(
                    "Valor",
                    value=float(row["value"])
                )

                new_date = st.date_input(
                    "Data",
                    value=pd.to_datetime(row["date"])
                )

                new_category = "Salario"
                new_description = ""

            # =========================
            # DESPESA
            # =========================
            else:

                new_category = st.selectbox(
                    "Categoria",
                    categories,
                    index=categories.index(row["category"]) if row["category"] in categories else 0
                )

                new_value = st.number_input(
                    "Valor",
                    value=float(row["value"])
                )

                new_date = st.date_input(
                    "Data",
                    value=pd.to_datetime(row["date"])
                )

                # =========================
                # OUTROS
                # =========================
                if new_category == "Outros":
                    new_description = st.text_area(
                        "Descrição obrigatória",
                        value=row.get("description", "")
                    )
                else:
                    new_description = row.get("description", "")

            # =========================
            # SUBMIT
            # =========================
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
