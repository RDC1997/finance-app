from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finance_db import init_database
from finance_repository import execute_write, export_excel, load_categories, load_goals, load_transactions
from finance_ui import (
    MOVEMENT_TYPES,
    MONTHS,
    PEOPLE,
    apply_style,
    category_label,
    category_tone_class,
    filter_data,
    financial_summary,
    list_header,
    money,
    movement_card,
    page_title,
    section_title,
    sidebar_brand,
    summary_cards,
    transaction_label,
)

st.set_page_config(page_title="Rubi & Gabi Finance", layout="wide", page_icon="€")
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
    payment_source = "Salário"

    if movement_type == "Despesa":
        category = st.selectbox("Categoria", categories, key=f"add_category_{page}")
        is_food_category = category.strip().lower() in {"comida", "alimentação", "alimentacao"}
        if is_food_category:
            payment_source = st.selectbox(
                "Pago com",
                ["Salário", "Cartão alimentação"],
                key=f"add_payment_source_{page}",
            )

        if category == "Outros":
            description = st.text_input("Descrição obrigatória", key=f"add_description_{page}")

    col3, col4 = st.columns(2)

    with col3:
        value = st.number_input("Valor", min_value=0.0, step=1.0, key=f"add_value_{page}")

    with col4:
        movement_date = st.date_input("Data", value=date.today(), max_value=date.today(), key=f"add_date_{page}")

    if movement_type in {"Salário", "Subsídio de Alimentação"}:
        category = "Subsídio Alimentação" if movement_type == "Subsídio de Alimentação" else "Salário"
    if st.button("Adicionar movimento", key=f"add_button_{page}", type="primary", use_container_width=True):
        if value <= 0:
            st.error("O valor tem de ser superior a zero.")
        elif movement_type == "Despesa" and category == "Outros" and not description.strip():
            st.error("Na categoria Outros, a descrição é obrigatória.")
        else:
            execute_write(
                """
                INSERT INTO transactions
                (person, type, category, description, value, date, payment_source)
                VALUES
                (:person, :type, :category, :description, :value, :date, :payment_source)
                """,
                {
                    "person": person,
                    "type": movement_type,
                    "category": category,
                    "description": description.strip(),
                    "value": value,
                    "date": str(movement_date),
                    "payment_source": payment_source,
                },
            )
            st.success("Movimento adicionado.")
            st.rerun()


def edit_transaction_panel(page: str, page_df: pd.DataFrame, categories: list[str]) -> None:
    with st.expander("Gerir movimentos"):
        options = {transaction_label(row): int(row["id"]) for _, row in page_df.iterrows()}
        selected_label = st.selectbox("Movimento", list(options.keys()), key=f"select_transaction_{page}")
        selected_id = options[selected_label]
        selected_row = page_df[page_df["id"] == selected_id].iloc[0]
        selected_description = str(selected_row.get("description") or "").strip()
        selected_category = str(selected_row.get("category") or "")
        selected_type = str(selected_row.get("type") or "")
        selected_value_class = "income" if selected_type == "Salário" else "expense"
        selected_signal = "+" if selected_type == "Salário" else "-"
        selected_extra = f" · {selected_description}" if selected_description else ""

        st.markdown(
            f"""
            <div class="selected-movement-card">
                <div class="selected-movement-eyebrow">Movimento selecionado</div>
                <div class="selected-movement-title">
                    <span>{escape(category_label(selected_category))} · {escape(selected_type)}</span>
                    <span class="{selected_value_class}">{selected_signal}{money(selected_row['value'])}</span>
                </div>
                <div class="selected-movement-meta">
                    {escape(str(selected_row['date']))} · {escape(str(selected_row['person']))}{escape(selected_extra)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action = st.radio(
            "O que queres fazer?",
            ["Editar movimento", "Remover movimento"],
            horizontal=True,
            key=f"manage_action_{page}_{selected_id}",
        )

        if action == "Remover movimento":
            st.markdown(
                '<div class="danger-zone-note"><strong>Atenção:</strong> esta ação elimina apenas o movimento selecionado.</div>',
                unsafe_allow_html=True,
            )
            if st.button("Eliminar movimento", key=f"delete_transaction_{page}_{selected_id}", use_container_width=True):
                execute_write("DELETE FROM transactions WHERE id = :id", {"id": selected_id})
                st.success("Movimento removido.")
                st.rerun()
            return

        st.markdown('<div class="edit-block-label">Editar dados</div>', unsafe_allow_html=True)
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
                    "Descrição se Outros",
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


def render_money_line(title: str, meta: str, value: float, tone: str) -> None:
    value_class = "income" if tone == "income" else "expense"
    tone_class = "compact-income" if tone == "income" else "compact-expense"
    signal = "+" if tone == "income" else "-"

    st.markdown(
        f"""
        <div class="compact-movement-card {tone_class}">
            <div class="compact-row">
                <div class="compact-main">
                    <div class="compact-title">{escape(title)}</div>
                    <div class="movement-meta">{escape(meta)}</div>
                </div>
                <div class="{value_class}">{signal}{money(value)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def balance_class_name(balance: float) -> str:
    if balance > 0:
        return "income"
    if balance < 0:
        return "expense"
    return "neutral"


def render_person_breakdown(person: str, person_df: pd.DataFrame) -> None:
    st.markdown(f'<div class="section-title">Resumo {escape(person)}</div>', unsafe_allow_html=True)

    salary_df = person_df[person_df["type_normalized"] == "salário"]
    expense_df = person_df[person_df["type_normalized"] == "despesa"]

    col_salary, col_expense = st.columns(2)

    with col_salary:
        st.markdown('<div class="compact-panel-title salary-title">Salários</div>', unsafe_allow_html=True)

        if salary_df.empty:
            st.markdown('<div class="empty-mini-card">Sem salário registado.</div>', unsafe_allow_html=True)
        else:
            for _, row in salary_df.head(5).iterrows():
                render_money_line(
                    title=category_label("Salário"),
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
                    title=category_label(category),
                    meta=meta,
                    value=float(row["value"]),
                    tone="expense",
                )


def render_plotly_flow_chart(flow_df: pd.DataFrame, accent: str) -> None:
    if flow_df.empty:
        return
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=flow_df["date"],
            y=flow_df["signed_value"],
            mode="lines+markers",
            line={"width": 3, "color": accent},
            marker={"size": 7, "color": accent},
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.10)",
            hovertemplate="%{x}<br>Fluxo: %{y:.2f}€<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        height=190,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.2)", title=None, zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})




def normalize_type_label(value: str) -> str:
    value_norm = str(value or '').strip().lower()
    if value_norm in {"salário", "salario"}:
        return "Salário"
    if value_norm in {"subsídio de alimentação", "subsidio de alimentação", "subsídio alimentação", "subsidio alimentacao", "subsídio alimentacao"}:
        return "Subsídio de Alimentação"
    return "Despesa"


def person_financials(person_df: pd.DataFrame) -> dict:
    salary_df = person_df[person_df["type_normalized"] == "salário"]
    expense_df = person_df[person_df["type_normalized"] == "despesa"]
    salary_income = salary_df[salary_df["category"].fillna("").str.lower() != "subsídio alimentação"]["value"].sum()
    allowance_income = salary_df[salary_df["category"].fillna("").str.lower() == "subsídio alimentação"]["value"].sum()
    food_df = expense_df[expense_df["category"].fillna("").str.lower().isin(["comida","alimentação","alimentacao"])]
    payment_series = food_df["payment_source"] if "payment_source" in food_df.columns else pd.Series("Salário", index=food_df.index)
    expense_card = food_df[payment_series == "Cartão alimentação"]["value"].sum() if not food_df.empty else 0
    expense_salary_food = food_df[payment_series != "Cartão alimentação"]["value"].sum() if not food_df.empty else 0
    non_food_expense = expense_df[~expense_df.index.isin(food_df.index)]["value"].sum() if not expense_df.empty else 0
    expense_salary_total = expense_salary_food + non_food_expense
    total_expense = expense_df["value"].sum() if not expense_df.empty else 0
    return {
        "salary_income": float(salary_income),
        "allowance_income": float(allowance_income),
        "expense_salary": float(expense_salary_total),
        "expense_card": float(expense_card),
        "total_expense": float(total_expense),
        "salary_balance": float(salary_income - expense_salary_total),
        "card_balance": float(allowance_income - expense_card),
        "total_balance": float((salary_income + allowance_income) - total_expense),
    }

def render_dashboard(filtered_df: pd.DataFrame, goals_df: pd.DataFrame) -> None:
    page_title("Casal", "Centro financeiro premium do casal: claro, inteligente e focado.")

    if filtered_df.empty:
        st.info("Não existem movimentos para os filtros escolhidos.")
        return

    income, expense, balance = financial_summary(filtered_df)
    expense_df = filtered_df[filtered_df["type_normalized"] == "despesa"]
    savings_rate = (max(income - expense, 0) / income * 100) if income > 0 else 0.0
    margin = income - expense

    month_start = pd.Timestamp.today().replace(day=1).date()
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    dseries = pd.to_datetime(filtered_df["date"], errors="coerce").dt.date
    current_month_df = filtered_df[dseries >= month_start]
    prev_month_df = filtered_df[(dseries >= last_month_start) & (dseries <= last_month_end)]
    cur_income, cur_expense, cur_balance = financial_summary(current_month_df)
    _, _, prev_balance = financial_summary(prev_month_df)

    delta_balance = cur_balance - prev_balance
    delta_pct = ((delta_balance / abs(prev_balance)) * 100) if prev_balance else (100.0 if cur_balance > 0 else 0.0)
    trend = "↗" if delta_balance >= 0 else "↘"

    health_state = "healthy" if balance > 0 and savings_rate >= 15 else "warning" if balance >= 0 else "danger"
    hero_context = {
        "healthy": "Saúde financeira sólida: continuam consistentes e com controlo.",
        "warning": "Atenção moderada: estão estáveis, mas convém reforçar a poupança.",
        "danger": "Zona de correção: pequenos ajustes agora geram impacto imediato.",
    }[health_state]

    biggest_expense = expense_df.sort_values("value", ascending=False).head(1)
    biggest_val = float(biggest_expense.iloc[0]["value"]) if not biggest_expense.empty else 0.0
    biggest_pct = (biggest_val / expense * 100) if expense > 0 else 0.0
    cat_totals = expense_df.groupby("category")["value"].sum().sort_values(ascending=False) if not expense_df.empty else pd.Series(dtype=float)
    top_cat = str(cat_totals.index[0]) if not cat_totals.empty else "Sem despesas"
    top_val = float(cat_totals.iloc[0]) if not cat_totals.empty else 0.0
    top_pct = (top_val / expense * 100) if expense > 0 else 0.0

    st.markdown(f"""
        <div class="couple-hero hero-{health_state}">
            <div class="hero-left"><div class="family-label">💎 Rubi & Gabi · Estado financeiro</div><div class="family-note">{hero_context}</div></div>
            <div class="hero-center"><div class="family-balance">{money(balance)}</div><div class="hero-micro">↕ {money(abs(delta_balance))} ({delta_pct:.1f}%) vs mês anterior</div></div>
            <div class="hero-right"><div class="health-pill state-{health_state}">{'Em alta' if health_state=='healthy' else 'Em atenção' if health_state=='warning' else 'Ajustar'}</div><div class="family-note">Taxa poupança {savings_rate:.1f}%</div></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="family-dashboard-grid couple-secondary-grid">
            <div class="family-main-card income-card"><div class="family-label">Entradas</div><div class="family-value income">{money(income)}</div></div>
            <div class="family-main-card expense-card"><div class="family-label">Despesas</div><div class="family-value expense">{money(expense)}</div></div>
            <div class="family-main-card savings-card"><div class="family-label">Taxa de poupança</div><div class="family-value neutral">{savings_rate:.1f}%</div></div>
            <div class="family-main-card mint-card"><div class="family-label">Margem financeira</div><div class="family-value {balance_class_name(margin)}">{money(margin)}</div></div>
        </div>
    """, unsafe_allow_html=True)

    biggest_title = category_label(str(biggest_expense.iloc[0].get("category") or "Despesa")) if not biggest_expense.empty else "Sem despesas"
    biggest_meta = f"{biggest_expense.iloc[0]['person']} · {biggest_expense.iloc[0]['date']}" if not biggest_expense.empty else "Ainda não há despesas no período."

    st.markdown(f"""
        <div class="family-insight-grid">
            <div class="family-insight-card">
                <div class="family-label">Maior despesa</div>
                <div class="family-insight-title">💸 {escape(biggest_title)}</div>
                <div class="family-insight-value expense">-{money(biggest_val)} · {biggest_pct:.1f}%</div>
                <div class="metric-track"><span style="width:{max(2,min(100,biggest_pct)) if biggest_pct else 0}%;"></span></div>
                <div class="family-note">{escape(biggest_meta)}</div>
            </div>
            <div class="family-insight-card">
                <div class="family-label">Categoria com mais gastos</div>
                <div class="family-insight-title">📊 {escape(category_label(top_cat))}</div>
                <div class="family-insight-value expense">-{money(top_val)} · {top_pct:.1f}%</div>
                <div class="metric-track"><span style="width:{max(2,min(100,top_pct)) if top_pct else 0}%;"></span></div>
                <div class="family-note">Foco ideal para otimizar o próximo mês.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not goals_df.empty:
        st.markdown('<div class="family-goals-title">Metas da família</div>', unsafe_allow_html=True)
        for _, goal in goals_df.iterrows():
            target_value = float(goal["target_amount"])
            current_value = float(goal["current_amount"])
            progress = min(current_value / target_value, 1) if target_value > 0 else 0
            progress_percent = int(round(progress * 100))
            missing = max(target_value - current_value, 0)
            monthly_push = max((income - expense) * 0.25, 1)
            months_left = int((missing / monthly_push) + 0.999) if missing > 0 else 0
            eta_text = "Concluída" if missing <= 0 else f"Previsão: ~{months_left} mês(es)"
            st.markdown(f"""
                <div class="family-goal-item">
                    <div class="family-goal-top"><div class="family-goal-name">{escape(str(goal['name']))}</div><div class="family-goal-percent">{progress_percent}%</div></div>
                    <div class="family-goal-values">{money(current_value)} / {money(target_value)} · {eta_text}</div>
                    <div class="family-goal-track"><span style="width:{progress_percent}%;"></span></div>
                    <div class="family-note">{escape(goal_message(progress_percent))}</div>
                </div>
            """, unsafe_allow_html=True)

    month_story = "Mês equilibrado e com boa disciplina." if cur_balance >= 0 else "Mês sob pressão — priorizar cortes estratégicos ajuda já."
    st.markdown(f"""
        <div class="family-insight-grid">
            <div class="family-insight-card"><div class="family-label">Resumo do mês</div><div class="family-insight-title">{month_story}</div></div>
            <div class="family-insight-card"><div class="family-label">Insight automático</div><div class="family-insight-title">{('Entradas cobrem despesas com margem.' if margin >= 0 else 'Despesas superam entradas neste período.')}</div></div>
            <div class="family-insight-card"><div class="family-label">Comparação mensal</div><div class="family-insight-title">{trend} {money(abs(delta_balance))} ({delta_pct:.1f}%) vs mês anterior</div></div>
        </div>
    """, unsafe_allow_html=True)


def render_person_page(page: str, filtered_df: pd.DataFrame, categories: list[str]) -> None:
    page_title(page, "Gestão simples e clara dos teus movimentos.")
    page_df = filtered_df[filtered_df["person"] == page] if not filtered_df.empty else pd.DataFrame()
    pdata = person_financials(page_df) if not page_df.empty else {k:0.0 for k in ["salary_income","allowance_income","total_expense","total_balance","expense_salary","expense_card","salary_balance","card_balance"]}

    if page == "Gabi":
        st.markdown(
            f"""
            <div class="family-dashboard-grid person-main-grid">
                <div class="family-main-card income-card"><div class="family-label">Salário</div><div class="family-value income">{money(pdata["salary_income"])}</div></div>
                <div class="family-main-card expense-card"><div class="family-label">Despesas</div><div class="family-value expense">{money(pdata["total_expense"])}</div></div>
                <div class="family-main-card available-card"><div class="family-label">Saldo disponível</div><div class="family-value {balance_class_name(pdata["total_balance"])}">{money(pdata["total_balance"])}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="family-dashboard-grid person-main-grid">
                <div class="family-main-card income-card"><div class="family-label">Salário</div><div class="family-value income">{money(pdata["salary_income"])}</div></div>
                <div class="family-main-card mint-card"><div class="family-label">Subsídio alimentação</div><div class="family-value income">{money(pdata["allowance_income"])}</div></div>
                <div class="family-main-card expense-card"><div class="family-label">Despesas</div><div class="family-value expense">{money(pdata["total_expense"])}</div></div>
                <div class="family-main-card available-card"><div class="family-label">Saldo disponível</div><div class="family-value {balance_class_name(pdata["total_balance"])}">{money(pdata["total_balance"])}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    flow_df = page_df.copy() if not page_df.empty else pd.DataFrame()
    if not flow_df.empty:
        flow_df["signed_value"] = flow_df.apply(lambda r: float(r["value"]) if str(r["type_normalized"]) == "salário" else -float(r["value"]), axis=1)
        flow_df = flow_df.sort_values("date").tail(20)
        st.markdown('<div class="section-title">Fluxo financeiro</div>', unsafe_allow_html=True)
        accent = "#0ea5e9" if page == "Ruben" else "#8b5cf6"
        render_plotly_flow_chart(flow_df, accent)

    insights_col, feed_col = st.columns([1, 1])
    with insights_col:
        month_balance = pdata["total_balance"]
        insight = "Excelente controlo este mês." if month_balance > 0 else "Sugestão: reduzir 1 categoria dominante."
        st.markdown(f"""<div class="family-insight-card person-tone-{page.lower()}"><div class="family-label">Insight automático</div><div class="family-insight-title">{insight}</div><div class="family-note">Saldo atual: {money(month_balance)}</div></div>""", unsafe_allow_html=True)
    with feed_col:
        st.markdown('<div class="section-title">Activity feed</div>', unsafe_allow_html=True)
        recent = page_df.head(5) if not page_df.empty else pd.DataFrame()
        if recent.empty:
            st.markdown('<div class="empty-mini-card">Sem atividade recente.</div>', unsafe_allow_html=True)
        else:
            for _, row in recent.iterrows():
                icon = "💰" if str(row["type_normalized"]) == "salário" else "🧾"
                amount = f"+{money(row['value'])}" if str(row["type_normalized"]) == "salário" else f"-{money(row['value'])}"
                amount_class = "income" if str(row["type_normalized"]) == "salário" else "expense"
                st.markdown(f"""<div class="activity-item"><div>{icon} {escape(category_label(str(row.get('category') or 'Movimento')))}<div class="movement-meta">{row['date']}</div></div><div class="{amount_class}">{amount}</div></div>""", unsafe_allow_html=True)

    form_col, list_col = st.columns([1, 1.2])
    with form_col:
        add_transaction_form(page, [page], categories)
    with list_col:
        list_header("Movimentos recentes", 0 if page_df.empty else min(len(page_df), 8))
        if page_df.empty:
            st.info("Sem movimentos para mostrar.")
        else:
            for _, row in page_df.head(8).iterrows():
                movement_card(row)

    if not page_df.empty:
        edit_transaction_panel(page, page_df, categories)

def goal_progress_color(progress_percent: int) -> str:
    if progress_percent < 25:
        return "linear-gradient(90deg, #ef4444, #dc2626)"
    if progress_percent < 50:
        return "linear-gradient(90deg, #ef4444, #f97316)"
    if progress_percent < 75:
        return "linear-gradient(90deg, #f59e0b, #84cc16)"
    return "linear-gradient(90deg, #22c55e, #059669)"


def render_goal_progress(progress: float) -> None:
    safe_progress = max(0.0, min(float(progress), 1.0))
    progress_percent = int(round(safe_progress * 100))
    fill_width = max(progress_percent, 1) if progress_percent > 0 else 0
    color = goal_progress_color(progress_percent)

    st.markdown(
        f"""
        <div class="goal-progress-wrap">
            <div class="goal-progress-meta">
                <div class="goal-progress-label">Progresso</div>
                <div class="goal-progress-percent">{progress_percent}% concluído</div>
            </div>
            <div class="goal-progress-track">
                <div class="goal-progress-fill" style="width: {fill_width}%; background: {color};">{progress_percent}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def goal_message(progress_percent: int) -> str:
    if progress_percent >= 100:
        return "Conquista alcançada. Esta meta já é vossa."
    if progress_percent >= 75:
        return "Está mesmo perto. Falta só o último impulso."
    if progress_percent >= 50:
        return "Já vai bem encaminhada. Continuem assim."
    if progress_percent >= 25:
        return "Quase a meio caminho. Cada reforço conta."
    return "Começar é o passo mais difícil. Já estão no caminho."


def render_goals(goals_df: pd.DataFrame) -> None:
    page_title("Metas", "Guardar dinheiro com mais motivação e menos peso.")

    if "show_goal_form" not in st.session_state:
        st.session_state.show_goal_form = False

    if not st.session_state.show_goal_form:
        if st.button("Criar nova meta", type="primary", use_container_width=True):
            st.session_state.show_goal_form = True
            st.rerun()
    else:
        section_title("Criar nova meta")
        col_name, col_target, col_current = st.columns([1.25, 1, 1])
        with col_name:
            name = st.text_input("Nome da meta")
        with col_target:
            target = st.number_input("Valor objetivo", min_value=0.0, step=10.0)
        with col_current:
            current = st.number_input("Valor atual", min_value=0.0, step=10.0)

        save_col, cancel_col = st.columns(2)
        with save_col:
            save_goal = st.button("Guardar meta", type="primary", use_container_width=True)
        with cancel_col:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.show_goal_form = False
                st.rerun()

        if save_goal:
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
                        "description": "",
                        "target_amount": target,
                        "current_amount": current,
                    },
                )
                st.session_state.show_goal_form = False
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
        missing_value = max(target_value - current_value, 0)
        progress_percent = int(round(progress * 100))
        fill_width = max(progress_percent, 1) if progress_percent > 0 else 0
        color = goal_progress_color(progress_percent)
        goal_id = int(goal["id"])

        missing_days = max((date.today().replace(day=28) + timedelta(days=4)).replace(day=1) - date.today(), timedelta(days=0)).days
        medal = "🥇" if progress_percent >= 100 else "🚀" if progress_percent >= 75 else "🔥" if progress_percent >= 40 else "🌱"
        state = "Concluída" if progress_percent >= 100 else "Quase concluída" if progress_percent >= 75 else "Em progresso" if progress_percent >= 25 else "Início"
        st.markdown(
            f"""
            <div class="goal-card goal-card-rich">
                <div class="goal-title-row">
                    <div class="goal-title">{medal} {escape(str(goal['name']))}</div>
                    <div class="goal-amount">{money(current_value)} / {money(target_value)}</div>
                </div>
                <div class="goal-percent-center">{progress_percent}%</div>
                <div class="goal-progress-track goal-progress-track-large">
                    <div class="goal-progress-fill" style="width: {fill_width}%; background: {color};"></div>
                </div>
                <div class="goal-bottom-row">
                    <span>{state} · Faltam {money(missing_value)} · {missing_days} dias</span>
                    <strong>{escape(goal_message(progress_percent))}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        amount_col, add_col, remove_col, delete_col = st.columns([1.6, 0.7, 0.7, 0.7])
        with amount_col:
            amount = st.number_input("Valor", min_value=0.0, step=5.0, key=f"goal_amount_{goal_id}")
        with add_col:
            if st.button("➕", key=f"add_goal_{goal_id}", help="Adicionar valor") and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = current_amount + :amount WHERE id = :id",
                    {"amount": amount, "id": goal_id},
                )
                st.success("Valor adicionado.")
                st.rerun()
        with remove_col:
            if st.button("➖", key=f"remove_goal_value_{goal_id}", help="Retirar valor") and amount > 0:
                execute_write(
                    "UPDATE goals SET current_amount = :value WHERE id = :id",
                    {"value": max(current_value - amount, 0), "id": goal_id},
                )
                st.success("Valor retirado.")
                st.rerun()
        with delete_col:
            if st.button("🗑", key=f"delete_goal_{goal_id}", help="Remover meta"):
                execute_write("DELETE FROM goals WHERE id = :id", {"id": goal_id})
                st.success("Meta removida.")
                st.rerun()

def render_categories(categories_df: pd.DataFrame) -> None:
    page_title("Categorias", "Organizar despesas sem complicar.")

    protected_categories = {"outros"}
    with st.container():
        section_title("Adicionar categoria")
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

    if categories_df.empty:
        st.info("Ainda não existem categorias.")
        return
    usage_df = load_transactions()
    if not categories_df.empty:
        usage_counts = usage_df[usage_df["type"].fillna("").str.lower().eq("despesa")].groupby("category").agg(total=("value","sum"), usos=("id","count")).reset_index() if not usage_df.empty else pd.DataFrame(columns=["category","total","usos"])
        usage_map = {str(r["category"]): (float(r["total"]), int(r["usos"])) for _, r in usage_counts.iterrows()}
        for _, c in categories_df.iterrows():
            cname = str(c["name"])
            total, usos = usage_map.get(cname, (0.0,0))
            st.markdown(f'<div class="category-grid-card category-grid-card-modern"><div class="category-card-main"><div class="category-name">🏷️ {escape(cname)}</div><div class="small-muted">{money(total)} · {usos} usos</div></div></div>', unsafe_allow_html=True)

    with st.expander("Gerir categorias", expanded=True):
        options = {row["name"]: int(row["id"]) for _, row in categories_df.iterrows()}
        selected = st.radio("Selecionar categoria", list(options.keys()), horizontal=True)
        selected_key = selected.strip().lower()

        if selected_key == "outros":
            st.info("A categoria 'Outros' é protegida e não pode ser renomeada nem removida.")
            return

        rename_col, delete_col = st.columns(2)
        with rename_col:
            new_name = st.text_input("Novo nome", key=f"rename_{options[selected]}")
            if st.button("Renomear", key=f"rename_btn_{options[selected]}", use_container_width=True):
                if not new_name.strip():
                    st.error("Escreve um novo nome para a categoria.")
                else:
                    execute_write("UPDATE categories SET name = :name WHERE id = :id", {"name": new_name.strip(), "id": options[selected]})
                    st.success("Categoria renomeada.")
                    st.rerun()
        with delete_col:
            if st.button("Eliminar", key=f"delete_{options[selected]}", use_container_width=True):
                execute_write("DELETE FROM categories WHERE id = :id", {"id": options[selected]})
                st.success("Categoria removida.")
                st.rerun()

def render_export(transactions_df: pd.DataFrame) -> None:
    page_title("Exportar", "Escolher um mês e descarregar em Excel.")

    today = date.today()
    month_names = [name for name in MONTHS if name != "Todos"]

    if transactions_df.empty:
        years = [today.year]
    else:
        years = sorted(transactions_df["year"].dropna().astype(int).unique().tolist(), reverse=True)
        if today.year not in years:
            years = [today.year, *years]

    income, expense, balance = financial_summary(transactions_df)
    forecast = balance + ((balance / max(today.day, 1)) * max(30 - today.day, 0)) if not transactions_df.empty else 0
    st.markdown(f"""<div class="export-summary-card"><div class="export-summary-grid"><div class="export-summary-item"><div class="export-summary-label">Resumo</div><div class="export-summary-value">Saldo {money(balance)}</div></div><div class="export-summary-item"><div class="export-summary-label">Insight</div><div class="export-summary-value">{('Boa margem atual' if balance >= 0 else 'Atenção às despesas')}</div></div><div class="export-summary-item"><div class="export-summary-label">Previsão mensal</div><div class="export-summary-value">{money(forecast)}</div></div></div></div>""", unsafe_allow_html=True)

    col_year, col_month = st.columns(2)
    with col_year:
        selected_year = st.selectbox(
            "Ano",
            years,
            index=years.index(today.year) if today.year in years else 0,
            key="export_year",
        )
    with col_month:
        current_month_name = month_names[today.month - 1]
        selected_month_name = st.selectbox(
            "Mês",
            month_names,
            index=month_names.index(current_month_name),
            key="export_month",
        )

    selected_month = MONTHS[selected_month_name]
    month_df = transactions_df[
        (transactions_df["year"] == int(selected_year)) & (transactions_df["month"] == int(selected_month))
    ] if not transactions_df.empty else pd.DataFrame()

    export_columns = ["person", "type", "category", "description", "value", "date"]
    income, expense, balance = financial_summary(month_df)

    st.markdown(
        f"""
        <div class="export-summary-card">
            <div class="export-summary-grid">
                <div class="export-summary-item">
                    <div class="export-summary-label">Movimentos</div>
                    <div class="export-summary-value">{len(month_df)}</div>
                </div>
                <div class="export-summary-item">
                    <div class="export-summary-label">Salários</div>
                    <div class="export-summary-value income">{money(income)}</div>
                </div>
                <div class="export-summary-item">
                    <div class="export-summary-label">Despesas</div>
                    <div class="export-summary-value expense">{money(expense)}</div>
                </div>
                <div class="export-summary-item">
                    <div class="export-summary-label">Saldo</div>
                    <div class="export-summary-value {balance_class_name(balance)}">{money(balance)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if int(selected_year) == today.year and int(selected_month) == today.month:
        st.info("Estás a exportar um mês ainda em curso. Para análise financeira, o ideal é exportar no fim do mês.")

    if month_df.empty:
        st.warning("Não existem movimentos no mês selecionado.")
        return

    export_view = month_df[export_columns].copy()
    export_view.columns = ["Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]

    st.download_button(
        label="Exportar mês selecionado",
        data=export_excel(month_df[["id"] + export_columns]),
        file_name=f"movimentos_{selected_year}_{selected_month:02d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    with st.expander("Pré-visualizar movimentos"):
        st.dataframe(export_view, use_container_width=True, hide_index=True)

def main() -> None:
    sidebar_brand()
    st.sidebar.markdown('<div class="sidebar-section-label">Menu</div>', unsafe_allow_html=True)

    page = st.sidebar.radio("Menu", ["Casal", "Ruben", "Gabi", "Metas", "Categorias", "Exportar"], label_visibility="collapsed")

    if page in ["Casal", "Ruben", "Gabi"]:
        transactions_df = load_transactions()
        filtered_df = filter_data(transactions_df)
    elif page == "Exportar":
        transactions_df = load_transactions()
        filtered_df = transactions_df
    else:
        filtered_df = pd.DataFrame()

    if page == "Casal":
        render_dashboard(filtered_df, load_goals())
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
