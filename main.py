from fastapi import FastAPI
import requests
import os

app = FastAPI()

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_PASSWORD = os.getenv("SHOPIFY_API_PASSWORD")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")

@app.get("/")
def root():
    return {"message": "Backend Shopify-wFirma działa!"}

@app.post("/sync-orders")
def sync_orders():
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2023-10/orders.json"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, auth=(SHOPIFY_API_KEY, SHOPIFY_API_PASSWORD), headers=headers)
    if response.status_code == 200:
        orders = response.json()
        # Tu dodasz logikę: zapisz zamówienia do bazy i wyślij do wFirma
        return {"status": "Zamówienia pobrane", "count": len(orders.get("orders", []))}
    return {"error": "Nie udało się pobrać zamówień", "status_code": response.status_code}
