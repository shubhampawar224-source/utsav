from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_filename: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Sale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    user_id: int
    quantity: int = 1
    total_price: float
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
