from pydantic import BaseModel
from typing import List, Optional

class Order(BaseModel):
    CustomerName: str
    Email: str
    OrderNumber: str
    ProductsOrdered: List[str]
    Status: str
    TrackingNumber: Optional[str] = None

class OrderResponse(BaseModel):
    orders: List[Order]

class OrderSearchParams(BaseModel):
    customer_email: Optional[str] = None
    order_number: Optional[str] = None