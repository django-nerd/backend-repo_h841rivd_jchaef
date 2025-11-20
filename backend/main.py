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

# Seed a few demo products for the preview
if not PRODUCTS:
    demo = [
        Product(id="1", title="Teal Silk Scarf", description="Premium silk scarf with subtle geometric pattern", price=1999, stock=25, images=["https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop"], category="Fashion", rating=4.6),
        Product(id="2", title="Wireless Earbuds Pro", description="ANC, 30h battery, IPX5", price=5999, stock=50, images=["https://images.unsplash.com/photo-1590658268037-6bf12165a8df?q=80&w=1200&auto=format&fit=crop"], category="Electronics", rating=4.4),
        Product(id="3", title="Rose Glow Serum", description="Vitamin C + Hyaluronic acid", price=1299, stock=80, images=["https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?q=80&w=1200&auto=format&fit=crop"], category="Beauty", rating=4.3),
        Product(id="4", title="Minimalist Wall Lamp", description="Warm dimmable LED, matte gold", price=3499, stock=15, images=["https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop"], category="Home Decor", rating=4.5),
        Product(id="5", title="Prayer Mat – CloudSoft", description="Ultra-plush, anti-slip base", price=2499, stock=40, images=["https://images.unsplash.com/photo-1602453224934-5a4b63ac2b9f?q=80&w=1200&auto=format&fit=crop"], category="Islamic Essentials", rating=4.8),
        Product(id="6", title="Hardcover Journal", description="120 GSM paper, gold-foil cover", price=799, stock=120, images=["https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1200&auto=format&fit=crop"], category="Books", rating=4.2),
        Product(id="7", title="Gift Set – Teal Gold", description="Scented candle + mug + card", price=1499, stock=30, images=["https://images.unsplash.com/photo-1519682577862-22b62b24e493?q=80&w=1200&auto=format&fit=crop"], category="Gifts", rating=4.1),
        Product(id="8", title="Leather Card Holder", description="RFID-blocking, slim design", price=999, stock=60, images=["https://images.unsplash.com/photo-1617050351951-53c1ce9de2ef?q=80&w=1200&auto=format&fit=crop"], category="Accessories", rating=4.0),
    ]
    PRODUCTS.extend(demo)

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
