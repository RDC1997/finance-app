from sqlalchemy import Column, Integer, String, Float
from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    person = Column(String)
    type = Column(String)          # Salário / Despesa
    category = Column(String)
    description = Column(String)
    value = Column(Float)
    date = Column(String)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    target = Column(Float)