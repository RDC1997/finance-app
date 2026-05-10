from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

from database import engine, SessionLocal, Base
from models import Transaction, Category, Goal
from schemas import TransactionCreate, CategoryCreate, GoalCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_date(d):
    if d > str(date.today()):
        raise HTTPException(status_code=400, detail="Data futura não permitida")


def validate_outros(p):
    if (
        p.get("type", "").lower() == "despesa"
        and p.get("category", "").lower() == "outros"
        and not p.get("description")
    ):
        raise HTTPException(
            status_code=400,
            detail="Descrição obrigatória para categoria 'Outros'"
        )


@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()


@app.post("/transaction")
def add_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    payload = data.dict()

    validate_date(payload["date"])
    validate_outros(payload)

    t = Transaction(**payload)
    db.add(t)
    db.commit()
    db.refresh(t)

    return t


@app.put("/transaction/{id}")
def update_transaction(id: int, data: TransactionCreate, db: Session = Depends(get_db)):

    t = db.query(Transaction).filter(Transaction.id == id).first()

    if not t:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    payload = data.dict()

    payload["type"] = payload["type"].strip()
    payload["category"] = payload.get("category") or ""
    payload["description"] = payload.get("description") or ""

    validate_date(payload["date"])
    validate_outros(payload)

    for k, v in payload.items():
        setattr(t, k, v)

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


@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.post("/categories")
def add_category(data: CategoryCreate, db: Session = Depends(get_db)):

    exists = db.query(Category).filter(Category.name == data.name).first()

    if exists:
        raise HTTPException(status_code=400, detail="Categoria já existe")

    c = Category(name=data.name)
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


@app.get("/goals")
def get_goals(db: Session = Depends(get_db)):
    return db.query(Goal).all()


@app.post("/goal")
def add_goal(data: GoalCreate, db: Session = Depends(get_db)):

    g = Goal(**data.dict())
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