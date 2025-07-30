"""Tests for Pydantic model handling in FastServeApi."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestPydanticParameters:
    """Test Pydantic model parameters."""
    
    def test_basic_pydantic_parameter(self, app):
        """Test basic Pydantic model as parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        user_data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "tags": ["developer", "python"]
        }
        
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "John Doe" in data["message"]
        assert data["user_id"] == 12345
        assert data["username"] == "john_doe"
        assert data["is_active"] is True
    
    def test_pydantic_optional_fields(self, app):
        """Test Pydantic model with optional fields."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Without optional fields
        user_data = {
            "name": "Jane Smith",
            "age": 25
        }
        
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["username"] == "jane_smith"
    
    def test_pydantic_validation(self, app):
        """Test Pydantic model validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Missing required field
        user_data = {
            "name": "Invalid User"
            # age is missing
        }
        
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 422  # Validation error
        
        # Wrong type for field
        user_data = {
            "name": "Invalid User",
            "age": "not a number"
        }
        
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 422  # Validation error
    
    def test_pydantic_with_set_field(self, app):
        """Test Pydantic model with Set field."""
        TestService.initialize(app)
        client = TestClient(app)
        
        product_data = {
            "name": "Laptop",
            "price": 999.99,
            "in_stock": True,
            "categories": ["electronics", "computers", "electronics"]  # Duplicate will be removed
        }
        
        response = client.post("/test/create_product", json={"product": product_data})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Laptop"
        assert data["price"] == 999.99
        assert data["in_stock"] is True
        assert set(data["categories"]) == {"electronics", "computers"}
        assert len(data["categories"]) == 2  # Duplicates removed
    
    def test_single_pydantic_param_raw(self, app):
        """Test that single Pydantic model parameters can accept raw values."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # For single-parameter endpoints, raw values that match the model structure are accepted
        user_data = {
            "name": "Raw User",
            "age": 25
        }
        
        # This should work because single-parameter endpoints accept raw values
        response = client.post("/test/create_user", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["username"] == "raw_user"
        
        # Also test with wrapped format
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["username"] == "raw_user"


class TestPydanticReturns:
    """Test Pydantic model returns."""
    
    def test_valid_pydantic_return(self, app):
        """Test valid Pydantic model returns (FastServeApiModel)."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # UserResponse inherits from FastServeApiModel - should work
        user_data = {
            "name": "Test User",
            "age": 28
        }
        
        response = client.post("/test/create_user", json={"user": user_data})
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "user_id" in data
        assert "username" in data
        assert "is_active" in data
    
    def test_valid_list_model_return(self, app):
        """Test valid Pydantic list model returns (FastServeApiListModel)."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/list_users", json={"page": 1, "size": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["last_page"] is True
        assert data["total"] == 5
        assert len(data["users"]) == 5
        assert data["users"][0]["id"] == 1
    
    def test_invalid_pydantic_return(self, app):
        """Test invalid Pydantic model returns (BaseModel only)."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # InvalidResponse only inherits from BaseModel - should fail
        response = client.post("/test/invalid_return_user")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type must be a subclass of FastServeApiModel or FastServeApiListModel" in data["message"]


class TestMixedParameters:
    """Test mixed primitive and Pydantic parameters."""
    
    def test_mixed_params_all_provided(self, app):
        """Test mixed parameters with all fields provided."""
        TestService.initialize(app)
        client = TestClient(app)
        
        request_data = {
            "text": "Hello World",
            "user": {
                "name": "Alice",
                "age": 35,
                "email": "alice@example.com"
            },
            "numbers": [10, 20, 30],
            "options": {
                "feature_a": True,
                "feature_b": False,
                "feature_c": True
            }
        }
        
        response = client.post("/test/mixed_params", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello World"
        assert data["user_name"] == "Alice"
        assert data["user_age"] == 35
        assert data["numbers_sum"] == 60
        assert set(data["enabled_options"]) == {"feature_a", "feature_c"}
    
    def test_mixed_params_optional_omitted(self, app):
        """Test mixed parameters without optional fields."""
        TestService.initialize(app)
        client = TestClient(app)
        
        request_data = {
            "text": "Test",
            "user": {
                "name": "Bob",
                "age": 40
            },
            "numbers": [1, 2, 3]
            # options is optional
        }
        
        response = client.post("/test/mixed_params", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Test"
        assert data["user_name"] == "Bob"
        assert data["numbers_sum"] == 6
        assert "enabled_options" not in data


class TestListOfPydanticModels:
    """Test List[PydanticModel] handling."""
    
    def test_list_of_models_parameter(self, app):
        """Test list of Pydantic models as parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        users_data = [
            {"name": "User 1", "age": 20, "email": "user1@example.com"},
            {"name": "User 2", "age": 30},
            {"name": "User 3", "age": 40, "email": "user3@example.com", "tags": ["admin"]}
        ]
        
        response = client.post("/test/process_multiple_users", json={"users": users_data})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert data["names"] == ["User 1", "User 2", "User 3"]
        assert data["avg_age"] == 30.0
        assert data["with_email"] == 2
    
    def test_empty_list_of_models(self, app):
        """Test empty list of Pydantic models."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/process_multiple_users", json={"users": []})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["names"] == []
        assert data["avg_age"] == 0
        assert data["with_email"] == 0
    
    def test_list_of_models_return(self, app):
        """Test returning List[PydanticModel]."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test list_all_users endpoint
        response = client.post("/test/list_all_users", json={"page": 1, "size": 5})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5
        
        # Check first user
        assert data[0]["name"] == "User 1"
        assert data[0]["age"] == 20
        assert data[0]["email"] == "user1@example.com"
        assert data[0]["tags"] == ["tag0", "tag1"]
        
        # Check second user (no email)
        assert data[1]["name"] == "User 2"
        assert data[1]["age"] == 21
        assert data[1]["email"] is None
        assert data[1]["tags"] == []
        
        # Test pagination
        response = client.post("/test/list_all_users", json={"page": 2, "size": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "User 4"  # First user on page 2