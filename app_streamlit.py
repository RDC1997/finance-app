from __future__ import annotations

from datetime import date
from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st

from finance_db import init_database
from finance_repository import execute_write, load_categories, load_goals, load_transactions
from finance_ui import MONTHS, PEOPLE, apply_style, money, page_title, sidebar_brand

st.set_page_config(page_title="Rubi & Gabi Finance", layout="wide", page_icon="€")
apply_style()
init_database()

INCOME_TYPES = {
    "salário",
    "salario",
    "subsídio de alimentação",
    "subsidio de alimentação",
    "subsídio alimentação",
    "subsidio alimentação",
}
MOVEMENT_TYPES = ["Salário", "Subsídio de alimentação", "Despesa"]
EXPENSE_LABEL = "Despesa"
ADD_CATEGORY_OPTION = "+ Adicionar categoria"
PROTECTED_CATEGORY = "Outros"


def normalize_type_label(value: str) -> str:
    value_norm = str(value or "").strip().lower()
    return "entrada" if value_norm in INCOME_TYPES else "despesa"


def is_income(value: str) -> bool:
    return normalize_type_label(value) == "entrada"


def ensure_outros(categories_df: pd.DataFrame) -> list[str]:
    categories = categories_df["name"].dropna().astype(str).tolist() if not categories_df.empty else []
    if PROTECTED_CATEGORY not in categories:
        categories.append(PROTECTED_CATEGORY)
    unique_categories = dict.fromkeys(category.strip() for category in categories if category and category.strip())
    return sorted(unique_categories, key=lambda item: (item == PROTECTED_CATEGORY, item.lower()))


def clear_and_refresh() -> None:
    for fn in (load_transactions, load_goals, load_categories):
        if hasattr(fn, "clear"):
            fn.clear()
    st.rerun()


def format_date_pt(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "Sem data"
    return parsed.strftime("%d/%m/%Y")


def render_section_header(title: str, subtitle: str = "") -> None:
    subtitle_html = f"<div class='subtitle'>{escape(subtitle)}</div>" if subtitle else ""
    st.markdown(f"<div class='section-title'>{escape(title)}</div>{subtitle_html}", unsafe_allow_html=True)


def render_empty_state(message: str) -> None:
    st.markdown(f"<div class='empty-mini-card'>{escape(message)}</div>", unsafe_allow_html=True)


def render_metric_card(title: str, value: str, tone: str = "neutral", helper: str = "") -> None:
    tone_class = {
        "income": "income-card",
        "expense": "expense-card",
        "info": "available-card",
        "positive": "income-card",
        "warning": "expense-card",
        "neutral": "mint-card",
    }.get(tone, "mint-card")
    value_class = "income" if tone in {"income", "positive"} else "expense" if tone in {"expense", "warning"} else "neutral"
    helper_html = f"<div class='family-note'>{escape(helper)}</div>" if helper else ""
    st.markdown(
        f"""
        <div class="family-main-card {tone_class} compact-finance-card">
            <div class="family-label">{escape(title)}</div>
            <div class="family-value {value_class}">{escape(value)}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_row(rows: list[tuple[str, str]]) -> None:
    rows_html = "".join(
        f"<div class='quick-summary-row'><span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in rows
    )
    st.markdown(f"<div class='quick-summary-card'>{rows_html}</div>", unsafe_allow_html=True)


def render_main_balance_card(
    title: str,
    value: float,
    subtitle: str,
    positive_text: str,
    negative_text: str,
    amount_subtitle: str = "",
) -> None:
    positive = value >= 0
    level = "positive-card" if positive else "negative-card"
    message = positive_text if positive else negative_text
    amount_subtitle_html = f"<div class='hero-amount-subtitle'>{escape(amount_subtitle)}</div>" if amount_subtitle else ""
    st.markdown(
        f"""
        <div class="finance-hero-card {level}">
            <div>
                <div class="hero-micro">{escape(title)}</div>
                <div class="hero-title">{escape(message)}</div>
                <div class="hero-subtitle">{escape(subtitle)}</div>
            </div>
            <div class="hero-amount-block">
                <div class="hero-amount">{escape(money(value))}</div>
                {amount_subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def goal_progress(current: float, target: float) -> int:
    return int(round((current / target) * 100)) if target > 0 else 0


def goal_colour(progress: int, missing: float) -> str:
    if missing <= 0 or progress >= 75:
        return "#059669"
    return "#2563eb"


def goal_message(progress: int, missing: float) -> str:
    if missing <= 0 or progress >= 100:
        return "Meta atingida. Excelente trabalho!"
    if progress >= 75:
        return "Muito perto. Falta pouco."
    if progress >= 40:
        return "Bom progresso. Continua assim."
    return "Ainda no início, mas já conta."


def estimated_goal_time(missing: float, monthly_capacity: float) -> str:
    if missing <= 0:
        return "Concluída"
    if monthly_capacity <= 0:
        return "Sem previsão"
    months = max(1, int((missing / monthly_capacity) + 0.99))
    return f"cerca de {months} mês" if months == 1 else f"cerca de {months} meses"


def render_goal_progress_bar(progress: int, missing: float, label: str = "Progresso") -> None:
    safe_progress = min(max(progress, 0), 100)
    colour = goal_colour(safe_progress, missing)
    st.markdown(
        f"""
        <div class="goal-progress-wrap">
            <div class="goal-progress-meta">
                <span class="goal-progress-label">{escape(label)}</span>
                <span class="goal-progress-percent">{safe_progress}%</span>
            </div>
            <div class="goal-progress-track">
                <div class="goal-progress-fill" style="width: {safe_progress}%; background: {colour};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_goal_card(goal: pd.Series, monthly_capacity: float, editable: bool = True) -> None:
    goal_id = int(goal["id"])
    name = str(goal["name"])
    target = float(goal["target_amount"])
    current = float(goal["current_amount"])
    progress = goal_progress(current, target)
    safe_progress = min(max(progress, 0), 100)
    missing = max(target - current, 0)
    eta = estimated_goal_time(missing, monthly_capacity)
    monthly_need = "Sem previsão"
    if missing <= 0:
        monthly_need = "Meta concluída"
    elif monthly_capacity > 0:
        months = max(1, int((missing / monthly_capacity) + 0.99))
        monthly_need = money(missing / months)

    progress_label = "Progresso" if editable else "Caminho até à meta"
    progress_colour = goal_colour(safe_progress, missing)
    st.markdown(
        f"""
        <div class="goal-card goal-card-rich clean-goal-card premium-goal-card">
            <div class="goal-title-row">
                <div>
                    <div class="goal-title">{escape(name)}</div>
                    <div class="goal-bottom-row"><span>{escape(goal_message(progress, missing))}</span></div>
                </div>
                <div class="goal-amount">{escape(str(safe_progress))}%</div>
            </div>
            <div class="goal-stats-grid">
                <div><span>Atual</span><strong>{escape(money(current))}</strong></div>
                <div><span>Objetivo</span><strong>{escape(money(target))}</strong></div>
                <div><span>Em falta</span><strong>{escape(money(missing))}</strong></div>
                <div><span>Previsão</span><strong>{escape(eta)}</strong></div>
                <div><span>Média necessária/mês</span><strong>{escape(monthly_need)}</strong></div>
            </div>
            <div class="goal-progress-wrap">
                <div class="goal-progress-meta">
                    <span class="goal-progress-label">{escape(progress_label)}</span>
                    <span class="goal-progress-percent">{safe_progress}%</span>
                </div>
                <div class="goal-progress-track">
                    <div class="goal-progress-fill" style="width: {safe_progress}%; background: {progress_colour};"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not editable:
        return

    if st.session_state.get(f"confirm_goal_delete_{goal_id}"):
        st.warning(f"Queres mesmo eliminar a meta “{name}”? Esta ação não pode ser desfeita.")
        c1, c2, c3 = st.columns([1.2, 1, 3])
        with c1:
            st.markdown("<div class='danger-action-marker'></div>", unsafe_allow_html=True)
            if st.button("Eliminar definitivamente", key=f"goal_delete_yes_{goal_id}", use_container_width=True):
                execute_write("DELETE FROM goals WHERE id = :id", {"id": goal_id})
                st.session_state.pop(f"confirm_goal_delete_{goal_id}", None)
                clear_and_refresh()
        with c2:
            if st.button("Cancelar", key=f"goal_delete_no_{goal_id}", use_container_width=True):
                st.session_state.pop(f"confirm_goal_delete_{goal_id}", None)
                st.rerun()
        return

    with st.form(f"goal_form_{goal_id}", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1.15, 1.1, 1.1, .85])
        with c1:
            amount = st.number_input("Valor", min_value=0.0, step=5.0, key=f"goal_amount_{goal_id}")
        with c2:
            st.markdown("<div class='success-action-marker'></div>", unsafe_allow_html=True)
            add_submitted = st.form_submit_button("Adicionar valor à meta", type="primary", use_container_width=True)
        with c3:
            st.markdown("<div class='info-action-marker'></div>", unsafe_allow_html=True)
            remove_submitted = st.form_submit_button("Retirar valor da meta", use_container_width=True)
        with c4:
            delete_submitted = st.form_submit_button("Pedir eliminação", use_container_width=True)

    if add_submitted:
        if amount <= 0:
            st.error("Indica um valor superior a zero.")
        else:
            execute_write("UPDATE goals SET current_amount = current_amount + :amount WHERE id = :id", {"amount": amount, "id": goal_id})
            clear_and_refresh()
    if remove_submitted:
        if amount <= 0:
            st.error("Indica um valor superior a zero.")
        else:
            execute_write("UPDATE goals SET current_amount = :value WHERE id = :id", {"value": max(current - amount, 0), "id": goal_id})
            clear_and_refresh()
    if delete_submitted:
        st.session_state[f"confirm_goal_delete_{goal_id}"] = True
        st.rerun()

def display_type_for_edit(value: str) -> str:
    clean = str(value or "").strip().lower()
    if clean in {"subsídio de alimentação", "subsidio de alimentação", "subsídio alimentação", "subsidio alimentação"}:
        return "Subsídio de alimentação"
    if clean in {"salário", "salario"}:
        return "Salário"
    return EXPENSE_LABEL


def movement_defaults_for_type(movement_type: str, category: str) -> tuple[str, str]:
    if movement_type == EXPENSE_LABEL:
        return movement_type, category or PROTECTED_CATEGORY
    if movement_type == "Subsídio de alimentação":
        return movement_type, "Subsídio de alimentação"
    return movement_type, "Salário"


def save_transaction(person: str, movement_type: str, category: str, description: str, value: float, movement_date: date) -> bool:
    final_type, final_category = movement_defaults_for_type(movement_type, category)
    if value <= 0:
        st.error("O valor tem de ser superior a zero.")
        return False
    if movement_date > date.today():
        st.error("A data não pode ser futura.")
        return False
    if final_type == EXPENSE_LABEL and final_category == PROTECTED_CATEGORY and not description.strip():
        st.error("Na categoria Outros, a descrição é obrigatória.")
        return False

    execute_write(
        """
        INSERT INTO transactions (person,type,category,description,value,date,payment_source)
        VALUES (:person,:type,:category,:description,:value,:date,:payment_source)
        """,
        {
            "person": person,
            "type": final_type,
            "category": final_category,
            "description": description.strip() if final_type == EXPENSE_LABEL and final_category == PROTECTED_CATEGORY else "",
            "value": value,
            "date": str(movement_date),
            "payment_source": "Salário",
        },
    )
    return True


def update_transaction(transaction_id: int, movement_type: str, category: str, description: str, value: float, movement_date: date) -> bool:
    final_type, final_category = movement_defaults_for_type(movement_type, category)
    if value <= 0:
        st.error("O valor tem de ser superior a zero.")
        return False
    if movement_date > date.today():
        st.error("A data não pode ser futura.")
        return False
    if final_type == EXPENSE_LABEL and final_category == PROTECTED_CATEGORY and not description.strip():
        st.error("Na categoria Outros, a descrição é obrigatória.")
        return False
    execute_write(
        """
        UPDATE transactions
        SET type = :type, category = :category, description = :description, value = :value, date = :date
        WHERE id = :id
        """,
        {
            "id": transaction_id,
            "type": final_type,
            "category": final_category,
            "description": description.strip() if final_type == EXPENSE_LABEL and final_category == PROTECTED_CATEGORY else "",
            "value": value,
            "date": str(movement_date),
        },
    )
    return True


def render_add_movement_form(person: str, categories: list[str]) -> None:
    st.markdown("<div class='form-shell-title'>Registar novo movimento</div>", unsafe_allow_html=True)
    with st.container(border=True):
        movement_type = st.selectbox("Tipo de movimento", MOVEMENT_TYPES, key=f"add_type_{person}")
        category = ""
        description = ""

        if movement_type == EXPENSE_LABEL:
            category = st.selectbox("Categoria", categories, key=f"add_category_{person}")
            if category == PROTECTED_CATEGORY:
                description = st.text_input("Descrição obrigatória", key=f"add_description_{person}")

        c1, c2 = st.columns(2)
        with c1:
            value = st.number_input("Valor", min_value=0.0, step=1.0, key=f"add_value_{person}")
        with c2:
            movement_date = st.date_input("Data", value=date.today(), max_value=date.today(), key=f"add_date_{person}")

        marker = "success-action-marker" if movement_type != EXPENSE_LABEL else "danger-action-marker"
        label = "Registar entrada" if movement_type != EXPENSE_LABEL else "Registar despesa"
        st.markdown(f"<div class='{marker}'></div>", unsafe_allow_html=True)
        submitted = st.button(label, key=f"submit_add_transaction_{person}", use_container_width=True)
        if submitted and save_transaction(person, movement_type, category, description, value, movement_date):
            clear_and_refresh()

def render_movement_card(row: pd.Series, categories: list[str] | None = None, editable: bool = False) -> None:
    income_row = is_income(row.get("type"))
    sign = "+" if income_row else "-"
    value_class = "income" if income_row else "expense"
    movement_class = "income-movement" if income_row else "expense-movement"
    movement_type = "Entrada" if income_row else "Despesa"
    category = str(row.get("category") or row.get("type") or "Movimento")
    description = str(row.get("description") or "").strip()
    desc = f" · {escape(description)}" if description else ""
    transaction_id = int(row.get("id"))

    st.markdown(
        f"""
        <div class="movement-card compact-list-card {movement_class}">
            <div class="movement-top compact-card-row">
                <div class="compact-card-main">
                    <div class="movement-title">{escape(category)}</div>
                    <div class="movement-meta">{escape(format_date_pt(row.get('date')))} · {escape(str(row.get('person')))} · {escape(movement_type)}{desc}</div>
                </div>
                <div class="{value_class} compact-card-value">{sign}{escape(money(row.get('value', 0)))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not editable or categories is None:
        return

    action_cols = st.columns([1, 1, 4])
    with action_cols[0]:
        if st.button("Editar", key=f"show_edit_transaction_{transaction_id}", use_container_width=True):
            st.session_state[f"edit_transaction_{transaction_id}"] = True
            st.session_state.pop(f"confirm_transaction_delete_{transaction_id}", None)
            st.rerun()
    with action_cols[1]:
        if st.button("Eliminar", key=f"ask_delete_transaction_{transaction_id}", use_container_width=True):
            st.session_state[f"confirm_transaction_delete_{transaction_id}"] = True
            st.session_state.pop(f"edit_transaction_{transaction_id}", None)
            st.rerun()

    if st.session_state.get(f"confirm_transaction_delete_{transaction_id}"):
        st.warning(f"Queres mesmo eliminar este movimento de {money(row.get('value', 0))}? Esta ação não pode ser desfeita.")
        c1, c2, c3 = st.columns([1.2, 1, 3])
        with c1:
            st.markdown("<div class='danger-action-marker'></div>", unsafe_allow_html=True)
            if st.button("Confirmar eliminação", key=f"delete_transaction_yes_{transaction_id}", use_container_width=True):
                execute_write("DELETE FROM transactions WHERE id = :id", {"id": transaction_id})
                st.session_state.pop(f"confirm_transaction_delete_{transaction_id}", None)
                clear_and_refresh()
        with c2:
            if st.button("Cancelar", key=f"delete_transaction_no_{transaction_id}", use_container_width=True):
                st.session_state.pop(f"confirm_transaction_delete_{transaction_id}", None)
                st.rerun()
        return

    if not st.session_state.get(f"edit_transaction_{transaction_id}"):
        return

    with st.container(border=True):
        current_type = display_type_for_edit(str(row.get("type") or ""))
        movement_type = st.selectbox("Tipo de movimento", MOVEMENT_TYPES, index=MOVEMENT_TYPES.index(current_type), key=f"edit_type_{transaction_id}")
        edit_category = PROTECTED_CATEGORY
        edit_description = ""
        if movement_type == EXPENSE_LABEL:
            current_category = category if category in categories else PROTECTED_CATEGORY
            edit_category = st.selectbox("Categoria", categories, index=categories.index(current_category), key=f"edit_category_{transaction_id}")
            if edit_category == PROTECTED_CATEGORY:
                edit_description = st.text_input("Descrição obrigatória", value=description, key=f"edit_description_{transaction_id}")
        c1, c2 = st.columns(2)
        with c1:
            edit_value = st.number_input("Valor", min_value=0.0, step=1.0, value=float(row.get("value", 0)), key=f"edit_value_{transaction_id}")
        with c2:
            parsed_date = pd.to_datetime(row.get("date"), errors="coerce")
            default_date = parsed_date.date() if not pd.isna(parsed_date) else date.today()
            edit_date = st.date_input("Data", value=min(default_date, date.today()), max_value=date.today(), key=f"edit_date_{transaction_id}")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("<div class='success-action-marker'></div>", unsafe_allow_html=True)
            saved = st.button("Guardar alteração", key=f"save_transaction_{transaction_id}", use_container_width=True)
        with c4:
            cancelled = st.button("Cancelar edição", key=f"cancel_edit_transaction_{transaction_id}", use_container_width=True)

        if saved and update_transaction(transaction_id, movement_type, edit_category, edit_description, edit_value, edit_date):
            st.session_state.pop(f"edit_transaction_{transaction_id}", None)
            clear_and_refresh()
        if cancelled:
            st.session_state.pop(f"edit_transaction_{transaction_id}", None)
            st.rerun()

def summarize_money(df: pd.DataFrame) -> tuple[float, float, float]:
    if df.empty:
        return 0.0, 0.0, 0.0
    income = float(df[df["type"].apply(is_income)]["value"].sum())
    expense = float(df[~df["type"].apply(is_income)]["value"].sum())
    return income, expense, income - expense


def top_expense_and_category(df: pd.DataFrame) -> tuple[pd.Series | None, pd.Series]:
    expenses = df[~df["type"].apply(is_income)].copy() if not df.empty else pd.DataFrame()
    top = expenses.sort_values("value", ascending=False).iloc[0] if not expenses.empty else None
    top_category = expenses.groupby("category")["value"].sum().sort_values(ascending=False) if not expenses.empty else pd.Series(dtype=float)
    return top, top_category


def render_person_page(person: str, data: pd.DataFrame, categories: list[str]) -> None:
    page_title(person, "Resumo individual para veres o essencial e registares movimentos rapidamente.")
    pdf = data[data["person"] == person].copy() if not data.empty else pd.DataFrame()
    income, expense, balance = summarize_money(pdf)
    top_expense, _ = top_expense_and_category(pdf)

    render_main_balance_card(
        "Saldo disponível",
        balance,
        f"Gastaste {money(expense)} este mês.",
        f"Tens {money(balance)} disponíveis",
        f"Faltam {money(abs(balance))} para equilibrar o mês",
        "Saldo disponível",
    )

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_metric_card("Recebido", money(income), "income")
    with summary_cols[1]:
        render_metric_card("Gasto", money(expense), "expense")
    with summary_cols[2]:
        render_metric_card("Saldo", money(balance), "info")
    with summary_cols[3]:
        if top_expense is None:
            render_metric_card("Movimentos", str(len(pdf)), "neutral")
        else:
            render_metric_card("Maior saída", money(float(top_expense["value"])), "expense", str(top_expense["category"]))

    quick_cols = st.columns([1, 1])
    with quick_cols[0]:
        render_section_header("Leitura rápida", "O essencial da página individual.")
        last_text = "Sem movimentos" if pdf.empty else f"{pdf.iloc[0]['category']} — {money(float(pdf.iloc[0]['value']))}"
        top_line = "Sem despesas" if top_expense is None else f"{top_expense['category']} — {money(float(top_expense['value']))}"
        rows = [
            ("Total recebido", money(income)),
            ("Total gasto", money(expense)),
            ("Movimentos", str(len(pdf))),
            ("Último movimento", last_text),
            ("Maior saída", top_line),
        ]
        render_summary_row(rows)
    with quick_cols[1]:
        render_add_movement_form(person, categories)

    render_section_header("Últimos movimentos", "Cartões compactos com ações discretas.")
    if pdf.empty:
        render_empty_state("Sem movimentos recentes.")
    else:
        for _, row in pdf.head(8).iterrows():
            render_movement_card(row, categories=categories, editable=True)

def render_quick_summary(rows: list[tuple[str, str]]) -> None:
    render_summary_row(rows)


def render_couple_dashboard(df: pd.DataFrame, goals_df: pd.DataFrame) -> None:
    page_title("Casal", "Dashboard principal da família para acompanhar o mês num relance.")
    income, expense, balance = summarize_money(df)
    top, _ = top_expense_and_category(df)
    savings_rate = (balance / income * 100) if income > 0 else 0.0
    available_rate = max(balance / income * 100, 0) if income > 0 else 0.0

    render_main_balance_card(
        "Estado financeiro do mês",
        balance,
        f"Sobraram {money(balance)} depois das despesas." if balance >= 0 else f"As despesas passaram as entradas em {money(abs(balance))}.",
        "O mês está positivo",
        "O mês precisa de atenção",
        "Saldo disponível",
    )

    cols = st.columns(5)
    with cols[0]:
        render_metric_card("Recebido", money(income), "income")
    with cols[1]:
        render_metric_card("Gasto", money(expense), "expense")
    with cols[2]:
        render_metric_card("Saldo disponível", money(balance), "info")
    with cols[3]:
        render_metric_card("Taxa de poupança", f"{savings_rate:.0f}%", "info")
    with cols[4]:
        render_metric_card("Movimentos", str(len(df)), "neutral")

    top_line = "Sem despesas registadas" if top is None else f"{top['category']} — {money(float(top['value']))}"
    if top is not None:
        top_cols = st.columns([1, 1])
        with top_cols[0]:
            render_metric_card("Maior saída", money(float(top["value"])), "expense", str(top["category"]))

    render_section_header("Leitura rápida do mês", "Resumo em linguagem simples para decidir o próximo passo.")
    quick_rows = [
        ("Estado do mês", "Está positivo e equilibrado." if balance >= 0 else "Precisa de atenção porque as despesas ultrapassaram as entradas."),
        ("Dinheiro disponível", f"Ainda está disponível {available_rate:.0f}% do dinheiro recebido." if income > 0 else "Ainda não há entradas registadas neste filtro."),
        ("Maior saída", top_line),
        ("Atividade", f"Foram registados {len(df)} movimentos no período selecionado."),
    ]
    render_quick_summary(quick_rows)

    render_section_header("Metas da família", "Acompanhamento claro das metas em curso.")
    if goals_df.empty:
        render_empty_state("Sem metas ativas. Cria uma meta na página Metas para começar a acompanhar objetivos.")
    else:
        monthly_capacity = max(balance * 0.25, 0)
        for _, goal in goals_df.iterrows():
            render_goal_card(goal, monthly_capacity, editable=False)

def render_goals_page(goals_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Metas", "Zona principal para acompanhar, reforçar e gerir objetivos.")
    total_saved = float(goals_df["current_amount"].sum()) if not goals_df.empty else 0.0
    total_target = float(goals_df["target_amount"].sum()) if not goals_df.empty else 0.0
    total_missing = max(total_target - total_saved, 0)
    closest = "Sem metas"
    closest_helper = ""
    if not goals_df.empty:
        temp = goals_df.copy()
        temp["missing"] = (temp["target_amount"].astype(float) - temp["current_amount"].astype(float)).clip(lower=0)
        temp["ratio"] = temp.apply(lambda row: float(row["current_amount"]) / float(row["target_amount"]) if float(row["target_amount"]) > 0 else 0, axis=1)
        closest_row = temp.sort_values(["missing", "ratio"], ascending=[True, False]).iloc[0]
        closest = str(closest_row["name"])
        closest_helper = f"Falta {money(float(closest_row['missing']))}"

    render_section_header("Resumo das metas")
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("Total guardado", money(total_saved), "income")
    with cols[1]:
        render_metric_card("Total em falta", money(total_missing), "info")
    with cols[2]:
        render_metric_card("Metas ativas", str(len(goals_df)), "neutral")
    with cols[3]:
        render_metric_card("Meta mais próxima", closest, "info", closest_helper)

    _, _, balance = summarize_money(tx_df)
    monthly_capacity = max(balance * 0.25, 0)

    render_section_header("Lista de metas existentes")
    if goals_df.empty:
        render_empty_state("Ainda não há metas. Cria a primeira abaixo.")
    else:
        for _, goal in goals_df.iterrows():
            render_goal_card(goal, monthly_capacity, editable=True)

    with st.expander("+ Criar nova meta", expanded=False):
        st.caption("Usa quando quiseres acrescentar um novo objetivo.")
        with st.container(border=True):
            with st.form("create_goal", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    name = st.text_input("Nome da meta")
                with c2:
                    target = st.number_input("Objetivo", min_value=0.0, step=10.0)
                with c3:
                    current = st.number_input("Valor atual", min_value=0.0, step=10.0)
                st.markdown("<div class='success-action-marker'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Guardar meta", type="primary", use_container_width=True)
            if submitted:
                if not name.strip() or target <= 0:
                    st.error("Indica o nome da meta e um objetivo superior a zero.")
                else:
                    execute_write(
                        "INSERT INTO goals (name,description,target_amount,current_amount) VALUES (:name,'',:target,:current)",
                        {"name": name.strip(), "target": target, "current": current},
                    )
                    clear_and_refresh()


def set_category_mode(mode: str | None, selected: str | None = None) -> None:
    if mode is None:
        st.session_state.pop("category_mode", None)
        st.session_state.pop("category_mode_selected", None)
        return
    st.session_state["category_mode"] = mode
    st.session_state["category_mode_selected"] = selected


def render_categories_page(categories_df: pd.DataFrame, tx_df: pd.DataFrame) -> None:
    page_title("Categorias", "Organiza as despesas de forma simples, limpa e protegida.")
    categories = ensure_outros(categories_df)
    expenses = tx_df[~tx_df["type"].apply(is_income)].copy() if not tx_df.empty else pd.DataFrame()
    current_month = date.today().month
    current_year = date.today().year
    month_expenses = expenses[(expenses["month"] == current_month) & (expenses["year"] == current_year)] if not expenses.empty else pd.DataFrame()

    render_section_header("Categorias", "Lista simples para consultar e gerir sem ruído visual.")
    category_rows_html = []
    for category in categories:
        movement_count = int((expenses["category"] == category).sum()) if not expenses.empty else 0
        month_total = float(month_expenses[month_expenses["category"] == category]["value"].sum()) if not month_expenses.empty else 0.0
        protected = category == PROTECTED_CATEGORY
        category_rows_html.append(
            f"""
            <div class="category-list-row {'protected-category' if protected else ''}">
                <div>
                    <div class="category-name">{escape(category)}</div>
                    <div class="category-muted">{movement_count} movimentos · {escape(money(month_total))} gastos este mês</div>
                </div>
                <div class="category-lock">{'Protegida' if protected else 'Editável'}</div>
            </div>
            """
        )
    st.markdown(f"<div class='category-list-panel'>{''.join(category_rows_html)}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        render_section_header("Gerir categoria", "Seleciona uma categoria para ver ações disponíveis ou adiciona uma nova.")
        options = categories + [ADD_CATEGORY_OPTION]
        selected = st.selectbox("Selecionar categoria", options, key="selected_category")

        if selected == ADD_CATEGORY_OPTION:
            with st.form("add_category_form", clear_on_submit=True):
                new_name = st.text_input("Nome")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='success-action-marker'></div>", unsafe_allow_html=True)
                    saved = st.form_submit_button("Guardar categoria", type="primary", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("Cancelar", use_container_width=True)
            if saved:
                clean_name = new_name.strip()
                if not clean_name:
                    st.error("Indica o nome da categoria.")
                elif clean_name.lower() in {cat.lower() for cat in categories}:
                    st.error("Essa categoria já existe.")
                else:
                    execute_write("INSERT INTO categories (name) VALUES (:name)", {"name": clean_name})
                    set_category_mode(None)
                    clear_and_refresh()
            if cancelled:
                set_category_mode(None)
                st.rerun()
            return

        affected = int((tx_df["category"] == selected).sum()) if not tx_df.empty and "category" in tx_df.columns else 0
        selected_month_total = float(month_expenses[month_expenses["category"] == selected]["value"].sum()) if not month_expenses.empty else 0.0
        st.markdown(
            f"""
            <div class='selected-movement-card selected-category-panel'>
                <div class='selected-movement-eyebrow'>Categoria selecionada</div>
                <div class='selected-movement-title'>{escape(selected)}</div>
                <div class='movement-meta'>{affected} movimentos associados · {escape(money(selected_month_total))} gastos este mês</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if selected == PROTECTED_CATEGORY:
            st.info("A categoria Outros é obrigatória e não pode ser eliminada.")
            return

        mode = st.session_state.get("category_mode")
        mode_selected = st.session_state.get("category_mode_selected")
        if mode_selected != selected:
            mode = None

        if mode not in {"edit", "delete", "view"}:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Editar nome", use_container_width=True):
                    set_category_mode("edit", selected)
                    st.rerun()
            with c2:
                if st.button("Ver movimentos", use_container_width=True, disabled=affected == 0):
                    set_category_mode("view", selected)
                    st.rerun()
            with c3:
                if st.button("Eliminar", use_container_width=True):
                    set_category_mode("delete", selected)
                    st.rerun()
            return

        if mode == "view":
            related = tx_df[tx_df["category"] == selected].head(8) if not tx_df.empty else pd.DataFrame()
            if related.empty:
                render_empty_state("Sem movimentos associados a esta categoria.")
            else:
                for _, row in related.iterrows():
                    render_movement_card(row, editable=False)
            if st.button("Fechar movimentos", use_container_width=True):
                set_category_mode(None)
                st.rerun()
            return

        if mode == "edit":
            with st.form("edit_category_form"):
                new_name = st.text_input("Novo nome", value=selected)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='success-action-marker'></div>", unsafe_allow_html=True)
                    saved = st.form_submit_button("Guardar alteração", type="primary", use_container_width=True)
                with c2:
                    cancelled = st.form_submit_button("Cancelar", use_container_width=True)
            if saved:
                clean_name = new_name.strip()
                if not clean_name:
                    st.error("Indica o novo nome.")
                elif clean_name == PROTECTED_CATEGORY:
                    st.error("O nome Outros está reservado.")
                elif clean_name.lower() in {cat.lower() for cat in categories if cat != selected}:
                    st.error("Já existe uma categoria com esse nome.")
                else:
                    execute_write("UPDATE categories SET name = :new_name WHERE name = :old_name", {"new_name": clean_name, "old_name": selected})
                    execute_write("UPDATE transactions SET category = :new_name WHERE category = :old_name", {"new_name": clean_name, "old_name": selected})
                    set_category_mode(None)
                    clear_and_refresh()
            if cancelled:
                set_category_mode(None)
                st.rerun()
            return

        if affected:
            st.warning(f"Ao eliminar, {affected} movimento(s) desta categoria passam para Outros para manter o histórico.")
        else:
            st.warning("Queres mesmo eliminar esta categoria? Esta ação não pode ser desfeita.")
        with st.form("delete_category_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='danger-action-marker'></div>", unsafe_allow_html=True)
                confirmed = st.form_submit_button("Eliminar definitivamente", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("Cancelar", use_container_width=True)
        if confirmed:
            execute_write("UPDATE transactions SET category = :fallback WHERE category = :category", {"fallback": PROTECTED_CATEGORY, "category": selected})
            execute_write("DELETE FROM categories WHERE name = :category", {"category": selected})
            set_category_mode(None)
            clear_and_refresh()
        if cancelled:
            set_category_mode(None)
            st.rerun()

def export_table_pt(df: pd.DataFrame, *, format_value: bool = False) -> pd.DataFrame:
    columns = ["person", "type", "category", "description", "value", "date"]
    export_df = df[[col for col in columns if col in df.columns]].copy()
    export_df = export_df.rename(
        columns={
            "person": "Pessoa",
            "type": "Tipo",
            "category": "Categoria",
            "description": "Descrição",
            "value": "Valor",
            "date": "Data",
        }
    )
    if "Valor" in export_df.columns:
        numeric_values = pd.to_numeric(export_df["Valor"], errors="coerce").fillna(0).round(2)
        export_df["Valor"] = numeric_values.apply(money) if format_value else numeric_values
    if "Data" in export_df.columns:
        export_df["Data"] = export_df["Data"].apply(format_date_pt)
    return export_df


def dataframe_to_csv(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def dataframe_to_excel(dataframe: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Movimentos")
    return output.getvalue()


def render_export_page(df: pd.DataFrame) -> None:
    page_title("Exportar", "Filtra o período, confirma o resumo e descarrega os movimentos.")
    today = date.today()
    years = sorted(df["year"].dropna().astype(int).unique().tolist(), reverse=True) if not df.empty else [today.year]
    if today.year not in years:
        years.insert(0, today.year)

    with st.sidebar.container(border=True):
        st.markdown('<div class="sidebar-section-label">Filtros rápidos</div>', unsafe_allow_html=True)
        year = st.selectbox("Ano", ["Todos"] + years, key="export_year")
        month_name = st.selectbox("Mês", list(MONTHS.keys()), index=today.month, key="export_month")
        person = st.selectbox("Pessoa", ["Todos"] + PEOPLE, key="export_person")

    export_df = df.copy() if not df.empty else pd.DataFrame()
    if not export_df.empty and year != "Todos":
        export_df = export_df[export_df["year"] == int(year)]
    month = MONTHS[month_name]
    if not export_df.empty and month != 0:
        export_df = export_df[export_df["month"] == int(month)]
    if person != "Todos" and not export_df.empty:
        export_df = export_df[export_df["person"] == person]

    if year == "Todos" and month_name == "Todos":
        period_text = "Todos os períodos"
    elif year == "Todos":
        period_text = f"{month_name}, todos os anos"
    elif month_name == "Todos":
        period_text = f"Ano {year}"
    else:
        period_text = f"{month_name} de {year}"
    person_text = "todas as pessoas" if person == "Todos" else person

    st.markdown(
        f"""
        <div class="export-period-card">
            <div class="selected-movement-eyebrow">Período selecionado</div>
            <div class="selected-movement-title">{escape(period_text)}</div>
            <div class="movement-meta">Inclui {escape(person_text)}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    income, expense, balance = summarize_money(export_df)
    cards = st.columns(4)
    with cards[0]:
        render_metric_card("Movimentos registados", str(len(export_df)), "neutral")
    with cards[1]:
        render_metric_card("Recebido", money(income), "income")
    with cards[2]:
        render_metric_card("Gasto", money(expense), "expense")
    with cards[3]:
        render_metric_card("Saldo", money(balance), "info")

    render_section_header("Pré-visualização dos movimentos")
    if export_df.empty:
        st.markdown(
            f"""
            <div class="export-empty-state">
                <div class="export-empty-icon">⬇</div>
                <div>
                    <div class="export-empty-title">Sem movimentos para exportar</div>
                    <div class="export-empty-text">Não existem movimentos em {escape(period_text)} para {escape(person_text)}. Ajusta os filtros ou seleciona Todos para preparar o ficheiro.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.button("Exportar Excel", disabled=True, use_container_width=True)
        with c2:
            st.button("Exportar CSV", disabled=True, use_container_width=True)
        return

    visible_df = export_table_pt(export_df, format_value=True)
    excel_df = export_table_pt(export_df, format_value=False)
    safe_person = person.lower().replace(" ", "_") if person != "Todos" else "todos"
    safe_year = str(year).lower()
    safe_month = f"{month:02d}" if month else "todos"
    file_suffix = f"{safe_year}_{safe_month}_{safe_person}"
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Exportar Excel",
            dataframe_to_excel(excel_df),
            f"movimentos_{file_suffix}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Exportar CSV",
            dataframe_to_csv(visible_df),
            f"movimentos_{file_suffix}.csv",
            "text/csv",
            use_container_width=True,
        )
    st.dataframe(visible_df, use_container_width=True, hide_index=True)

def filter_transactions(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        with st.sidebar.container(border=True):
            st.markdown('<div class="sidebar-section-label">Filtros rápidos</div>', unsafe_allow_html=True)
            st.selectbox("Pessoa", ["Todos"] + PEOPLE, disabled=True)
            st.selectbox("Ano", [date.today().year], disabled=True)
            st.selectbox("Mês", list(MONTHS.keys()), disabled=True)
            st.text_input("Pesquisar movimentos", disabled=True)
        return dataframe

    filtered = dataframe.copy()
    with st.sidebar.container(border=True):
        st.markdown('<div class="sidebar-section-label">Filtros rápidos</div>', unsafe_allow_html=True)
        selected_person = st.selectbox("Pessoa", ["Todos"] + PEOPLE, key="filter_person")
        if selected_person != "Todos":
            filtered = filtered[filtered["person"] == selected_person]

        years = sorted(filtered["year"].dropna().astype(int).unique().tolist(), reverse=True)
        if not years:
            years = [date.today().year]
        selected_year = st.selectbox("Ano", ["Todos"] + years, key="filter_year")
        if selected_year != "Todos":
            filtered = filtered[filtered["year"] == int(selected_year)]

        selected_month = st.selectbox("Mês", list(MONTHS.keys()), key="filter_month")
        if MONTHS[selected_month] != 0:
            filtered = filtered[filtered["month"] == MONTHS[selected_month]]

        search = st.text_input("Pesquisar movimentos", key="filter_search")
        if search.strip():
            term = search.strip().lower()
            searchable = filtered[["description", "category", "type", "person"]].fillna("").agg(" ".join, axis=1).str.lower()
            filtered = filtered[searchable.str.contains(term, regex=False)]

    return filtered


def inject_app_polish() -> None:
    """Compatibility hook: all visual rules live in finance_ui.CSS.

    Keeping this function avoids touching the app flow while preventing a
    second stylesheet from reintroducing top overlays or page gradients.
    """
    return None

def main() -> None:
    sidebar_brand()
    inject_app_polish()

    menu_options = ["Casal", "Ruben", "Gabi", "Metas", "Categorias", "Exportar"]
    menu_labels = {
        "Casal": "👫 Casal",
        "Ruben": "👤 Ruben",
        "Gabi": "👤 Gabi",
        "Metas": "🎯 Metas",
        "Categorias": "🏷️ Categorias",
        "Exportar": "⬇️ Exportar",
    }
    page = st.sidebar.radio("Menu", menu_options, format_func=lambda item: menu_labels[item], label_visibility="collapsed")
    transactions = load_transactions()
    goals = load_goals()
    categories = load_categories()
    filtered = filter_transactions(transactions) if page in ["Casal", "Ruben", "Gabi"] else transactions

    if page == "Casal":
        render_couple_dashboard(filtered, goals)
    elif page in PEOPLE:
        render_person_page(page, filtered, ensure_outros(categories))
    elif page == "Metas":
        render_goals_page(goals, transactions)
    elif page == "Categorias":
        render_categories_page(categories, transactions)
    elif page == "Exportar":
        render_export_page(transactions)


if __name__ == "__main__":
    main()
