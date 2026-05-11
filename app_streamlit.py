from datetime import date

import pandas as pd
import streamlit as st

from finance_db import init_database
from finance_repository import execute_write, export_excel, load_categories, load_goals, load_transactions
from finance_ui import (
    MOVEMENT_TYPES,
    PEOPLE,
    apply_style,
    card,
    expense_bar_chart,
    filter_data,
    financial_summary,
    money,
    movement_card,
    page_title,
    section_title,
    summary_cards,
    transaction_label,
)

st.set_page_config(page_title="Rubi & Gabi Finance", layout="wide", page_icon="💰")
apply_style()
init_database()


def category_options(categories_df: pd.DataFrame) -> list[str]:
    categories = categories_df["name"].tolist() if not categories_df.empty else []
    return categories if "Outros" in categories else [*categories, "Outros"]


def add_transaction_form(page: str, people: list[str], categories: list[str]) -> None:
    section_title("Adicionar movimento")
    with st.container():
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            person = st.selectbox("Pessoa", people, key=f"add_person_{page}")
        with col2:
            movement_type = st.selectbox("Tipo", MOVEMENT_TYPES, key=f"add_type_{page}")

        category = "Salário"
        description = ""
        if movement_type == "Despesa":
            category = st.selectbox("Categoria", categories, key=f"add_category_{page}")
            if category == "Outros":
                description = st.text_input("Descrição obrigatória", key=f"add_description_{page}")

        col3, col4 = st.columns(2)
        with col3:
            value = st.number_input("Valor", min_value=0.0, step=1.0, key=f"add_value_{page}")
        with col4:
            movement_date = st.date_input("Data", value=date.today(), max_value=date.today(), key=f"add_date_{page}")

        if st.button("Adicionar movimento", key=f"add_button_{page}"):
            if value <= 0:
                st.error("O valor tem de ser superior a zero.")
            elif movement_type == "Despesa" and category == "Outros" and not description.strip():
                st.error("Na categoria Outros, a descrição é obrigatória.")
            else:
                execute_write(
                    """
                    INSERT INTO transactions
                    (person, type, category, description, value, date)
                    VALUES
                    (:person, :type, :category, :description, :value, :date)
                    """,
                    {
                        "person": person,
                        "type": movement_type,
                        "category": category,
                        "description": description.strip(),
                        "value": value,
                        "date": str(movement_date),
                    },
                )
                st.success("Movimento adicionado.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def edit_transaction_panel(page: str, page_df: pd.DataFrame, categories: list[str]) -> None:
    section_title("Editar ou remover movimento")
    options = {transaction_label(row): int(row["id"]) for _, row in page_df.iterrows()}
    selected_label = st.selectbox("Escolhe o movimento", list(options.keys()), key=f"select_transaction_{page}")
    selected_id = options[selected_label]
    selected_row = page_df[page_df["id"] == selected_id].iloc[0]

    st.markdown('<div class="clean-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        edit_person = st.selectbox(
            "Pessoa",
            PEOPLE,
            index=PEOPLE.index(selected_row["person"]) if selected_row["person"] in PEOPLE else 0,
            key=f"edit_person_{page}_{selected_id}",
        )
    with col2:
        edit_type = st.selectbox(
            "Tipo",
            MOVEMENT_TYPES,
            index=MOVEMENT_TYPES.index(selected_row["type"]) if selected_row["type"] in MOVEMENT_TYPES else 0,
            key=f"edit_type_{page}_{selected_id}",
        )

    edit_category = "Salário"
    edit_description = ""
    if edit_type == "Despesa":
        edit_category = st.selectbox(
            "Categoria",
            categories,
            index=categories.index(selected_row["category"]) if selected_row["category"] in categories else 0,
            key=f"edit_category_{page}_{selected_id}",
        )
        if edit_category == "Outros":
            edit_description = st.text_input(
                "Descrição obrigatória",
                value=str(selected_row["description"] or ""),
                key=f"edit_description_{page}_{selected_id}",
            )

    col3, col4 = st.columns(2)
    with col3:
        edit_value = st.number_input(
            "Valor",
            min_value=0.0,
            step=1.0,
            value=float(selected_row["value"]),
            key=f"edit_value_{page}_{selected_id}",
        )
    with col4:
        edit_date = st.date_input(
            "Data",
            value=pd.to_datetime(selected_row["date"]).date(),
            max_value=date.today(),
            key=f"edit_date_{page}_{selected_id}",
        )

    col_save, col_delete = st.columns(2)
    with col_save:
        if st.button("Guardar alterações", key=f"save_transaction_{page}_{selected_id}"):
            if edit_value <= 0:
                st.error("O valor tem de ser superior a zero.")
            elif edit_type == "Despesa" and edit_category == "Outros" and not edit_description.strip():
                st.error("Na categoria Outros, a descrição é obrigatória.")
            else:
                execute_write(
                    """
                    UPDATE transactions
                    SET person = :person,
                        type = :type,
                        category = :category,
                        description = :description,
                        value = :value,
                        date = :date
                    WHERE id = :id
                    """,
                    {
                        "id": selected_id,
                        "person": edit_person,
                        "type": edit_type,
                        "category": edit_category,
                        "description": edit_description.strip(),
                        "value": edit_value,
                        "date": str(edit_date),
                    },
                )
                st.success("Movimento atualizado.")
                st.rerun()

    with col_delete:
        if st.button("Remover movimento", key=f"delete_transaction_{page}_{selected_id}"):
            execute_write("DELETE FROM transactions WHERE id = :id", {"id": selected_id})
            st.success("Movimento removido.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(filtered_df: pd.DataFrame) -> None:
    page_title("Dashboard", "Visão geral simples das vossas contas.")
    summary_cards(filtered_df, "Saldo disponível")

    if filtered_df.empty:
        st.info("Não existem movimentos para os filtros escolhidos.")
        return

    expenses_df = filtered_df[filtered_df["type_normalized"] == "despesa"]
    section_title("Resumo rápido")
    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)
        st.markdown("#### Para onde foi o dinheiro")
        if expenses_df.empty:
            st.info("Sem despesas.")
        else:
            st.plotly_chart(expense_bar_chart(expenses_df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)
        st.markdown("#### Por pessoa")
        for person in PEOPLE:
            person_df = filtered_df[filtered_df["person"] == person]
            income, expense, balance = financial_summary(person_df)
            st.markdown(
                f"""
                <div class="movement-card">
                    <div class="movement-top">
                        <div>
                            <div class="movement-title">{person}</div>
                            <div class="movement-meta">Receitas {money(income)} · Despesas {money(expense)}</div>
                        </div>
                        <div class="income">{money(balance)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    section_title("Últimos movimentos")
    for _, row in filtered_df.head(6).iterrows():
        movement_card(row)


def render_person_page(page: str, filtered_df: pd.DataFrame, categories: list[str]) -> None:
    page_title(page, "Adicionar, consultar, editar e remover movimentos.")
    people = PEOPLE if page == "Casal" else [page]
    add_transaction_form(page, people, categories)

    page_df = filtered_df[filtered_df["person"].isin(people)] if not filtered_df.empty else pd.DataFrame()
    summary_cards(page_df)
    section_title("Movimentos recentes")

    if page_df.empty:
        st.info("Sem movimentos para mostrar.")
        return

    for _, row in page_df.head(8).iterrows():
        movement_card(row)

    with st.expander("Ver tabela completa"):
        table_df = page_df[["person", "type", "category", "description", "value", "date"]].copy()
        table_df.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    edit_transaction_panel(page, page_df, categories)


def render_goals(goals_df: pd.DataFrame) -> None:
    page_title("Metas", "Acompanhar objetivos de forma simples.")
    section_title("Criar meta")

    with st.container():
        st.markdown('<div class="clean-box">', unsafe_allow_html=True)
        name = st.text_input("Nome da meta")
        description = st.text_input("Descrição")
        target = st.number_input("Objetivo", min_value=0.0, step=10.0)
        current = st.number_input("Valor atual", min_value=0.0, step=10.0)

        if st.button("Criar meta"):
            if not name.strip():
                st.error("O nome é obrigatório.")
            elif target <= 0:
                st.error("O objetivo tem de ser superior a zero.")
            else:
                execute_write(
                    """
                    INSERT INTO goals
                    (name, description, target_amount, current_amount)
                    VALUES
                    (:name, :description, :target_amount, :current_amount)
                    """,
                    {
                        "name": name.strip(),
                        "description": description.strip(),
                        "target_amount": target,
                        "current_amount": current,
                    },
                )
                st.success("Meta criada.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    section_title("Metas existentes")
    if goals_df.empty:
        st.info("Ainda não existem metas.")
        return

    for _, goal in goals_df.iterrows():
        target_value = float(goal["target_amount"])
        current_value = float(goal["current_amount"])
        progress = min(current_value / target_value, 1) if target_value > 0 else 0

        st.markdown(
            f"""
            <div class="clean-box">
                <div class="movement-top">
                    <div>
                        <div class="movement-title">{goal['name']}</div>
                        <div class="movement-meta">{goal['description']}</div>
                    </div>
                    <div class="income">{money(current_value)} / {money(target_value)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(progress)

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        goal_id = int(goal["id"])
        with col1:
            amount = st.number_input("Valor", min_value=0.0, step=5.0, key=f"goal_amount_{goal_id}")
        with col2:
            if st.button("Adicionar", key=f"add_goal_{goal_id}") and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = current_amount + :amount WHERE id = :id",
                    {"amount": amount, "id": goal_id},
                )
                st.success("Valor adicionado.")
                st.rerun()
        with col3:
            if st.button("Retirar", key=f"remove_goal_value_{goal_id}") and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = :value WHERE id = :id",
                    {"value": max(current_value - amount, 0), "id": goal_id},
                )
                st.success("Valor retirado.")
                st.rerun()
        with col4:
            if st.button("Remover", key=f"delete_goal_{goal_id}"):
                execute_write("DELETE FROM goals WHERE id = :id", {"id": goal_id})
                st.success("Meta removida.")
                st.rerun()


def render_categories(categories_df: pd.DataFrame) -> None:
    page_title("Categorias", "Gerir categorias usadas nas despesas.")
    st.markdown('<div class="clean-box">', unsafe_allow_html=True)
    new_category = st.text_input("Nova categoria")

    if st.button("Adicionar categoria"):
        if not new_category.strip():
            st.error("Escreve o nome da categoria.")
        else:
            try:
                execute_write("INSERT INTO categories (name) VALUES (:name)", {"name": new_category.strip()})
                st.success("Categoria adicionada.")
                st.rerun()
            except Exception:
                st.error("Essa categoria já existe.")

    st.markdown("</div>", unsafe_allow_html=True)
    section_title("Categorias existentes")

    for _, category in categories_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f'<div class="movement-card"><div class="movement-title">{category["name"]}</div></div>', unsafe_allow_html=True)
        with col2:
            if category["name"].lower() == "outros":
                st.caption("Protegida")
            elif st.button("Remover", key=f"remove_cat_{category['id']}"):
                execute_write("DELETE FROM categories WHERE id = :id", {"id": int(category["id"])})
                st.success("Categoria removida.")
                st.rerun()


def render_export(filtered_df: pd.DataFrame) -> None:
    page_title("Exportar", "Descarregar movimentos em Excel.")
    if filtered_df.empty:
        st.info("Não existem dados para exportar.")
        return

    export_columns = ["person", "type", "category", "description", "value", "date"]
    export_view = filtered_df[export_columns].copy()
    export_view.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]
    st.dataframe(export_view, use_container_width=True, hide_index=True)

    st.download_button(
        label="Descarregar Excel",
        data=export_excel(filtered_df[["id"] + export_columns]),
        file_name="movimentos_financeiros.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def main() -> None:
    transactions_df = load_transactions()
    categories_df = load_categories()
    goals_df = load_goals()
    categories = category_options(categories_df)

    st.sidebar.title("💰 Rubi & Gabi")
    page = st.sidebar.radio("Menu", ["Dashboard", "Ruben", "Gabi", "Casal", "Metas", "Categorias", "Exportar"])
    filtered_df = filter_data(transactions_df)

    if page == "Dashboard":
        render_dashboard(filtered_df)
    elif page in ["Ruben", "Gabi", "Casal"]:
        render_person_page(page, filtered_df, categories)
    elif page == "Metas":
        render_goals(goals_df)
    elif page == "Categorias":
        render_categories(categories_df)
    elif page == "Exportar":
        render_export(filtered_df)


if __name__ == "__main__":
    main()
