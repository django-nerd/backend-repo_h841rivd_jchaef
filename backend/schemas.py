from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class User(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    provider: Optional[str] = None  # email, google, phone
    created_at: Optional[str] = None

class Product(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    price: float
    stock: int = 0
    images: List[str] = []
    category: str
    rating: float = 0
    supplier: Optional[str] = None
    supplier_link: Optional[str] = None
    attributes: dict = {}

class Review(BaseModel):
    id: Optional[str] = None
    product_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)

class Order(BaseModel):
    id: Optional[str] = None
    user_id: str
    items: List[CartItem]
    amount: float
    currency: str = "INR"
    status: str = "pending"
    payment_id: Optional[str] = None
    provider: Optional[str] = None  # stripe or razorpay
    address: Optional[dict] = None
    timeline: List[dict] = []

class SearchQuery(BaseModel):
    text: Optional[str] = None
    voice: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort: Optional[str] = None

class AIRecommendRequest(BaseModel):
    user_id: Optional[str] = None
    recent_searches: List[str] = []

class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "INR"
    provider: str = "stripe"

class WebhookEvent(BaseModel):
    provider: str
    payload: dict
