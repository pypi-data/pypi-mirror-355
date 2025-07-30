"""Tests for basic endpoint registration and simple parameter types."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService, MultiWordService


class TestEndpointRegistration:
    """Test endpoint registration and naming."""
    
    def test_endpoint_registration(self, app):
        """Test that endpoints are properly registered."""
        TestService.initialize(app)
        
        routes = [route.path for route in app.routes]
        assert "/test/simple_string" in routes
        assert "/test/echo_string" in routes
        assert "/test/add_numbers" in routes
    
    def test_multi_word_class_name(self, app):
        """Test that multi-word class names are converted to snake_case."""
        MultiWordService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/multi_word/get_info")
        assert response.status_code == 200
        data = response.json()
        assert data == "Multi-word service"


class TestSimpleParameters:
    """Test endpoints with simple parameter types."""
    
    def test_no_parameters(self, app):
        """Test endpoint with no parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/simple_string")
        assert response.status_code == 200
        data = response.json()
        assert data == "Hello, World!"
    
    def test_single_string_param(self, app):
        """Test endpoint with single string parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test with object notation
        response = client.post("/test/echo_string", json={"message": "Test message"})
        assert response.status_code == 200
        data = response.json()
        assert data == "Test message"
        
        # Test with raw value (single field)
        response = client.post("/test/echo_string", json="Direct message")
        assert response.status_code == 200
        data = response.json()
        assert data == "Direct message"
    
    def test_multiple_int_params(self, app):
        """Test endpoint with multiple integer parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/add_numbers", json={"a": 5, "b": 3})
        assert response.status_code == 200
        data = response.json()
        assert data == 8
    
    def test_float_parameter(self, app):
        """Test float parameter and return type."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test float parameter with object notation
        response = client.post("/test/echo_float", json={"value": 3.14})
        assert response.status_code == 200
        data = response.json()
        assert data == 3.14
        assert isinstance(data, float)
        
        # Test float parameter with raw value (single field)
        response = client.post("/test/echo_float", json=2.71828)
        assert response.status_code == 200
        data = response.json()
        assert data == 2.71828
        assert isinstance(data, float)
        
        # Test type coercion from int to float
        response = client.post("/test/echo_float", json={"value": 42})
        assert response.status_code == 200
        data = response.json()
        assert data == 42.0
        assert isinstance(data, float)
        
        # Test with string that can be converted to float
        response = client.post("/test/echo_float", json={"value": "3.14"})
        assert response.status_code == 200
        data = response.json()
        assert data == 3.14
        assert isinstance(data, float)
    
    def test_boolean_parameter(self, app):
        """Test boolean parameter type."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test with object notation
        response = client.post("/test/toggle_boolean", json={"state": False})
        assert response.status_code == 200
        data = response.json()
        assert data is True
        assert isinstance(data, bool)
        
        # Test with raw value (single field)
        response = client.post("/test/toggle_boolean", json=False)
        assert response.status_code == 200
        data = response.json()
        assert data is True
        assert isinstance(data, bool)
        
        # Test with object notation
        response = client.post("/test/toggle_boolean", json={"state": True})
        assert response.status_code == 200
        data = response.json()
        assert data is False
        assert isinstance(data, bool)
        
        # Test with raw value (single field)
        response = client.post("/test/toggle_boolean", json=True)
        assert response.status_code == 200
        data = response.json()
        assert data is False
        assert isinstance(data, bool)


class TestOptionalParameters:
    """Test endpoints with optional parameters."""
    
    def test_optional_string_param(self, app):
        """Test endpoint with optional string parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # With default value
        response = client.post("/test/optional_param", json={"name": "Alice"})
        assert response.status_code == 200
        data = response.json()
        assert data == "Hello, Alice!"
        
        # With custom value
        response = client.post("/test/optional_param", json={"name": "Bob", "greeting": "Hi"})
        assert response.status_code == 200
        data = response.json()
        assert data == "Hi, Bob!"
    
    def test_optional_boolean_param(self, app):
        """Test optional boolean parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test with no value (should return None)
        response = client.post("/test/optional_boolean")
        assert response.status_code == 200
        data = response.json()
        assert data is None
        
        # Test with True
        response = client.post("/test/optional_boolean", json={"flag": True})
        assert response.status_code == 200
        data = response.json()
        assert data is True
        
        # Test with False
        response = client.post("/test/optional_boolean", json={"flag": False})
        assert response.status_code == 200
        data = response.json()
        assert data is False
        
        # Test with explicit None
        response = client.post("/test/optional_boolean", json={"flag": None})
        assert response.status_code == 200
        data = response.json()
        assert data is None


class TestParameterValidation:
    """Test parameter validation and error handling."""
    
    def test_missing_required_param(self, app):
        """Test endpoint with missing required parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/echo_string")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_invalid_param_type(self, app):
        """Test endpoint with invalid parameter type."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/add_numbers", json={"a": "not_a_number", "b": 3})
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_boolean_param_coercion(self, app):
        """Test boolean parameter type coercion and validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test with string "true" - Pydantic coerces to boolean
        response = client.post("/test/toggle_boolean", json={"state": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data is False  # "true" -> True -> not True = False
        
        # Test with string "false" - Pydantic coerces to boolean
        response = client.post("/test/toggle_boolean", json={"state": "false"})
        assert response.status_code == 200
        data = response.json()
        assert data is True  # "false" -> False -> not False = True
        
        # Test with number 1 - Pydantic coerces to boolean
        response = client.post("/test/toggle_boolean", json={"state": 1})
        assert response.status_code == 200
        data = response.json()
        assert data is False  # 1 -> True -> not True = False
        
        # Test with number 0 - Pydantic coerces to boolean
        response = client.post("/test/toggle_boolean", json={"state": 0})
        assert response.status_code == 200
        data = response.json()
        assert data is True  # 0 -> False -> not False = True
        
        # Test with null - This should fail
        response = client.post("/test/toggle_boolean", json={"state": None})
        assert response.status_code == 422
        
        # Test with invalid string that can't be coerced
        response = client.post("/test/toggle_boolean", json={"state": "invalid"})
        assert response.status_code == 422


class TestNoneReturnType:
    """Test None/void return type."""
    
    def test_return_void(self, app):
        """Test endpoint that returns None."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/return_void")
        assert response.status_code == 200
        data = response.json()
        assert data is None