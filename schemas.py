from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    person: str
    type: str
    category: str
    description: Optional[str] = None
    value: float
    date: str


class CategoryCreate(BaseModel):
    name: str


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0