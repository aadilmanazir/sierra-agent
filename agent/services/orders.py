import json
import os
import httpx
from typing import List, Dict, Any, Optional

# Local API base URL
API_BASE = "http://localhost:8000"

async def search_orders(customer_email: str = None, order_number: str = None) -> List[Dict[str, Any]]:
    """
    Search for orders with optional filtering
    """
    params = {}
    if customer_email:
        params["customer_email"] = customer_email
    if order_number:
        params["order_number"] = order_number
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/orders/", params=params)
        response.raise_for_status()
        return response.json()["orders"]

def format_order_info(order: Dict[str, Any]) -> str:
    """
    Format order information for display to the user
    """
    products_ordered = ", ".join(order['ProductsOrdered'])
    
    # Create tracking info with link when available
    if order.get('TrackingNumber'):
        tracking_url = f"https://tools.usps.com/go/TrackConfirmAction?tLabels={order['TrackingNumber']}"
        tracking_info = f"Tracking Number: {order['TrackingNumber']}\nTracking Link: {tracking_url}"
    else:
        tracking_info = "No tracking number available"
    
    return f"""
    Order: {order['OrderNumber']}
    Customer: {order['CustomerName']} ({order['Email']})
    Status: {order['Status'].upper()}
    Products Ordered: {products_ordered}
    Tracking Info: {tracking_info}
    """

def order_status_to_readable(status: str) -> str:
    """
    Convert order status to a readable format
    """
    status_map = {
        "delivered": "The order has been delivered",
        "in-transit": "The order is on its way",
        "fulfilled": "The order has been processed and is ready for shipping",
        "error": "There was an issue with the order"
    }
    
    return status_map.get(status.lower(), f"The order status is: {status}")

def orders_to_context(orders: List[Dict[str, Any]]) -> str:
    """
    Convert a list of orders to a context string for the agent
    """
    if not orders:
        return "No orders found matching your criteria."
    
    result = f"Found {len(orders)} orders:\n\n"
    for order in orders:
        result += f"- Order {order['OrderNumber']} for {order['CustomerName']}: Status: {order['Status']}\n"
    
    return result

async def get_order_details(order_number: str, customer_email: str = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific order
    """
    orders = await search_orders(customer_email=customer_email, order_number=order_number)
    if not orders:
        raise ValueError(f"No order found with number {order_number}")
    
    return orders[0]

async def track_order(tracking_number: str) -> Dict[str, Any]:
    """
    Track an order using its tracking number
    """
    # Search all orders to find one with matching tracking number
    orders = await search_orders()
    matching_orders = [order for order in orders if order.get('TrackingNumber') == tracking_number]
    
    if not matching_orders:
        raise ValueError(f"No order found with tracking number {tracking_number}")
    
    return matching_orders[0]
