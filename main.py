from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

from database import engine, SessionLocal, Base
from models import Transaction, Category, Goal

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

# =========================
# CORS (OBRIGATÓRIO PARA FRONTEND)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.1.72:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB
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
        raise HTTPException(status_code=400, detail="Data futura não permitida")


def validate_outros(transaction: dict):
    if (
        transaction["type"] == "Despesa"
        and transaction["category"] == "Outros"
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

    t = Transaction(**data)
    db.add(t)
    db.commit()
    db.refresh(t)

    return t


@app.delete("/transaction/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):

    t = db.query(Transaction).filter(Transaction.id == id).first()

    if not t:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    db.delete(t)
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

    exists = db.query(Category).filter(Category.name == data["name"]).first()

    if exists:
        raise HTTPException(status_code=400, detail="Categoria já existe")

    c = Category(name=data["name"])
    db.add(c)
    db.commit()
    db.refresh(c)

    return c


@app.delete("/categories/{id}")
def delete_category(id: int, db: Session = Depends(get_db)):

    c = db.query(Category).filter(Category.id == id).first()

    if not c:
        raise HTTPException(status_code=404, detail="Categoria não existe")

    if c.name.lower() == "outros":
        raise HTTPException(status_code=400, detail="Categoria protegida")

    db.delete(c)
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

    g = Goal(**data)
    db.add(g)
    db.commit()
    db.refresh(g)

    return g


@app.delete("/goal/{id}")
def delete_goal(id: int, db: Session = Depends(get_db)):

    g = db.query(Goal).filter(Goal.id == id).first()

    if not g:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    db.delete(g)
    db.commit()

    return {"ok": True}