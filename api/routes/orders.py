import json
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os

from api.models.order import Order, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])

# Load order data
# Define base directory and data file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "CustomerOrders.json")

def load_orders():
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading order data: {e}")
        return []

@router.get("/", response_model=OrderResponse)
def get_orders(
    customer_email: Optional[str] = None,
    order_number: Optional[str] = None
):
    """
    Get all orders with optional filtering
    """
    orders = load_orders()
    
    if customer_email:
        orders = [o for o in orders if o["Email"].lower() == customer_email.lower()]
    
    if order_number:
        orders = [o for o in orders if o["OrderNumber"] == order_number]
        
    return {"orders": orders}