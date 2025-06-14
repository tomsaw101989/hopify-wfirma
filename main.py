from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔓 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Baza danych (Supabase)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 🧾 Model zamówienia
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50))
    customer_name = Column(String(100))
    image_url = Column(String(300))  # ✅ tutaj był błąd wcięcia
    items = Column(Text)
    total_price = Column(Float)
    status = Column(String(50))
    created_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

# 🔁 Output model
class OrderOut(BaseModel):
    id: int
    number: str
    customer_name: str
    image_url: str  # ✅ też trzeba było przesunąć
    items: List[str]
    total_price: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# 📦 GET zamówień
@app.get("/orders")
def get_orders():
    db = SessionLocal()
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return {
        "orders": [
            OrderOut(
                id=o.id,
                number=o.number,
                customer_name=o.customer_name,
                image_url=o.image_url,
                items=o.items.split("|"),
                total_price=o.total_price,
                status=o.status,
                created_at=o.created_at
            )
            for o in orders
        ]
    }

# 🔄 Synchronizacja z Shopify
@app.post("/sync-orders")
def sync_orders():
    db = SessionLocal()
    store = os.getenv("SHOPIFY_STORE")
    api_key = os.getenv("SHOPIFY_API_KEY")
    api_password = os.getenv("SHOPIFY_API_PASSWORD")
    url = f"https://{store}.myshopify.com/admin/api/2023-10/orders.json"
    response = requests.get(url, auth=(api_key, api_password))
    if response.status_code != 200:
        return {"error": "Błąd pobierania", "status_code": response.status_code}

    data = response.json()
    for order in data.get("orders", []):
        customer_name = order["customer"].get("first_name", "") + " " + order["customer"].get("last_name", "")
        items = [item["title"] for item in order.get("line_items", [])]
        image_url = order.get("line_items", [{}])[0].get("image", {}).get("src", "")

        existing = db.query(Order).filter_by(number=order["order_number"]).first()
        if not existing:
            new_order = Order(
                number=order["order_number"],
                customer_name=customer_name,
                items="|".join(items),
                total_price=order["total_price"],
                status="Nowe",
                created_at=order["created_at"],
                image_url=image_url
            )
            db.add(new_order)
    db.commit()
    return {"status": "Zamówienia pobrane i zapisane", "count": len(data.get("orders", []))}
