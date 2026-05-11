from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from finance_db import init_database
from finance_repository import execute_write, export_excel, load_categories, load_goals, load_transactions
from finance_ui import (
    MOVEMENT_TYPES,
    PEOPLE,
    apply_style,
    filter_data,
    financial_summary,
    list_header,
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
    st.markdown('<div class="form-caption">Regista salários ou despesas em poucos segundos.</div>', unsafe_allow_html=True)

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

    if st.button("Adicionar movimento", key=f"add_button_{page}", type="primary", use_container_width=True):
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


def edit_transaction_panel(page: str, page_df: pd.DataFrame, categories: list[str]) -> None:
    section_title("Editar ou remover movimento")

    options = {transaction_label(row): int(row["id"]) for _, row in page_df.iterrows()}
    selected_label = st.selectbox("Escolhe o movimento", list(options.keys()), key=f"select_transaction_{page}")
    selected_id = options[selected_label]
    selected_row = page_df[page_df["id"] == selected_id].iloc[0]

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
        if st.button("Guardar alterações", key=f"save_transaction_{page}_{selected_id}", type="primary", use_container_width=True):
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
        if st.button("Remover movimento", key=f"delete_transaction_{page}_{selected_id}", use_container_width=True):
            execute_write("DELETE FROM transactions WHERE id = :id", {"id": selected_id})
            st.success("Movimento removido.")
            st.rerun()


def render_money_line(title: str, meta: str, value: float, tone: str) -> None:
    value_class = "income" if tone == "income" else "expense"
    signal = "+" if tone == "income" else "-"

    st.markdown(
        f"""
        <div class="compact-movement-card">
            <div class="compact-row">
                <div>
                    <div class="compact-title">{escape(title)}</div>
                    <div class="movement-meta">{escape(meta)}</div>
                </div>
                <div class="{value_class}">{signal}{money(value)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_person_breakdown(person: str, person_df: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-title">Resumo {escape(person)}</div>', unsafe_allow_html=True)

    salary_df = person_df[person_df["type_normalized"] == "salário"]
    expense_df = person_df[person_df["type_normalized"] == "despesa"]

    col_salary, col_expense = st.columns(2)

    with col_salary:
        st.markdown('<div class="compact-panel-title salary-title">Salário</div>', unsafe_allow_html=True)

        if salary_df.empty:
            st.markdown('<div class="empty-mini-card">Sem salário registado.</div>', unsafe_allow_html=True)
        else:
            for _, row in salary_df.head(5).iterrows():
                render_money_line(
                    title="Salário",
                    meta=f"{person} · {row['date']}",
                    value=float(row["value"]),
                    tone="income",
                )

    with col_expense:
        st.markdown('<div class="compact-panel-title expense-title">Despesas</div>', unsafe_allow_html=True)

        if expense_df.empty:
            st.markdown('<div class="empty-mini-card">Sem despesas registadas.</div>', unsafe_allow_html=True)
        else:
            for _, row in expense_df.head(5).iterrows():
                category = str(row.get("category") or "Despesa")
                description = str(row.get("description") or "").strip()

                if category == "Outros" and description:
                    meta = f"Despesa · Outros · {description} · {row['date']}"
                else:
                    meta = f"Despesa · {category} · {row['date']}"

                render_money_line(
                    title=category,
                    meta=meta,
                    value=float(row["value"]),
                    tone="expense",
                )


def render_dashboard(filtered_df: pd.DataFrame) -> None:
    page_title("Casal", "Visão geral conjunta, simples e rápida das vossas contas.")
    summary_cards(filtered_df, "Saldo disponível")

    if filtered_df.empty:
        st.info("Não existem movimentos para os filtros escolhidos.")
        return

    for person in PEOPLE:
        person_df = filtered_df[filtered_df["person"] == person]
        render_person_breakdown(person, person_df)

    list_header("Últimos movimentos", min(len(filtered_df), 6))

    for _, row in filtered_df.head(6).iterrows():
        movement_card(row)


def render_person_page(page: str, filtered_df: pd.DataFrame, categories: list[str]) -> None:
    page_title(page, "Adicionar, consultar, editar e remover movimentos.")

    people = [page]
    page_df = filtered_df[filtered_df["person"].isin(people)] if not filtered_df.empty else pd.DataFrame()

    summary_cards(page_df)

    form_col, list_col = st.columns([0.95, 1.25])

    with form_col:
        add_transaction_form(page, people, categories)

    with list_col:
        list_header("Movimentos recentes", 0 if page_df.empty else min(len(page_df), 8))

        if page_df.empty:
            st.info("Sem movimentos para mostrar.")
        else:
            for _, row in page_df.head(8).iterrows():
                movement_card(row)

    if page_df.empty:
        return

    with st.expander("Ver tabela completa"):
        table_df = page_df[["person", "type", "category", "description", "value", "date"]].copy()
        table_df.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    edit_transaction_panel(page, page_df, categories)


def render_goals(goals_df: pd.DataFrame) -> None:
    page_title("Metas", "Acompanhar objetivos de forma simples.")
    section_title("Criar meta")

    name = st.text_input("Nome da meta")
    description = st.text_input("Descrição")
    target = st.number_input("Objetivo", min_value=0.0, step=10.0)
    current = st.number_input("Valor atual", min_value=0.0, step=10.0)

    if st.button("Criar meta", type="primary", use_container_width=True):
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
                        <div class="movement-title">{escape(str(goal['name']))}</div>
                        <div class="movement-meta">{escape(str(goal['description']))}</div>
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
            if st.button("Adicionar", key=f"add_goal_{goal_id}", use_container_width=True) and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = current_amount + :amount WHERE id = :id",
                    {"amount": amount, "id": goal_id},
                )
                st.success("Valor adicionado.")
                st.rerun()

        with col3:
            if st.button("Retirar", key=f"remove_goal_value_{goal_id}", use_container_width=True) and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = :value WHERE id = :id",
                    {"value": max(current_value - amount, 0), "id": goal_id},
                )
                st.success("Valor retirado.")
                st.rerun()

        with col4:
            if st.button("Remover", key=f"delete_goal_{goal_id}", use_container_width=True):
                execute_write("DELETE FROM goals WHERE id = :id", {"id": goal_id})
                st.success("Meta removida.")
                st.rerun()


def render_categories(categories_df: pd.DataFrame) -> None:
    page_title("Categorias", "Gerir categorias usadas nas despesas.")

    new_category = st.text_input("Nova categoria")

    if st.button("Adicionar categoria", type="primary", use_container_width=True):
        if not new_category.strip():
            st.error("Escreve o nome da categoria.")
        else:
            try:
                execute_write("INSERT INTO categories (name) VALUES (:name)", {"name": new_category.strip()})
                st.success("Categoria adicionada.")
                st.rerun()
            except Exception:
                st.error("Essa categoria já existe.")

    section_title("Categorias existentes")

    for _, category in categories_df.iterrows():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(
                f'<div class="movement-card"><div class="movement-title">{escape(str(category["name"]))}</div></div>',
                unsafe_allow_html=True,
            )

        with col2:
            if category["name"].lower() == "outros":
                st.caption("Protegida")
            elif st.button("Remover", key=f"remove_cat_{category['id']}", use_container_width=True):
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
        use_container_width=True,
    )


def main() -> None:
    st.sidebar.title("💰 Rubi & Gabi")
    st.sidebar.caption("Gestão financeira simples")

    page = st.sidebar.radio("Menu", ["Casal", "Ruben", "Gabi", "Metas", "Categorias", "Exportar"])

    transactions_df = load_transactions()
    filtered_df = filter_data(transactions_df)

    if page == "Casal":
        render_dashboard(filtered_df)
    elif page in ["Ruben", "Gabi"]:
        categories_df = load_categories()
        render_person_page(page, filtered_df, category_options(categories_df))
    elif page == "Metas":
        render_goals(load_goals())
    elif page == "Categorias":
        render_categories(load_categories())
    elif page == "Exportar":
        render_export(filtered_df)


if __name__ == "__main__":
    main()