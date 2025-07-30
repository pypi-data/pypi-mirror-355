"""Tests for nested Pydantic model handling."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestBasicNestedModels:
    """Test basic nested Pydantic model handling."""
    
    def test_single_level_nesting(self, app):
        """Test single level of nested models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        profile_data = {
            "name": "John Doe",
            "age": 30,
            "contact": {
                "email": "john@example.com",
                "phone": "+1234567890"
            }
        }
        
        response = client.post("/test/create_user_profile", json={"profile": profile_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Profile created for John Doe" in data["message"]
        assert data["profile_id"] == 99999
        assert data["user"]["name"] == "John Doe"
        assert data["user"]["contact"]["email"] == "john@example.com"
        assert data["created_at"] == "2024-01-01T00:00:00Z"
    
    def test_multi_level_nesting(self, app):
        """Test deeply nested Pydantic model with multiple levels."""
        TestService.initialize(app)
        client = TestClient(app)
        
        profile_data = {
            "name": "Jane Smith",
            "age": 35,
            "contact": {
                "email": "jane@example.com",
                "phone": "+9876543210",
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "country": "USA",
                    "zip_code": "10001"
                }
            },
            "company": {
                "name": "Tech Corp",
                "address": {
                    "street": "456 Business Ave",
                    "city": "San Francisco",
                    "country": "USA",
                    "zip_code": "94105"
                },
                "employee_count": 100
            },
            "tags": ["developer", "manager"],
            "metadata": {"department": "Engineering", "level": "Senior"}
        }
        
        response = client.post("/test/create_user_profile", json={"profile": profile_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["contact"]["address"]["city"] == "New York"
        assert data["user"]["company"]["name"] == "Tech Corp"
        assert data["user"]["company"]["address"]["city"] == "San Francisco"
        assert len(data["user"]["tags"]) == 2
        assert data["user"]["metadata"]["department"] == "Engineering"


class TestNestedModelParameters:
    """Test nested model parameters."""
    
    def test_nested_model_param(self, app):
        """Test single nested model parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        address_data = {
            "street": "789 Oak St",
            "city": "Boston",
            "country": "USA",
            "zip_code": "02101"
        }
        
        # Test with wrapped format
        response = client.post("/test/update_address", json={
            "user_id": 123,
            "address": address_data
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 123
        assert data["updated"] is True
        assert data["address"]["city"] == "Boston"
        assert data["address"]["zip_code"] == "02101"
    
    def test_company_info_raw(self, app):
        """Test nested model with raw value for single-param endpoint."""
        TestService.initialize(app)
        client = TestClient(app)
        
        company_data = {
            "name": "StartupXYZ",
            "address": {
                "street": "999 Innovation Blvd",
                "city": "Austin",
                "country": "USA"
            },
            "employee_count": 50
        }
        
        # Test with raw value (single parameter)
        response = client.post("/test/get_company_info", json=company_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "StartupXYZ"
        assert data["location"] == "Austin, USA"
        assert data["employees"] == 50
        assert data["full_address"]["street"] == "999 Innovation Blvd"
        assert data["full_address"]["zip"] is None  # Optional field


class TestNestedListHandling:
    """Test nested models containing lists."""
    
    def test_model_with_nested_list(self, app):
        """Test nested model containing a list of nested models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        order_data = {
            "order_id": 12345,
            "customer_name": "Alice Johnson",
            "items": [
                {"product_id": 1, "quantity": 2, "price": 10.99},
                {"product_id": 2, "quantity": 1, "price": 25.50},
                {"product_id": 3, "quantity": 3, "price": 5.00}
            ],
            "shipping_address": {
                "street": "321 Elm St",
                "city": "Chicago",
                "country": "USA",
                "zip_code": "60601"
            }
        }
        
        response = client.post("/test/process_order", json={"order": order_data})
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == 12345
        assert data["customer"] == "Alice Johnson"
        assert data["item_count"] == 3
        assert data["total"] == 2 * 10.99 + 1 * 25.50 + 3 * 5.00  # 62.48
        assert data["ship_to"] == "Chicago, USA"
    
    def test_list_of_nested_models_param(self, app):
        """Test list of models with nested structures."""
        TestService.initialize(app)
        client = TestClient(app)
        
        profiles_data = [
            {
                "name": "User 1",
                "age": 25,
                "contact": {
                    "email": "user1@example.com",
                    "phone": "+111",
                    "address": {
                        "street": "Street 1",
                        "city": "City 1",
                        "country": "Country 1"
                    }
                }
            },
            {
                "name": "User 2",
                "age": 30,
                "contact": {
                    "email": "user2@example.com"
                    # No phone or address
                }
            },
            {
                "name": "User 3",
                "age": 35,
                "contact": {
                    "email": "user3@example.com",
                    "phone": "+333"
                    # No address
                }
            }
        ]
        
        response = client.post("/test/extract_contacts", json={"profiles": profiles_data})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "User 1"
        assert data[0]["has_phone"] is True
        assert data[0]["has_address"] is True
        assert data[0]["city"] == "City 1"
        assert data[1]["has_phone"] is False
        assert data[1]["has_address"] is False
        assert "city" not in data[1]
        assert data[2]["has_phone"] is True
        assert data[2]["has_address"] is False


class TestNestedModelReturns:
    """Test returning nested models."""
    
    def test_return_list_of_nested_models(self, app):
        """Test returning List of nested Pydantic models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test get_order_items
        response = client.post("/test/get_order_items", json={"order_id": 123})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        assert data[0]["product_id"] == 1
        assert data[0]["quantity"] == 2
        assert data[0]["price"] == 10.50
        
        assert data[1]["product_id"] == 2
        assert data[1]["quantity"] == 1
        assert data[1]["price"] == 25.00
        
        # Test empty order
        response = client.post("/test/get_order_items", json={"order_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_return_complex_nested_models(self, app):
        """Test returning List of complex nested models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test find_companies_by_city - San Francisco
        response = client.post("/test/find_companies_by_city", json={"city": "San Francisco"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check first company
        assert data[0]["name"] == "Tech Giant"
        assert data[0]["employee_count"] == 10000
        assert data[0]["address"]["street"] == "1 Market St"
        assert data[0]["address"]["city"] == "San Francisco"
        assert data[0]["address"]["country"] == "USA"
        assert data[0]["address"]["zip_code"] == "94105"
        
        # Check second company
        assert data[1]["name"] == "AI Startup"
        assert data[1]["employee_count"] == 50
        
        # Test New York
        response = client.post("/test/find_companies_by_city", json={"city": "New York"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Finance Corp"
        assert data[0]["address"]["city"] == "New York"
        
        # Test city with no companies
        response = client.post("/test/find_companies_by_city", json={"city": "Boston"})
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_single_param_nested_list_raw(self, app):
        """Test single parameter endpoint returning List[NestedModel] with raw input."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test with raw city string (single parameter)
        response = client.post("/test/find_companies_by_city", json="San Francisco")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Tech Giant"
        
        # Test with wrapped format
        response = client.post("/test/find_companies_by_city", json={"city": "New York"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Finance Corp"


class TestOptionalNestedFields:
    """Test optional fields in nested models."""
    
    def test_minimal_nested_model(self, app):
        """Test optional fields in nested models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Minimal profile with only required fields
        profile_data = {
            "name": "Minimal User",
            "age": 22,
            "contact": {
                "email": "minimal@example.com"
                # Optional: phone, address
            }
            # Optional: company, tags, metadata
        }
        
        response = client.post("/test/create_user_profile", json={"profile": profile_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["name"] == "Minimal User"
        assert data["user"]["contact"]["phone"] is None
        assert data["user"]["contact"]["address"] is None
        assert data["user"]["company"] is None
        assert data["user"]["tags"] == []
        assert data["user"]["metadata"] is None


class TestNestedModelValidation:
    """Test validation errors in nested models."""
    
    def test_missing_required_nested_field(self, app):
        """Test missing required field in nested model."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Missing required field in nested model
        profile_data = {
            "name": "Invalid User",
            "age": 40,
            "contact": {
                # Missing required 'email' field
                "phone": "+123456"
            }
        }
        
        response = client.post("/test/create_user_profile", json={"profile": profile_data})
        assert response.status_code == 422  # Validation error
    
    def test_wrong_type_in_nested_field(self, app):
        """Test wrong type in deeply nested field."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Wrong type in deeply nested field
        order_data = {
            "order_id": 999,
            "customer_name": "Bad Customer",
            "items": [
                {"product_id": 1, "quantity": "not_a_number", "price": 10.0}  # Wrong type
            ],
            "shipping_address": {
                "street": "Bad St",
                "city": "Bad City",
                "country": "Bad Country"
            }
        }
        
        response = client.post("/test/process_order", json={"order": order_data})
        assert response.status_code == 422  # Validation error