import json
import os
import httpx
from typing import List, Dict, Any, Optional

# Local API base URL
API_BASE = "http://localhost:8000"

async def get_all_products() -> List[Dict[str, Any]]:
    """
    Get all products from the product catalog without filtering
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/products")
            response.raise_for_status()
            result = response.json()
            
            # Check for expected structure
            if not isinstance(result, dict) or "products" not in result:
                print(f"Unexpected API response format: {result}")
                return []
                
            products = result["products"]
            if not isinstance(products, list):
                print(f"API returned non-list products: {products}")
                return []
                
            return products
    except httpx.HTTPError as e:
        print(f"HTTP error retrieving products: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error retrieving products: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error retrieving products: {e}")
        return []
