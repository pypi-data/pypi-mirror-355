"""Tests for collection type parameters and returns."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestListTypes:
    """Test List type handling."""
    
    def test_list_parameter(self, app):
        """Test list parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/process_boolean_list", json={
            "values": [True, False, True, True, False]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert data["true_count"] == 3
        assert data["false_count"] == 2
        assert data["all_true"] is False
        assert data["any_true"] is True
    
    def test_empty_list(self, app):
        """Test empty list handling."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/process_boolean_list", json={"values": []})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["true_count"] == 0
        assert data["false_count"] == 0
        assert data["all_true"] is True  # all([]) returns True
        assert data["any_true"] is False  # any([]) returns False
    
    def test_list_type_validation(self, app):
        """Test list element type validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test List[bool] with mixed types (should fail)
        response = client.post("/test/process_boolean_list", json={
            "values": [True, False, "not a bool"]
        })
        assert response.status_code == 422  # Should fail validation
        
        # Test List[bool] with integers (should fail - no coercion in lists)
        response = client.post("/test/process_boolean_list", json={
            "values": [1, 0, 2]
        })
        assert response.status_code == 422  # Should fail validation
        
        # Test List[str] with valid strings
        response = client.post("/test/process_string_list", json={
            "words": ["hello", "world", "test"]
        })
        assert response.status_code == 200
        assert response.json() == "hello world test"
        
        # Test List[str] with numbers (should fail)
        response = client.post("/test/process_string_list", json={
            "words": [1, 2, 3]
        })
        assert response.status_code == 422  # Should fail validation
        
        # Test List[str] with mixed types (should fail)
        response = client.post("/test/process_string_list", json={
            "words": ["hello", 123, "world"]
        })
        assert response.status_code == 422  # Should fail validation
        
        # Test List[int] with valid integers
        response = client.post("/test/process_int_list", json={
            "numbers": [10, 20, 30]
        })
        assert response.status_code == 200
        assert response.json() == 60
        
        # Test List[int] with strings (should fail)
        response = client.post("/test/process_int_list", json={
            "numbers": ["ten", "twenty", "thirty"]
        })
        assert response.status_code == 422  # Should fail validation
        
        # Test List[int] with floats (Pydantic may coerce these)
        response = client.post("/test/process_int_list", json={
            "numbers": [10.0, 20.0, 30.0]
        })
        assert response.status_code == 200  # Pydantic coerces floats to ints
        assert response.json() == 60


class TestSetTypes:
    """Test Set type handling."""
    
    def test_set_return(self, app):
        """Test returning a set."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/return_set")
        assert response.status_code == 200
        data = response.json()
        # Sets are serialized as lists in JSON
        assert isinstance(data, list)
        assert set(data) == {"apple", "banana", "cherry"}
    
    def test_set_parameter(self, app):
        """Test set parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test set parameter with object notation
        response = client.post("/test/echo_set", json={"values": [1, 2, 3, 2, 1]})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert set(data) == {1, 2, 3}  # Duplicates removed
        
        # Test set parameter with raw value (single field) - comes as list
        response = client.post("/test/echo_set", json=[4, 5, 6, 5])
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert set(data) == {4, 5, 6}
        
        # Test processing set
        response = client.post("/test/process_set", json={
            "items": ["apple", "orange", "banana", "apple"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3  # Duplicates removed
        assert data["items"] == ["apple", "banana", "orange"]  # Sorted
        assert data["has_apple"] is True
        
        # Test empty set
        response = client.post("/test/echo_set", json={"values": []})
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_set_type_validation(self, app):
        """Test set element type validation."""
        TestService.initialize(app)
        client = TestClient(app)
        
        # Test Set[int] with strings (should fail)
        response = client.post("/test/echo_set", json={"values": ["one", "two", "three"]})
        assert response.status_code == 422  # Should fail validation
        
        # Test Set[int] with mixed types (should fail)
        response = client.post("/test/echo_set", json={"values": [1, 2, "three", 4]})
        assert response.status_code == 422  # Should fail validation
        
        # Test Set[str] with valid strings
        response = client.post("/test/process_set", json={
            "items": ["apple", "banana", "cherry"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        
        # Test Set[str] with numbers (should fail)
        response = client.post("/test/process_set", json={"items": [1, 2, 3]})
        assert response.status_code == 422  # Should fail validation
        
        # Test Set[str] with mixed types (should fail)
        response = client.post("/test/process_set", json={
            "items": ["apple", 123, "cherry"]
        })
        assert response.status_code == 422  # Should fail validation


class TestDictTypes:
    """Test Dict type handling."""
    
    def test_dict_return(self, app):
        """Test dict return type."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/return_dict", json={"key": "test", "value": "data"})
        assert response.status_code == 200
        assert response.json() == {"test": "data"}
    
    def test_dict_parameter(self, app):
        """Test dict parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/complex_params", json={
            "text": "Test",
            "numbers": [1, 2, 3],
            "options": {"feature_a": True, "feature_b": False, "feature_c": True},
            "coordinates": [0.0, 0.0]
        })
        assert response.status_code == 200
        data = response.json()
        assert set(data["enabled_options"]) == {"feature_a", "feature_c"}


class TestTupleTypes:
    """Test Tuple type handling."""
    
    def test_tuple_return(self, app):
        """Test tuple return type."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/return_tuple", json={"a": 42, "b": "answer"})
        assert response.status_code == 200
        data = response.json()
        assert data == [42, "answer"]  # Tuples are serialized as lists
    
    def test_tuple_parameter(self, app):
        """Test tuple parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        response = client.post("/test/complex_params", json={
            "text": "Distance test",
            "numbers": [1],
            "options": {},
            "coordinates": [3.0, 4.0]  # Tuple parameter as list
        })
        assert response.status_code == 200
        data = response.json()
        assert data["distance"] == 5.0  # sqrt(3^2 + 4^2) = 5


class TestComplexCollections:
    """Test complex collection combinations."""
    
    def test_complex_nested_collections(self, app):
        """Test complex nested collection parameters."""
        TestService.initialize(app)
        client = TestClient(app)
        
        request_data = {
            "text": "Complex test",
            "numbers": [1, 2, 3, 4, 5],
            "options": {
                "feature_a": True,
                "feature_b": False,
                "feature_c": True,
                "feature_d": True
            },
            "coordinates": [3.0, 4.0]
        }
        
        response = client.post("/test/complex_params", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Complex test"
        assert data["sum"] == 15
        assert set(data["enabled_options"]) == {"feature_a", "feature_c", "feature_d"}
        assert data["distance"] == 5.0