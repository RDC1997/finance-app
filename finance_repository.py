from io import BytesIO

import pandas as pd
import streamlit as st
from sqlalchemy import text

from finance_db import ensure_default_categories, get_engine

TRANSACTION_COLUMNS = [
    "id",
    "person",
    "type",
    "category",
    "description",
    "value",
    "date",
    "date_dt",
    "year",
    "month",
]
GOAL_COLUMNS = ["id", "name", "description", "target_amount", "current_amount"]


def clear_data_cache() -> None:
    load_transactions.clear()
    load_categories.clear()
    load_goals.clear()


@st.cache_data(ttl=20, show_spinner=False)
def load_transactions() -> pd.DataFrame:
    with get_engine().begin() as conn:
        dataframe = pd.read_sql("SELECT * FROM transactions ORDER BY id DESC", conn)

    if dataframe.empty:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    dataframe["value"] = pd.to_numeric(dataframe["value"], errors="coerce").fillna(0)
    dataframe["date_dt"] = pd.to_datetime(dataframe["date"], errors="coerce")
    dataframe["year"] = dataframe["date_dt"].dt.year
    dataframe["month"] = dataframe["date_dt"].dt.month
    dataframe["type_normalized"] = dataframe["type"].fillna("").str.lower()

    return dataframe


@st.cache_data(ttl=60, show_spinner=False)
def load_categories() -> pd.DataFrame:
    ensure_default_categories()
    with get_engine().begin() as conn:
        return pd.read_sql("SELECT * FROM categories ORDER BY name", conn)


@st.cache_data(ttl=20, show_spinner=False)
def load_goals() -> pd.DataFrame:
    with get_engine().begin() as conn:
        dataframe = pd.read_sql("SELECT * FROM goals ORDER BY id DESC", conn)

    if dataframe.empty:
        return pd.DataFrame(columns=GOAL_COLUMNS)

    dataframe["target_amount"] = pd.to_numeric(dataframe["target_amount"], errors="coerce").fillna(0)
    dataframe["current_amount"] = pd.to_numeric(dataframe["current_amount"], errors="coerce").fillna(0)

    return dataframe


def execute_write(statement: str, params: dict) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(statement), params)
    clear_data_cache()


def export_excel(dataframe: pd.DataFrame) -> bytes:
    output = BytesIO()
    export_df = dataframe.copy()
    export_df = export_df.drop(columns=[col for col in ["date_dt", "year", "month", "type_normalized"] if col in export_df])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Movimentos")

    return output.getvalue()
