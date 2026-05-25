from __future__ import annotations

from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.express as px
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
        <div class="family-main-card {escape(tone)}-card">
            <div class="family-label">{escape(title)}</div>
            <div class="family-value {'income' if tone=='income' else 'expense' if tone=='expense' else 'neutral'}">{escape(value)}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(title: str, message: str, level: str) -> None:
    st.markdown(
        f"""
        <div class="couple-hero hero-{escape(level)}">
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


def render_goal_card(goal: pd.Series, monthly_capacity: float) -> None:
    goal_id = int(goal["id"])
    target = float(goal["target_amount"])
    current = float(goal["current_amount"])
    progress = int(round((current / target) * 100)) if target > 0 else 0
    missing = max(target - current, 0)
    eta = "Concluída" if missing == 0 else f"~{max(1, int((missing / max(monthly_capacity,1)) + 0.99))} mês(es)"
    st.markdown(
        f"""
        <div class="goal-card goal-card-rich">
            <div class="goal-title-row"><div class="goal-title">{escape(str(goal['name']))}</div><div class="goal-amount">{money(current)} / {money(target)}</div></div>
            <div class="goal-bottom-row"><span>{progress}% · Falta {money(missing)} · Previsão {eta}</span><strong>{escape(goal_message(progress))}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
    page_title(person, "Resumo individual claro, diário e acionável.")
    pdf = data[data["person"] == person].copy() if not data.empty else pd.DataFrame()
    income = pdf[pdf["type"].apply(normalize_type_label) == "salário"]["value"].sum() if not pdf.empty else 0
    expense = pdf[pdf["type"].apply(normalize_type_label) == "despesa"]["value"].sum() if not pdf.empty else 0
    balance = income - expense
    expense_rate = (expense / income * 100) if income > 0 else 0.0

    cols = st.columns(4)
    with cols[0]: render_metric_card("Rendimento total", money(income), "income")
    with cols[1]: render_metric_card("Despesas", money(expense), "expense")
    with cols[2]: render_metric_card("Saldo disponível", money(balance), "neutral")
    with cols[3]: render_metric_card("% rendimento gasto", f"{expense_rate:.1f}%", "neutral")

    render_status_banner("Estado financeiro", "Positivo" if balance >= 0 else "Em atenção", "healthy" if balance > 0 else "warning")

    if not pdf.empty:
        flow = pdf.copy()
        flow["signed"] = flow.apply(lambda r: r["value"] if normalize_type_label(r["type"]) == "salário" else -r["value"], axis=1)
        fig = px.bar(flow.sort_values("date"), x="date", y="signed", color="type", title="Fluxo financeiro")
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns([1, 1.2])
    with c1:
        render_section_header("Adicionar movimento")
        mtype = st.selectbox("Tipo", MOVEMENT_TYPES, key=f"add_type_{person}")
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
                execute_write("INSERT INTO transactions (person,type,category,description,value,date,payment_source) VALUES (:p,:t,:c,:d,:v,:dt,:ps)",
                              {"p": person, "t": mtype, "c": ("Subsídio Alimentação" if mtype=="Subsídio de Alimentação" else cat), "d": desc.strip(), "v": val, "dt": str(d), "ps": "Salário"})
                clear_and_refresh()
    with c2:
        render_section_header("Movimentos recentes")
        if pdf.empty:
            render_empty_state("Sem movimentos recentes.")
        else:
            for _, row in pdf.head(8).iterrows():
                render_movement_card(row)


def render_couple_dashboard(df: pd.DataFrame, goals_df: pd.DataFrame) -> None:
    page_title("Casal", "Página principal do mês com foco em decisões rápidas.")
    if df.empty:
        render_empty_state("Sem movimentos para os filtros selecionados.")
        return
    income = df[df["type"].apply(normalize_type_label) == "salário"]["value"].sum()
    expense = df[df["type"].apply(normalize_type_label) == "despesa"]["value"].sum()
    balance = income - expense
    savings_rate = (max(balance, 0) / income * 100) if income > 0 else 0.0

    state = "healthy" if balance > 0 and savings_rate >= 15 else "warning" if balance >= 0 else "danger"
    render_status_banner("Estado financeiro do mês", f"Saldo {money(balance)} · Taxa poupança {savings_rate:.1f}%", state)

    c = st.columns(4)
    with c[0]: render_metric_card("Entradas", money(income), "income")
    with c[1]: render_metric_card("Despesas", money(expense), "expense")
    with c[2]: render_metric_card("Margem", money(balance), "neutral")
    with c[3]: render_metric_card("Taxa de poupança", f"{savings_rate:.1f}%", "neutral")

    exp_df = df[df["type"].apply(normalize_type_label) == "despesa"]
    if not exp_df.empty:
        top = exp_df.sort_values("value", ascending=False).iloc[0]
        cat = exp_df.groupby("category")["value"].sum().sort_values(ascending=False)
        top_cat = cat.index[0]
        top_cat_val = float(cat.iloc[0])
        total = float(expense) if expense else 1.0
        x1, x2 = st.columns(2)
        with x1:
            render_metric_card("Maior despesa", f"{money(top['value'])} ({(top['value']/total*100):.1f}%)", "expense", f"{top['category']} · {top['person']}")
        with x2:
            render_metric_card("Categoria com mais gastos", f"{money(top_cat_val)} ({(top_cat_val/total*100):.1f}%)", "expense", str(top_cat))

    render_section_header("Metas da família")
    if goals_df.empty:
        render_empty_state("Sem metas ativas.")
    else:
        cap = max(balance * 0.25, 1)
        for _, g in goals_df.iterrows():
            render_goal_card(g, cap)


def render_goals_page(goals_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Metas", "Motivação diária para transformar objetivos em realidade.")
    total_saved = goals_df["current_amount"].sum() if not goals_df.empty else 0
    total_target = goals_df["target_amount"].sum() if not goals_df.empty else 0
    total_missing = max(total_target - total_saved, 0)
    avg_progress = ((total_saved / total_target) * 100) if total_target > 0 else 0
    cols = st.columns(4)
    with cols[0]: render_metric_card("Total guardado", money(total_saved), "income")
    with cols[1]: render_metric_card("Total em falta", money(total_missing), "expense")
    with cols[2]: render_metric_card("Metas ativas", str(len(goals_df)), "neutral")
    with cols[3]: render_metric_card("Progresso médio", f"{avg_progress:.1f}%", "neutral")

    render_section_header("Criar nova meta")
    n1, n2, n3 = st.columns(3)
    name = n1.text_input("Nome")
    target = n2.number_input("Objetivo", min_value=0.0, step=10.0)
    current = n3.number_input("Atual", min_value=0.0, step=10.0)
    if st.button("Guardar meta", type="primary", use_container_width=True):
        if not name.strip() or target <= 0:
            st.error("Nome obrigatório e objetivo superior a zero.")
        else:
            execute_write("INSERT INTO goals (name,description,target_amount,current_amount) VALUES (:n,'',:t,:c)", {"n": name.strip(), "t": target, "c": current})
            clear_and_refresh()

    cap = max((tx_df[tx_df["type"].apply(normalize_type_label) == "salário"]["value"].sum() - tx_df[tx_df["type"].apply(normalize_type_label) == "despesa"]["value"].sum()) * 0.25, 1) if not tx_df.empty else 1
    for _, g in goals_df.iterrows():
        render_goal_card(g, cap)


def render_categories_page(categories_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Categorias", "Gestão premium de categorias e uso.")
    exp_df = tx_df[tx_df["type"].apply(normalize_type_label) == "despesa"] if not tx_df.empty else pd.DataFrame()
    total_exp = exp_df["value"].sum() if not exp_df.empty else 0
    usage = exp_df.groupby("category").agg(total=("value", "sum"), count=("id", "count")) if not exp_df.empty else pd.DataFrame()
    for _, c in categories_df.iterrows():
        name = c["name"]
        total = float(usage.loc[name, "total"]) if not usage.empty and name in usage.index else 0
        count = int(usage.loc[name, "count"]) if not usage.empty and name in usage.index else 0
        pct = (total / total_exp * 100) if total_exp > 0 else 0
        status = "Usada" if count > 0 else "Sem uso"
        st.markdown(f"<div class='category-grid-card'><div class='category-name'>{escape(str(name))}</div><div class='small-muted'>{money(total)} · {count} mov. · {pct:.1f}% · {status}</div></div>", unsafe_allow_html=True)

    sel = st.selectbox("Selecionar categoria", categories_df["name"].tolist() if not categories_df.empty else ["Outros"])
    nn = st.text_input("Novo nome")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Renomear", use_container_width=True):
            if sel == "Outros": st.error("Não podes renomear 'Outros'.")
            elif not nn.strip(): st.error("Novo nome obrigatório.")
            else:
                execute_write("UPDATE categories SET name=:n WHERE name=:s", {"n": nn.strip(), "s": sel})
                clear_and_refresh()
    with c2:
        if st.button("Eliminar", use_container_width=True):
            if sel == "Outros":
                st.error("Não podes eliminar 'Outros'.")
            elif not exp_df.empty and sel in exp_df["category"].values:
                st.error("Categoria com movimentos associados não pode ser removida.")
            else:
                execute_write("DELETE FROM categories WHERE name=:s", {"s": sel})
                clear_and_refresh()
    with c3:
        new_cat = st.text_input("Nova categoria")
        if st.button("Adicionar categoria", type="primary", use_container_width=True):
            if not new_cat.strip(): st.error("Nome obrigatório.")
            else:
                try:
                    execute_write("INSERT INTO categories (name) VALUES (:n)", {"n": new_cat.strip()})
                    clear_and_refresh()
                except Exception:
                    st.error("Categoria já existe.")


def render_export_page(df: pd.DataFrame) -> None:
    page_title("Exportar", "Exportação profissional por mês.")
    today = date.today()
    years = sorted(df["year"].dropna().astype(int).unique().tolist(), reverse=True) if not df.empty else [today.year]
    if today.year not in years:
        years.insert(0, today.year)
    month_names = [m for m in MONTHS if m != "Todos"]
    y = st.selectbox("Ano", years)
    m_name = st.selectbox("Mês", month_names, index=today.month - 1)
    m = MONTHS[m_name]
    mdf = df[(df["year"] == int(y)) & (df["month"] == int(m))] if not df.empty else pd.DataFrame()
    inc = mdf[mdf["type"].apply(normalize_type_label) == "salário"]["value"].sum() if not mdf.empty else 0
    exp = mdf[mdf["type"].apply(normalize_type_label) == "despesa"]["value"].sum() if not mdf.empty else 0
    bal = inc - exp
    render_metric_card("Movimentos", str(len(mdf)), "neutral")
    render_metric_card("Entradas", money(inc), "income")
    render_metric_card("Despesas", money(exp), "expense")
    render_metric_card("Saldo", money(bal), "neutral")
    st.info("Mês em curso." if int(y) == today.year and int(m) == today.month else "Mês fechado para análise.")
    if not mdf.empty:
        st.download_button(f"Exportar {m_name} {y}", export_excel(mdf[["id", "person", "type", "category", "description", "value", "date"]]), f"movimentos_{y}_{m:02d}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.dataframe(mdf[["person", "type", "category", "description", "value", "date"]], use_container_width=True, hide_index=True)


def main() -> None:
    sidebar_brand()
    page = st.sidebar.radio("Menu", ["Casal", "Ruben", "Gabi", "Metas", "Categorias", "Exportar"], label_visibility="collapsed")
    tx = load_transactions()
    goals = load_goals()
    categories = load_categories()
    if page in ["Casal", "Ruben", "Gabi"]:
        filtered = filter_data(tx)
    else:
        filtered = tx

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
