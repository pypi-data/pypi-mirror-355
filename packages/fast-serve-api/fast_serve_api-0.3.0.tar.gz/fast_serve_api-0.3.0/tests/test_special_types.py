"""Tests for special types like Literal."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestLiteralTypes:
    """Test Literal type handling."""
    
    def test_literal_return_type(self, app):
        """Test Literal return type validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test valid literal returns
        response = client.post("/test/get_status", json={"name": "admin"})
        assert response.status_code == 200
        assert response.json() == "active"
        
        response = client.post("/test/get_status", json={"name": "guest"})
        assert response.status_code == 200
        assert response.json() == "inactive"
        
        response = client.post("/test/get_status", json={"name": "other"})
        assert response.status_code == 200
        assert response.json() == "pending"
    
    def test_literal_parameter(self, app):
        """Test Literal parameter validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test valid literal values
        response = client.post("/test/set_priority", json={"level": "high"})
        assert response.status_code == 200
        assert response.json() == "Priority set to: high"
        
        response = client.post("/test/set_priority", json={"level": "low"})
        assert response.status_code == 200
        assert response.json() == "Priority set to: low"
        
        response = client.post("/test/set_priority", json={"level": "medium"})
        assert response.status_code == 200
        assert response.json() == "Priority set to: medium"
        
        # Test invalid literal values
        response = client.post("/test/set_priority", json={"level": "urgent"})
        assert response.status_code == 422  # Should fail validation
        
        response = client.post("/test/set_priority", json={"level": "medium-high"})
        assert response.status_code == 422  # Should fail validation
    
    def test_literal_with_optional(self, app):
        """Test Literal parameter with optional parameter."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test valid action without force
        response = client.post("/test/process_action", json={"action": "start"})
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "start"
        assert data["forced"] is False
        
        # Test valid action with force
        response = client.post("/test/process_action", json={"action": "stop", "force": True})
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "stop"
        assert data["forced"] is True
        
        # Test invalid action
        response = client.post("/test/process_action", json={"action": "pause"})
        assert response.status_code == 422  # Should fail validation
    
    def test_mixed_type_literal(self, app):
        """Test Literal with mixed types."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test integer literal
        response = client.post("/test/mixed_literal_type", json={"value": 1})
        assert response.status_code == 200
        assert "Received: 1" in response.json()
        
        # Test string literal
        response = client.post("/test/mixed_literal_type", json={"value": "two"})
        assert response.status_code == 200
        assert "Received: two" in response.json()
        
        # Test float literal
        response = client.post("/test/mixed_literal_type", json={"value": 3.14})
        assert response.status_code == 200
        assert "Received: 3.14" in response.json()
        
        # Test boolean literal
        response = client.post("/test/mixed_literal_type", json={"value": True})
        assert response.status_code == 200
        assert "Received: True" in response.json()
        
        # Test invalid values
        response = client.post("/test/mixed_literal_type", json={"value": 2})
        assert response.status_code == 422  # 2 is not in the allowed values
        
        response = client.post("/test/mixed_literal_type", json={"value": "three"})
        assert response.status_code == 422  # "three" is not in the allowed values
    
    def test_literal_single_param_raw(self, app):
        """Test single-field Literal with raw values."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test valid raw values
        response = client.post("/test/set_priority", json="high")
        assert response.status_code == 200
        assert response.json() == "Priority set to: high"
        
        response = client.post("/test/set_priority", json="medium")
        assert response.status_code == 200
        assert response.json() == "Priority set to: medium"
        
        # Test invalid raw value for Literal
        response = client.post("/test/set_priority", json="urgent")
        assert response.status_code == 422  # Should fail validation
        
        # Test mixed literal with raw values
        response = client.post("/test/mixed_literal_type", json=1)
        assert response.status_code == 200
        assert "Received: 1" in response.json()
        
        response = client.post("/test/mixed_literal_type", json="two")
        assert response.status_code == 200
        assert "Received: two" in response.json()
        
        response = client.post("/test/mixed_literal_type", json=3.14)
        assert response.status_code == 200
        assert "Received: 3.14" in response.json()
        
        response = client.post("/test/mixed_literal_type", json=True)
        assert response.status_code == 200
        assert "Received: True" in response.json()
        
        # Test invalid raw value for mixed literal
        response = client.post("/test/mixed_literal_type", json=99)
        assert response.status_code == 422  # 99 is not in the allowed values
    
    def test_literal_return_validation_error(self, app):
        """Test Literal return type validation errors."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test method that returns invalid literal value
        response = client.post("/test/wrong_literal_return")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]