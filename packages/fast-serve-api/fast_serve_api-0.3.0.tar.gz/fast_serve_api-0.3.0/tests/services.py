"""Test services for fast-serve-api tests."""
from typing import List, Dict, Optional, Tuple, Any, Set, Literal
from pydantic import BaseModel

from fast_serve_api import FastServeApi
from tests.models import (
    UserInput, ProductInput, UserResponse, UserListResponse, InvalidResponse,
    AddressModel, CompanyModel, UserProfileInput, UserProfileResponse,
    Order, OrderItem
)


class TestService(FastServeApi):
    """Test service for unit tests."""
    
    @staticmethod
    def simple_string() -> str:
        return "Hello, World!"
    
    @staticmethod
    def echo_string(message: str) -> str:
        return message
    
    @staticmethod
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    @staticmethod
    def optional_param(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"
    
    @staticmethod
    def return_list(count: int) -> List[int]:
        return list(range(count))
    
    @staticmethod
    def return_dict(key: str, value: str) -> Dict[str, str]:
        return {key: value}
    
    @staticmethod
    def return_tuple(a: int, b: str) -> Tuple[int, str]:
        return (a, b)
    
    @staticmethod
    def complex_params(
        text: str,
        numbers: List[int],
        options: Dict[str, bool],
        coordinates: Tuple[float, float]
    ) -> Dict[str, Any]:
        return {
            "text": text,
            "sum": sum(numbers),
            "enabled_options": [k for k, v in options.items() if v],
            "distance": (coordinates[0]**2 + coordinates[1]**2)**0.5
        }
    
    @staticmethod
    def raise_error(message: str) -> str:
        raise ValueError(message)
    
    @staticmethod
    def toggle_boolean(state: bool) -> bool:
        return not state
    
    @staticmethod
    def optional_boolean(flag: Optional[bool] = None) -> Optional[bool]:
        return flag
    
    @staticmethod
    def process_boolean_list(values: List[bool]) -> Dict[str, Any]:
        return {
            "count": len(values),
            "true_count": sum(values),
            "false_count": len(values) - sum(values),
            "all_true": all(values),
            "any_true": any(values)
        }
    
    @staticmethod
    def echo_float(value: float) -> float:
        return value
    
    @staticmethod
    def return_void() -> None:
        return None
    
    @staticmethod
    def wrong_type_string() -> int:
        """Should return int but returns string."""
        return "hello"
    
    @staticmethod
    def wrong_type_none() -> str:
        """Should return str but returns None."""
        return None
    
    @staticmethod
    def wrong_type_bool() -> int:
        """Should return int but returns bool."""
        return True
    
    @staticmethod
    def wrong_list_type() -> List[str]:
        """Should return List[str] but returns List with mixed types."""
        return ["hello", 123, "world"]
    
    @staticmethod
    def wrong_dict_type() -> Dict[str, int]:
        """Should return Dict[str, int] but returns Dict with wrong value types."""
        return {"a": 1, "b": "two", "c": 3}
    
    @staticmethod
    def return_set() -> Set[str]:
        return {"apple", "banana", "cherry"}
    
    @staticmethod
    def echo_set(values: Set[int]) -> Set[int]:
        return values
    
    @staticmethod
    def process_set(items: Set[str]) -> Dict[str, Any]:
        return {
            "count": len(items),
            "items": sorted(items),  # Sort for consistent testing
            "has_apple": "apple" in items
        }
    
    @staticmethod
    def wrong_set_type() -> Set[int]:
        """Should return Set[int] but returns Set with mixed types."""
        return {1, "two", 3}
    
    @staticmethod
    def process_string_list(words: List[str]) -> str:
        """Join a list of strings."""
        return " ".join(words)
    
    @staticmethod
    def process_int_list(numbers: List[int]) -> int:
        """Sum a list of integers."""
        return sum(numbers)
    
    @staticmethod
    def get_status(name: str) -> Literal["active", "inactive", "pending"]:
        """Return a status based on name."""
        if name == "admin":
            return "active"
        elif name == "guest":
            return "inactive"
        else:
            return "pending"
    
    @staticmethod
    def set_priority(level: Literal["low", "medium", "high"]) -> str:
        """Set priority level."""
        return f"Priority set to: {level}"
    
    @staticmethod
    def process_action(action: Literal["start", "stop", "restart"], force: bool = False) -> Dict[str, Any]:
        """Process an action."""
        return {
            "action": action,
            "forced": force,
            "timestamp": "2024-01-01T00:00:00"
        }
    
    @staticmethod
    def wrong_literal_return() -> Literal["yes", "no"]:
        """Should return 'yes' or 'no' but returns something else."""
        return "maybe"  # Wrong!
    
    @staticmethod
    def mixed_literal_type(value: Literal[1, "two", 3.14, True]) -> str:
        """Accept mixed type literals."""
        return f"Received: {value} (type: {type(value).__name__})"
    
    @staticmethod
    def create_user(user: UserInput) -> UserResponse:
        """Create a user from input data and return valid response."""
        return UserResponse(
            success=True,
            message=f"User {user.name} created successfully",
            user_id=12345,
            username=user.name.lower().replace(" ", "_"),
            is_active=True
        )
    
    @staticmethod
    def list_users(page: int = 1, size: int = 10) -> UserListResponse:
        """Return a paginated list of users."""
        users = [
            {"id": i, "name": f"User {i}", "active": i % 2 == 0}
            for i in range(1, 6)
        ]
        return UserListResponse(
            success=True,
            message="Users retrieved successfully",
            page=page,
            size=size,
            last_page=True,
            total=5,
            users=users
        )
    
    @staticmethod
    def create_product(product: ProductInput) -> Dict[str, Any]:
        """Create a product and return as dict (mixed return type)."""
        return {
            "id": 999,
            "name": product.name,
            "price": product.price,
            "in_stock": product.in_stock,
            "categories": list(product.categories)
        }
    
    @staticmethod
    def invalid_return_user() -> InvalidResponse:
        """Should fail - returns BaseModel instead of FastServeApiModel."""
        return InvalidResponse(data="test", count=1)
    
    @staticmethod
    def mixed_params(
        text: str,
        user: UserInput,
        numbers: List[int],
        options: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """Test method with mixed primitive and Pydantic parameters."""
        result = {
            "text": text,
            "user_name": user.name,
            "user_age": user.age,
            "numbers_sum": sum(numbers)
        }
        if options:
            result["enabled_options"] = [k for k, v in options.items() if v]
        return result
    
    @staticmethod
    def process_multiple_users(users: List[UserInput]) -> Dict[str, Any]:
        """Process a list of Pydantic models."""
        return {
            "count": len(users),
            "names": [u.name for u in users],
            "avg_age": sum(u.age for u in users) / len(users) if users else 0,
            "with_email": sum(1 for u in users if u.email)
        }
    
    @staticmethod
    def create_user_profile(profile: UserProfileInput) -> UserProfileResponse:
        """Create a user profile with nested data."""
        return UserProfileResponse(
            success=True,
            message=f"Profile created for {profile.name}",
            profile_id=99999,
            user=profile,
            created_at="2024-01-01T00:00:00Z"
        )
    
    @staticmethod
    def update_address(user_id: int, address: AddressModel) -> Dict[str, Any]:
        """Update user address (nested model parameter)."""
        return {
            "user_id": user_id,
            "updated": True,
            "address": {
                "street": address.street,
                "city": address.city,
                "country": address.country,
                "zip_code": address.zip_code
            }
        }
    
    @staticmethod
    def process_order(order: Order) -> Dict[str, Any]:
        """Process an order with nested items and address."""
        total = sum(item.quantity * item.price for item in order.items)
        return {
            "order_id": order.order_id,
            "customer": order.customer_name,
            "item_count": len(order.items),
            "total": total,
            "ship_to": f"{order.shipping_address.city}, {order.shipping_address.country}"
        }
    
    @staticmethod
    def get_company_info(company: CompanyModel) -> Dict[str, Any]:
        """Get company information with nested address."""
        return {
            "name": company.name,
            "location": f"{company.address.city}, {company.address.country}",
            "full_address": {
                "street": company.address.street,
                "city": company.address.city,
                "country": company.address.country,
                "zip": company.address.zip_code
            },
            "employees": company.employee_count
        }
    
    @staticmethod
    def extract_contacts(profiles: List[UserProfileInput]) -> List[Dict[str, Any]]:
        """Extract contact information from multiple profiles."""
        contacts = []
        for profile in profiles:
            contact_data = {
                "name": profile.name,
                "email": profile.contact.email,
                "has_phone": profile.contact.phone is not None,
                "has_address": profile.contact.address is not None
            }
            if profile.contact.address:
                contact_data["city"] = profile.contact.address.city
            contacts.append(contact_data)
        return contacts
    
    @staticmethod
    def list_all_users(page: int = 1, size: int = 10) -> List[UserInput]:
        """Return a list of UserInput models (not wrapped in FastServeApiListModel)."""
        users = []
        start = (page - 1) * size
        for i in range(start, start + size):
            users.append(UserInput(
                name=f"User {i + 1}",
                age=20 + (i % 50),
                email=f"user{i + 1}@example.com" if i % 2 == 0 else None,
                tags=[f"tag{i % 3}", f"tag{(i + 1) % 3}"] if i % 3 == 0 else []
            ))
        return users
    
    @staticmethod
    def get_order_items(order_id: int) -> List[OrderItem]:
        """Return a list of OrderItem models."""
        # Simulate fetching order items
        if order_id == 999:
            return []  # Empty order
        
        items = [
            OrderItem(product_id=1, quantity=2, price=10.50),
            OrderItem(product_id=2, quantity=1, price=25.00),
            OrderItem(product_id=3, quantity=3, price=5.99)
        ]
        return items
    
    @staticmethod
    def find_companies_by_city(city: str) -> List[CompanyModel]:
        """Find companies in a given city - returns List of nested models."""
        companies = []
        if city.lower() == "san francisco":
            companies.extend([
                CompanyModel(
                    name="Tech Giant",
                    address=AddressModel(
                        street="1 Market St",
                        city="San Francisco",
                        country="USA",
                        zip_code="94105"
                    ),
                    employee_count=10000
                ),
                CompanyModel(
                    name="AI Startup",
                    address=AddressModel(
                        street="100 Mission St",
                        city="San Francisco",
                        country="USA",
                        zip_code="94105"
                    ),
                    employee_count=50
                )
            ])
        elif city.lower() == "new york":
            companies.append(
                CompanyModel(
                    name="Finance Corp",
                    address=AddressModel(
                        street="200 Wall St",
                        city="New York",
                        country="USA",
                        zip_code="10005"
                    ),
                    employee_count=5000
                )
            )
        return companies


class MultiWordService(FastServeApi):
    """Test service with multi-word name."""
    
    @staticmethod
    def get_info() -> str:
        return "Multi-word service"