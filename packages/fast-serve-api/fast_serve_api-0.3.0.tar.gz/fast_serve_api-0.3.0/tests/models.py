"""Test models for fast-serve-api tests."""
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel

from fast_serve_api.models import FastServeApiModel, FastServeApiListModel


# Test Pydantic models for parameter testing
class UserInput(BaseModel):
    """Input model for user data."""
    name: str
    age: int
    email: Optional[str] = None
    tags: List[str] = []


class ProductInput(BaseModel):
    """Input model for product data."""
    name: str
    price: float
    in_stock: bool = True
    categories: Set[str] = set()


# Test Pydantic models for return testing
class UserResponse(FastServeApiModel):
    """Valid response model that inherits from FastServeApiModel."""
    user_id: int
    username: str
    is_active: bool


class UserListResponse(FastServeApiListModel):
    """Valid list response model that inherits from FastServeApiListModel."""
    users: List[Dict[str, Any]]


class InvalidResponse(BaseModel):
    """Invalid response model that only inherits from BaseModel."""
    data: str
    count: int


# Nested Pydantic models for testing
class AddressModel(BaseModel):
    """Nested address model."""
    street: str
    city: str
    country: str
    zip_code: Optional[str] = None


class CompanyModel(BaseModel):
    """Nested company model."""
    name: str
    address: AddressModel
    employee_count: int = 0


class ContactInfo(BaseModel):
    """Contact information model."""
    email: str
    phone: Optional[str] = None
    address: Optional[AddressModel] = None


class UserProfileInput(BaseModel):
    """Complex nested user profile input."""
    name: str
    age: int
    contact: ContactInfo
    company: Optional[CompanyModel] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class UserProfileResponse(FastServeApiModel):
    """Complex nested response model."""
    profile_id: int
    user: UserProfileInput
    created_at: str


class OrderItem(BaseModel):
    """Nested order item."""
    product_id: int
    quantity: int
    price: float


class Order(BaseModel):
    """Order with nested items."""
    order_id: int
    customer_name: str
    items: List[OrderItem]
    shipping_address: AddressModel
    total: Optional[float] = None