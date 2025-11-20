from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import stripe

from schemas import Product, Review, Order, SearchQuery, AIRecommendRequest, PaymentIntentRequest, WebhookEvent, CartItem, User

app = FastAPI(title="BlessedBuy API", version="0.1.0")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In a full app, use MongoDB helpers (database.py). Here we mock with simple lists just to scaffold endpoints.
# Note: In production, replace with create_document/get_documents and motor collection access.
PRODUCTS: List[Product] = []
REVIEWS: List[Review] = []
ORDERS: List[Order] = []
USERS: List[User] = []

@app.get("/")
def root():
    return {"message": "BlessedBuy API running"}

@app.post("/products", response_model=Product)
def create_product(product: Product):
    product.id = str(len(PRODUCTS)+1)
    PRODUCTS.append(product)
    return product

@app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = None):
    if category:
        return [p for p in PRODUCTS if p.category == category]
    return PRODUCTS

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    for p in PRODUCTS:
        if p.id == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/reviews", response_model=Review)
def create_review(review: Review):
    review.id = str(len(REVIEWS)+1)
    REVIEWS.append(review)
    return review

@app.get("/products/{product_id}/reviews", response_model=List[Review])
def list_reviews(product_id: str):
    return [r for r in REVIEWS if r.product_id == product_id]

@app.post("/orders", response_model=Order)
def create_order(order: Order):
    order.id = str(len(ORDERS)+1)
    ORDERS.append(order)
    return order

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    for o in ORDERS:
        if o.id == order_id:
            return o
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/search", response_model=List[Product])
def search_products(query: SearchQuery):
    results = PRODUCTS
    if query.text:
        q = query.text.lower()
        results = [p for p in results if q in p.title.lower() or q in p.description.lower()]
    if query.category:
        results = [p for p in results if p.category == query.category]
    if query.min_price is not None:
        results = [p for p in results if p.price >= query.min_price]
    if query.max_price is not None:
        results = [p for p in results if p.price <= query.max_price]
    if query.sort == "price_asc":
        results = sorted(results, key=lambda x: x.price)
    if query.sort == "price_desc":
        results = sorted(results, key=lambda x: x.price, reverse=True)
    return results

@app.post("/ai/recommend", response_model=List[Product])
def ai_recommend(req: AIRecommendRequest):
    # Simple heuristic placeholder: match recent_searches keywords in title
    if not req.recent_searches:
        return PRODUCTS[:8]
    keys = [k.lower() for k in req.recent_searches]
    scored = []
    for p in PRODUCTS:
        score = sum(1 for k in keys if k in p.title.lower() or k in p.description.lower() or k in p.category.lower())
        if score:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored][:12]

# Payments: Stripe intent creation (Razorpay could be similar)
stripe.api_key = os.getenv("STRIPE_SECRET", "")

@app.post("/payments/intent")
def create_payment_intent(req: PaymentIntentRequest):
    if req.provider == "stripe":
        if not stripe.api_key:
            # Dev mode: just return a fake client_secret
            return {"client_secret": "test_secret", "provider": "stripe"}
        intent = stripe.PaymentIntent.create(amount=req.amount, currency=req.currency)
        return {"client_secret": intent.client_secret, "provider": "stripe"}
    # For Razorpay, integrate similarly (create order and return id)
    return {"message": "Provider not implemented", "provider": req.provider}

@app.post("/payments/webhook")
def payment_webhook(event: WebhookEvent):
    # In real deployment, verify signature and update order
    return {"received": True, "provider": event.provider}

# Auth stubs (use Firebase or Supabase in a real app)
class AuthRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    provider: str = "email"

@app.post("/auth/login", response_model=User)
def login(req: AuthRequest):
    # Stub: create a user or find existing
    for u in USERS:
        if req.email and u.email == req.email:
            return u
    new_user = User(id=str(len(USERS)+1), email=req.email, name=req.name, phone=req.phone, provider=req.provider)
    USERS.append(new_user)
    return new_user
