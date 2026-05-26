from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from finance_db import init_database
from finance_repository import execute_write, export_excel, load_categories, load_goals, load_transactions
from finance_ui import MOVEMENT_TYPES, MONTHS, PEOPLE, apply_style, filter_data, money, page_title, sidebar_brand

st.set_page_config(page_title="Rubi & Gabi Finance", layout="wide", page_icon="€")
apply_style()
init_database()


def normalize_type_label(value: str) -> str:
    value_norm = str(value or "").strip().lower()
    if value_norm in {"salário", "salario", "subsídio de alimentação", "subsidio de alimentação", "subsídio alimentação"}:
        return "salário"
    return "despesa"


def ensure_outros(categories_df: pd.DataFrame) -> list[str]:
    categories = categories_df["name"].tolist() if not categories_df.empty else []
    if "Outros" not in categories:
        categories.append("Outros")
    return categories


def clear_and_refresh() -> None:
    for fn in (load_transactions, load_goals, load_categories):
        if hasattr(fn, "clear"):
            fn.clear()
    st.rerun()


def render_section_header(title: str, subtitle: str = "") -> None:
    subtitle_html = f"<div class='subtitle'>{escape(subtitle)}</div>" if subtitle else ""
    st.markdown(f"<div class='section-title'>{escape(title)}</div>{subtitle_html}", unsafe_allow_html=True)


def render_empty_state(message: str) -> None:
    st.markdown(f"<div class='empty-mini-card'>{escape(message)}</div>", unsafe_allow_html=True)


def render_metric_card(title: str, value: str, tone: str = "neutral", helper: str = "") -> None:
    helper_html = f"<div class='family-note'>{escape(helper)}</div>" if helper else ""
    st.markdown(
        f"""
        <div class="family-main-card {escape(tone)}-card compact-card">
            <div class="family-label">{escape(title)}</div>
            <div class="family-value {'income' if tone=='income' else 'expense' if tone=='expense' else 'neutral'}">{escape(value)}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(title: str, message: str, level: str) -> None:
    st.markdown(
        f"""
        <div class="status-badge status-{escape(level)}">
            <div class="family-label">{escape(title)}</div>
            <div class="family-note">{escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_movement_card(row: pd.Series) -> None:
    is_income = normalize_type_label(row.get("type")) == "salário"
    sign = "+" if is_income else "-"
    value_class = "income" if is_income else "expense"
    description = str(row.get("description") or "").strip()
    desc = f" · {escape(description)}" if description else ""
    st.markdown(
        f"""
        <div class="movement-card {'income-movement' if is_income else 'expense-movement'}">
            <div class="movement-top">
                <div>
                    <div class="movement-title">{escape(str(row.get('category') or row.get('type') or 'Movimento'))}</div>
                    <div class="movement-meta">{escape(str(row.get('date')))} · {escape(str(row.get('person')))}{desc}</div>
                </div>
                <div class="{value_class}">{sign}{money(row.get('value', 0))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def goal_message(progress: int) -> str:
    if progress >= 100:
        return "Meta atingida. Excelente trabalho!"
    if progress >= 75:
        return "Quase lá. Último esforço!"
    if progress >= 40:
        return "Bom ritmo. Mantém a consistência."
    return "Cada euro conta. Continua!"


def render_goal_card(goal: pd.Series, monthly_capacity: float, editable: bool = True) -> None:
    goal_id = int(goal["id"])
    target = float(goal["target_amount"])
    current = float(goal["current_amount"])
    progress = int(round((current / target) * 100)) if target > 0 else 0
    missing = max(target - current, 0)
    eta = "Concluída" if missing == 0 else f"~{max(1, int((missing / max(monthly_capacity, 1)) + 0.99))} mês(es)"
    st.markdown(
        f"""
        <div class="goal-card goal-card-rich">
            <div class="goal-title-row"><div class="goal-title">{escape(str(goal['name']))}</div><div class="goal-amount">{money(current)} / {money(target)}</div></div>
            <div class="goal-bottom-row"><span>Falta {money(missing)} · Previsão {eta}</span><strong>{escape(goal_message(progress))}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(max(progress, 0), 100) / 100)
    if not editable:
        return

    c1, c2, c3, c4 = st.columns([1.8, 1, 1, 1])
    with c1:
        amt = st.number_input("Valor", min_value=0.0, step=5.0, key=f"goal_amt_{goal_id}")
    with c2:
        if st.button("Adicionar", key=f"goal_add_{goal_id}", use_container_width=True) and amt > 0:
            execute_write("UPDATE goals SET current_amount = current_amount + :a WHERE id = :id", {"a": amt, "id": goal_id})
            clear_and_refresh()
    with c3:
        if st.button("Retirar", key=f"goal_sub_{goal_id}", use_container_width=True) and amt > 0:
            execute_write("UPDATE goals SET current_amount = :v WHERE id = :id", {"v": max(current - amt, 0), "id": goal_id})
            clear_and_refresh()
    with c4:
        if st.button("Eliminar", key=f"goal_del_{goal_id}", use_container_width=True):
            execute_write("DELETE FROM goals WHERE id = :id", {"id": goal_id})
            clear_and_refresh()


def render_person_dashboard(person: str, data: pd.DataFrame, categories: list[str]) -> None:
    page_title(person, "Resumo simples para agir sem confusão.")
    pdf = data[data["person"] == person].copy() if not data.empty else pd.DataFrame()
    income = pdf[pdf["type"].apply(normalize_type_label) == "salário"]["value"].sum() if not pdf.empty else 0
    expense = pdf[pdf["type"].apply(normalize_type_label) == "despesa"]["value"].sum() if not pdf.empty else 0
    balance = income - expense

    exp_df = pdf[pdf["type"].apply(normalize_type_label) == "despesa"] if not pdf.empty else pd.DataFrame()
    top_expense = exp_df.sort_values("value", ascending=False).iloc[0] if not exp_df.empty else None
    top_category = exp_df.groupby("category")["value"].sum().sort_values(ascending=False) if not exp_df.empty else pd.Series(dtype=float)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Dinheiro recebido", money(income), "income")
    with c2:
        render_metric_card("Dinheiro gasto", money(expense), "expense")
    with c3:
        render_metric_card("Saldo disponível", money(balance), "neutral")

    level = "healthy" if balance >= 0 else "warning"
    msg = "Estás bem este mês." if balance >= 0 else "Atenção: gastaste mais do que recebeste."
    render_status_badge("Estado financeiro", msg, level)

    d1, d2 = st.columns(2)
    with d1:
        if top_expense is None:
            render_metric_card("Maior gasto", "Sem despesas", "neutral")
        else:
            render_metric_card("Maior gasto", money(float(top_expense["value"])), "expense", str(top_expense["category"]))
    with d2:
        if top_category.empty:
            render_metric_card("Categoria com mais gastos", "Sem despesas", "neutral")
        else:
            render_metric_card("Categoria com mais gastos", top_category.index[0], "neutral", money(float(top_category.iloc[0])))

    c_form, c_recent = st.columns([1, 1.2])
    with c_form:
        render_section_header("Adicionar movimento")
        mtype = st.selectbox("Tipo de movimento", MOVEMENT_TYPES, key=f"add_type_{person}")
        cat = "Salário" if mtype != "Despesa" else st.selectbox("Categoria", categories, key=f"add_cat_{person}")
        desc = st.text_input("Descrição", key=f"add_desc_{person}") if cat == "Outros" else ""
        val = st.number_input("Valor", min_value=0.0, step=1.0, key=f"add_val_{person}")
        d = st.date_input("Data", value=date.today(), max_value=date.today(), key=f"add_date_{person}")
        if st.button("Adicionar movimento", key=f"add_btn_{person}", type="primary", use_container_width=True):
            if val <= 0:
                st.error("O valor tem de ser superior a zero.")
            elif cat == "Outros" and not desc.strip():
                st.error("Na categoria Outros, a descrição é obrigatória.")
            else:
                execute_write(
                    "INSERT INTO transactions (person,type,category,description,value,date,payment_source) VALUES (:p,:t,:c,:d,:v,:dt,:ps)",
                    {"p": person, "t": mtype, "c": ("Subsídio Alimentação" if mtype == "Subsídio de Alimentação" else cat), "d": desc.strip(), "v": val, "dt": str(d), "ps": "Salário"},
                )
                clear_and_refresh()
    with c_recent:
        render_section_header("Últimos movimentos")
        if pdf.empty:
            render_empty_state("Sem movimentos recentes.")
        else:
            for _, row in pdf.head(8).iterrows():
                render_movement_card(row)


def render_couple_dashboard(df: pd.DataFrame, goals_df: pd.DataFrame) -> None:
    page_title("Casal", "Visão rápida do mês da família.")
    if df.empty:
        render_empty_state("Sem movimentos para os filtros selecionados.")
        return

    income = df[df["type"].apply(normalize_type_label) == "salário"]["value"].sum()
    expense = df[df["type"].apply(normalize_type_label) == "despesa"]["value"].sum()
    balance = income - expense

    exp_df = df[df["type"].apply(normalize_type_label) == "despesa"]
    top = exp_df.sort_values("value", ascending=False).iloc[0] if not exp_df.empty else None
    top_cat_series = exp_df.groupby("category")["value"].sum().sort_values(ascending=False) if not exp_df.empty else pd.Series(dtype=float)

    state_text = "Estamos bem este mês." if balance >= 0 else "Este mês exige atenção."
    render_status_badge("Estado do mês", state_text, "healthy" if balance >= 0 else "warning")

    cols = st.columns(3)
    with cols[0]:
        render_metric_card("Entradas do mês", money(income), "income")
    with cols[1]:
        render_metric_card("Despesas do mês", money(expense), "expense")
    with cols[2]:
        render_metric_card("Saldo disponível", money(balance), "neutral")

    info = st.columns(2)
    with info[0]:
        if top is None:
            render_metric_card("Maior gasto", "Sem despesas", "neutral")
        else:
            render_metric_card("Maior gasto", money(float(top["value"])), "expense", str(top["category"]))
    with info[1]:
        if top_cat_series.empty:
            render_metric_card("Categoria com mais gastos", "Sem despesas", "neutral")
        else:
            render_metric_card("Categoria com mais gastos", top_cat_series.index[0], "neutral", money(float(top_cat_series.iloc[0])))

    render_section_header("Resumo rápido")
    top_line = "Maior gasto: Sem despesas"
    if top is not None:
        top_line = f"Maior gasto: {top['category']} — {money(float(top['value']))}"
    st.markdown(
        f"""
        <div class="empty-mini-card">
            <p>Entrou {money(income)}.</p>
            <p>Saiu {money(expense)}.</p>
            <p>Sobrou {money(balance)}.</p>
            <p>{escape(top_line)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_header("Metas da família", "Acompanhamento visual das metas em curso.")
    if goals_df.empty:
        render_empty_state("Sem metas ativas.")
    else:
        cap = max(balance * 0.25, 1)
        for _, g in goals_df.iterrows():
            render_goal_card(g, cap, editable=False)


def render_goals_page(goals_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Metas", "Zona de gestão completa das metas.")
    total_saved = goals_df["current_amount"].sum() if not goals_df.empty else 0
    total_target = goals_df["target_amount"].sum() if not goals_df.empty else 0
    total_missing = max(total_target - total_saved, 0)
    closest = "Sem metas"
    if not goals_df.empty:
        temp = goals_df.copy()
        temp["ratio"] = temp.apply(lambda r: (float(r["current_amount"]) / float(r["target_amount"])) if float(r["target_amount"]) > 0 else 0, axis=1)
        closest = str(temp.sort_values("ratio", ascending=False).iloc[0]["name"])

    cols = st.columns(4)
    with cols[0]: render_metric_card("Total guardado", money(total_saved), "income")
    with cols[1]: render_metric_card("Total em falta", money(total_missing), "expense")
    with cols[2]: render_metric_card("Metas ativas", str(len(goals_df)), "neutral")
    with cols[3]: render_metric_card("Meta mais próxima", closest, "neutral")

    render_section_header("Criar nova meta")
    n1, n2, n3 = st.columns(3)
    name = n1.text_input("Nome da meta")
    target = n2.number_input("Objetivo", min_value=0.0, step=10.0)
    current = n3.number_input("Valor atual", min_value=0.0, step=10.0)
    if st.button("Guardar meta", type="primary", use_container_width=True):
        if not name.strip() or target <= 0:
            st.error("Nome obrigatório e objetivo superior a zero.")
        else:
            execute_write("INSERT INTO goals (name,description,target_amount,current_amount) VALUES (:n,'',:t,:c)", {"n": name.strip(), "t": target, "c": current})
            clear_and_refresh()

    cap = max((tx_df[tx_df["type"].apply(normalize_type_label) == "salário"]["value"].sum() - tx_df[tx_df["type"].apply(normalize_type_label) == "despesa"]["value"].sum()) * 0.25, 1) if not tx_df.empty else 1
    for _, g in goals_df.iterrows():
        render_goal_card(g, cap, editable=True)


def render_categories_page(categories_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Categorias", "Gerir categorias de forma simples.")
    category_options = (categories_df["name"].tolist() if not categories_df.empty else ["Outros"]) + ["Adicionar categoria"]
    selected = st.selectbox("Selecionar categoria", category_options)

    if selected == "Adicionar categoria":
        new_cat = st.text_input("Nome")
        if st.button("Guardar", type="primary", use_container_width=True):
            if not new_cat.strip():
                st.error("Nome obrigatório.")
            else:
                try:
                    execute_write("INSERT INTO categories (name) VALUES (:n)", {"n": new_cat.strip()})
                    clear_and_refresh()
                except Exception:
                    st.error("Categoria já existe.")
        return

    c1, c2 = st.columns(2)
    with c1:
        edit_clicked = st.button("Editar", use_container_width=True)
    with c2:
        del_clicked = st.button("Eliminar", use_container_width=True)

    if edit_clicked:
        if selected == "Outros":
            st.warning("A categoria 'Outros' está bloqueada e não pode ser renomeada.")
        else:
            nn = st.text_input("Novo nome")
            if st.button("Guardar", key="save_edit_cat", type="primary", use_container_width=True):
                if not nn.strip():
                    st.error("Novo nome obrigatório.")
                else:
                    execute_write("UPDATE categories SET name=:n WHERE name=:s", {"n": nn.strip(), "s": selected})
                    clear_and_refresh()

    if del_clicked:
        st.warning("Confirma que queres eliminar esta categoria?")
        if selected == "Outros":
            st.error("A categoria 'Outros' está bloqueada e não pode ser eliminada.")
        else:
            exp_df = tx_df[tx_df["type"].apply(normalize_type_label) == "despesa"] if not tx_df.empty else pd.DataFrame()
            blocked = not exp_df.empty and selected in exp_df["category"].values
            if blocked:
                st.error("Categoria com movimentos associados não pode ser removida.")
            elif st.button("Eliminar categoria", key="confirm_delete_cat", type="primary", use_container_width=True):
                execute_write("DELETE FROM categories WHERE name=:s", {"s": selected})
                clear_and_refresh()


def render_export_page(df: pd.DataFrame) -> None:
    page_title("Exportar", "Exporta movimentos por período com resumo rápido.")
    today = date.today()
    years = sorted(df["year"].dropna().astype(int).unique().tolist(), reverse=True) if not df.empty else [today.year]
    if today.year not in years:
        years.insert(0, today.year)

    filters = st.columns(2)
    with filters[0]:
        y = st.selectbox("Ano", years)
    with filters[1]:
        month_names = [m for m in MONTHS if m != "Todos"]
        m_name = st.selectbox("Mês", month_names, index=today.month - 1)

    m = MONTHS[m_name]
    mdf = df[(df["year"] == int(y)) & (df["month"] == int(m))] if not df.empty else pd.DataFrame()
    inc = mdf[mdf["type"].apply(normalize_type_label) == "salário"]["value"].sum() if not mdf.empty else 0
    exp = mdf[mdf["type"].apply(normalize_type_label) == "despesa"]["value"].sum() if not mdf.empty else 0
    bal = inc - exp

    cards = st.columns(4)
    with cards[0]: render_metric_card("Número de movimentos", str(len(mdf)), "neutral")
    with cards[1]: render_metric_card("Entradas", money(inc), "income")
    with cards[2]: render_metric_card("Despesas", money(exp), "expense")
    with cards[3]: render_metric_card("Saldo", money(bal), "neutral")

    if not mdf.empty:
        st.download_button(
            f"Exportar {m_name} {y}",
            export_excel(mdf[["id", "person", "type", "category", "description", "value", "date"]]),
            f"movimentos_{y}_{m:02d}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.dataframe(mdf[["person", "type", "category", "description", "value", "date"]], use_container_width=True, hide_index=True)
    else:
        render_empty_state("Sem movimentos no período selecionado.")


def main() -> None:
    sidebar_brand()
    st.markdown(
        """
        <style>
        .stButton > button {color: #ffffff !important; background: #1f6feb !important; border: 1px solid #1f6feb !important;}
        .stButton > button:hover {color: #ffffff !important; background: #195cc0 !important; border-color: #195cc0 !important;}
        .stButton > button:active {color: #ffffff !important; background: #144a9a !important; border-color: #144a9a !important;}
        .stButton > button:disabled {color: #d1d5db !important; background: #9ca3af !important; border-color: #9ca3af !important;}
        .status-badge {padding: 0.7rem 1rem; border-radius: 0.8rem; margin-bottom: 0.8rem; border: 1px solid #dbeafe;}
        .status-healthy {background: #ecfdf3;}
        .status-warning {background: #fff7ed;}
        .compact-card {box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08) !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    page = st.sidebar.radio("Menu", ["Casal", "Ruben", "Gabi", "Metas", "Categorias", "Exportar"], label_visibility="collapsed")
    tx = load_transactions()
    goals = load_goals()
    categories = load_categories()
    filtered = filter_data(tx) if page in ["Casal", "Ruben", "Gabi"] else tx

    if page == "Casal":
        render_couple_dashboard(filtered, goals)
    elif page in PEOPLE:
        render_person_dashboard(page, filtered, ensure_outros(categories))
    elif page == "Metas":
        render_goals_page(goals, tx)
    elif page == "Categorias":
        render_categories_page(categories, tx)
    elif page == "Exportar":
        render_export_page(tx)


if __name__ == "__main__":
    main()
