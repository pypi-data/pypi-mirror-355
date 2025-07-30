"""Tests for endpoints with all optional parameters."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestAllOptionalParameters:
    """Test endpoints where all parameters are optional."""
    
    def test_all_optional_no_body(self, app):
        """Test endpoint with all optional params can be called without body."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Call list_users without any body - should use defaults
        response = client.post("/test/list_users")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["page"] == 1  # Default value
        assert data["size"] == 10  # Default value
        assert data["total"] == 5
    
    def test_optional_boolean_no_body(self, app):
        """Test optional boolean endpoint without body."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Call optional_boolean without any body
        response = client.post("/test/optional_boolean")
        assert response.status_code == 200
        data = response.json()
        assert data is None
    
    def test_list_all_users_with_defaults(self, app):
        """Test list_all_users can be called without body."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Call without body - should use default page=1, size=10
        response = client.post("/test/list_all_users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # Default size
        assert data[0]["name"] == "User 1"  # First user on default page 1
    
    def test_mixed_optional_and_required(self, app):
        """Test that endpoints with required params still require body."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # echo_string has a required parameter, should fail without body
        response = client.post("/test/echo_string")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_optional_with_single_param(self, app):
        """Test single optional parameter endpoint."""
        from fast_serve_api import FastServeApi
        
        class OptionalTestService(FastServeApi):
            @staticmethod
            def optional_greeting(name: str = "World") -> str:
                return f"Hello, {name}!"
        
        OptionalTestService.initialize(app)
        client = TestClient(app)
        
        # Call without body
        response = client.post("/optional_test/optional_greeting")
        assert response.status_code == 200
        assert response.json() == "Hello, World!"
        
        # Call with body
        response = client.post("/optional_test/optional_greeting", json={"name": "Alice"})
        assert response.status_code == 200
        assert response.json() == "Hello, Alice!"
        
        # Call with raw value (single param)
        response = client.post("/optional_test/optional_greeting", json="Bob")
        assert response.status_code == 200
        assert response.json() == "Hello, Bob!"