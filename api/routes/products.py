import json
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os

from api.models.products import Product, ProductResponse, ProductSearchParams

router = APIRouter(prefix="/products", tags=["products"])

# Load product data
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ProductCatalog.json")

def load_products():
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading product data: {e}")
        return []

@router.get("/", response_model=ProductResponse)
def get_products(
    query: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    min_inventory: Optional[int] = None
):
    """
    Get all products with optional filtering
    """
    products = load_products()
    
    if query:
        query = query.lower()
        products = [p for p in products if (
            query in p["ProductName"].lower() or 
            query in p["Description"].lower() or
            query in p["SKU"].lower()
        )]
    
    if tags:
        products = [p for p in products if any(tag in p["Tags"] for tag in tags)]
    
    if min_inventory is not None:
        products = [p for p in products if p["Inventory"] >= min_inventory]
        
    return {"products": products}

@router.get("/{sku}", response_model=Product)
def get_product(sku: str):
    """
    Get a single product by SKU
    """
    products = load_products()
    for product in products:
        if product["SKU"] == sku:
            return product
    
    raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
