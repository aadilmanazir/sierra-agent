from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    ProductName: str
    SKU: str
    Inventory: int
    Description: str
    Tags: List[str]

class ProductResponse(BaseModel):
    products: List[Product]