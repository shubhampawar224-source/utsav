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
