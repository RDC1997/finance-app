from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

from database import engine, SessionLocal, Base
from models import Transaction, Category, Goal

# =========================
# DB INIT
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# APP
# =========================
app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.1.72:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATABASE SESSION
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# VALIDATION
# =========================
def validate_date(input_date: str):
    if input_date > str(date.today()):
        raise HTTPException(
            status_code=400,
            detail="Data futura não permitida"
        )

def validate_outros(transaction: dict):
    if (
        transaction.get("type") == "Despesa"
        and transaction.get("category") == "Outros"
        and not transaction.get("description")
    ):
        raise HTTPException(
            status_code=400,
            detail="Descrição obrigatória para categoria 'Outros'"
        )

# =========================
# TRANSACTIONS
# =========================
@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()

@app.post("/transaction")
def add_transaction(data: dict, db: Session = Depends(get_db)):

    validate_date(data["date"])
    validate_outros(data)

    transaction = Transaction(**data)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction

@app.delete("/transaction/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):

    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transação não encontrada"
        )

    db.delete(transaction)
    db.commit()

    return {"ok": True}

# =========================
# CATEGORIES
# =========================
@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.post("/categories")
def add_category(data: dict, db: Session = Depends(get_db)):

    exists = (
        db.query(Category)
        .filter(Category.name == data["name"])
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=400,
            detail="Categoria já existe"
        )

    category = Category(name=data["name"])

    db.add(category)
    db.commit()
    db.refresh(category)

    return category

@app.delete("/categories/{id}")
def delete_category(id: int, db: Session = Depends(get_db)):

    category = (
        db.query(Category)
        .filter(Category.id == id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Categoria não existe"
        )

    if category.name.lower() == "outros":
        raise HTTPException(
            status_code=400,
            detail="Categoria protegida"
        )

    db.delete(category)
    db.commit()

    return {"ok": True}

# =========================
# GOALS
# =========================
@app.get("/goals")
def get_goals(db: Session = Depends(get_db)):
    return db.query(Goal).all()

@app.post("/goal")
def add_goal(data: dict, db: Session = Depends(get_db)):

    goal = Goal(**data)

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal

@app.delete("/goal/{id}")
def delete_goal(id: int, db: Session = Depends(get_db)):

    goal = (
        db.query(Goal)
        .filter(Goal.id == id)
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Meta não encontrada"
        )

    db.delete(goal)
    db.commit()

    return {"ok": True}