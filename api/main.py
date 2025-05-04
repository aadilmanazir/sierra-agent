from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import products, orders

app = FastAPI(
    title="Sierra Outfitters API",
    description="API for Sierra Outfitters product catalog and order tracking",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Sierra Outfitters API",
        "endpoints": {
            "products": "/products",
            "orders": "/orders"
        }
    }
