"""Test models for fast-serve-api tests."""

from typing import Any

from pydantic import BaseModel

from fast_serve_api.models import FastServeApiListModel, FastServeApiModel


# Test Pydantic models for parameter testing
class UserInput(BaseModel):
    """Input model for user data."""

    name: str
    age: int
    email: str | None = None
    tags: list[str] = []


class ProductInput(BaseModel):
    """Input model for product data."""

    name: str
    price: float
    in_stock: bool = True
    categories: set[str] = set()


# Test Pydantic models for return testing
class UserResponse(FastServeApiModel):
    """Valid response model that inherits from FastServeApiModel."""

    user_id: int
    username: str
    is_active: bool


class UserListResponse(FastServeApiListModel):
    """Valid list response model that inherits from FastServeApiListModel."""

    users: list[dict[str, Any]]


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
    zip_code: str | None = None


class CompanyModel(BaseModel):
    """Nested company model."""

    name: str
    address: AddressModel
    employee_count: int = 0


class ContactInfo(BaseModel):
    """Contact information model."""

    email: str
    phone: str | None = None
    address: AddressModel | None = None


class UserProfileInput(BaseModel):
    """Complex nested user profile input."""

    name: str
    age: int
    contact: ContactInfo
    company: CompanyModel | None = None
    tags: list[str] = []
    metadata: dict[str, Any] | None = None


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
    items: list[OrderItem]
    shipping_address: AddressModel
    total: float | None = None
