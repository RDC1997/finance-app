import os

import streamlit as st
from sqlalchemy import create_engine, text

DEFAULT_CATEGORIES = [
    "Casa",
    "Comida",
    "Transportes",
    "Lazer",
    "Saúde",
    "Compras",
    "Contas",
    "Outros",
]


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")
    if not database_url:
        st.error("Configura a variável DATABASE_URL ou st.secrets['DATABASE_URL'].")
        st.stop()

    return database_url.replace("postgresql://", "postgresql+psycopg://")


@st.cache_resource
def get_engine():
    return create_engine(_database_url(), pool_pre_ping=True)


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        person TEXT,
        type TEXT,
        category TEXT,
        description TEXT,
        value FLOAT,
        date TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS goals (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        target_amount FLOAT,
        current_amount FLOAT
    )
    """,
    """
    ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS payment_source TEXT DEFAULT 'Salário'
    """,
)


def init_database() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(text(statement))


def ensure_default_categories() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for category in DEFAULT_CATEGORIES:
            conn.execute(
                text(
                    """
                    INSERT INTO categories (name)
                    VALUES (:name)
                    ON CONFLICT (name) DO NOTHING
                    """
                ),
                {"name": category},
            )
