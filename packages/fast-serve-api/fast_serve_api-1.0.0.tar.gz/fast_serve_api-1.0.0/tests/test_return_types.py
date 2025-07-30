"""Tests for return type validation."""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.services import TestService


class TestBasicReturnTypes:
    """Test basic return type validation."""

    def test_string_return(self, app):
        """Test string return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/simple_string")
        assert response.status_code == 200
        assert response.json() == "Hello, World!"

    def test_int_return(self, app):
        """Test integer return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/add_numbers", json={"a": 5, "b": 3})
        assert response.status_code == 200
        assert response.json() == 8

    def test_float_return(self, app):
        """Test float return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/echo_float", json={"value": 3.14})
        assert response.status_code == 200
        assert response.json() == 3.14

    def test_bool_return(self, app):
        """Test boolean return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/toggle_boolean", json={"state": True})
        assert response.status_code == 200
        assert response.json() is False

    def test_none_return(self, app):
        """Test None return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/return_void")
        assert response.status_code == 200
        assert response.json() is None


class TestCollectionReturnTypes:
    """Test collection return type validation."""

    def test_list_return(self, app):
        """Test list return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/return_list", json={"count": 5})
        assert response.status_code == 200
        data = response.json()
        assert data == [0, 1, 2, 3, 4]

    def test_dict_return(self, app):
        """Test dict return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post(
            "/test/return_dict", json={"key": "name", "value": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data == {"name": "test"}

    def test_tuple_return(self, app):
        """Test tuple return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/return_tuple", json={"a": 42, "b": "answer"})
        assert response.status_code == 200
        data = response.json()
        assert data == [42, "answer"]  # Tuples are serialized as lists

    def test_set_return(self, app):
        """Test set return type."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/return_set")
        assert response.status_code == 200
        data = response.json()
        # Sets are serialized as lists in JSON
        assert isinstance(data, list)
        assert set(data) == {"apple", "banana", "cherry"}


class TestReturnTypeValidationErrors:
    """Test return type validation error handling."""

    def test_wrong_primitive_type(self, app):
        """Test wrong primitive type returns."""
        TestService.initialize(app)
        client = TestClient(app)

        # Should return int but returns string
        response = client.post("/test/wrong_type_string")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]
        assert "expected <class 'int'>" in data["message"]
        assert "got str" in data["message"]

        # Should return str but returns None
        response = client.post("/test/wrong_type_none")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]
        assert "expected <class 'str'>" in data["message"]
        assert "got NoneType" in data["message"]

        # Should return int but returns bool
        response = client.post("/test/wrong_type_bool")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]
        assert "expected <class 'int'>" in data["message"]
        assert "got bool" in data["message"]

    def test_wrong_list_type(self, app):
        """Test wrong list element types."""
        TestService.initialize(app)
        client = TestClient(app)

        # Should return List[str] but returns mixed types
        response = client.post("/test/wrong_list_type")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]

    def test_wrong_dict_type(self, app):
        """Test wrong dict value types."""
        TestService.initialize(app)
        client = TestClient(app)

        # Should return Dict[str, int] but returns wrong value types
        response = client.post("/test/wrong_dict_type")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]

    def test_wrong_set_type(self, app):
        """Test wrong set element types."""
        TestService.initialize(app)
        client = TestClient(app)

        # Should return Set[int] but returns mixed types
        response = client.post("/test/wrong_set_type")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Return type mismatch" in data["message"]


class TestComplexReturnTypes:
    """Test complex return type combinations."""

    def test_nested_collections_return(self, app):
        """Test nested collection return types."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post(
            "/test/complex_params",
            json={
                "text": "Complex test",
                "numbers": [1, 2, 3, 4, 5],
                "options": {"feature_a": True, "feature_b": False, "feature_c": True},
                "coordinates": [3.0, 4.0],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Complex test"
        assert data["sum"] == 15
        assert set(data["enabled_options"]) == {"feature_a", "feature_c"}
        assert data["distance"] == 5.0


class TestAnyReturnType:
    """Test Any return type validation."""

    def test_any_return_type(self):
        """Test endpoint with Any return type."""
        from fast_serve_api import FastServeApi

        class AnyReturnService(FastServeApi):
            @staticmethod
            def return_anything() -> Any:
                return {"foo": "bar", "num": 42}

        app = FastAPI()
        AnyReturnService.initialize(app)
        client = TestClient(app)

        response = client.post("/any_return/return_anything")
        assert response.status_code == 200
        data = response.json()
        assert data["foo"] == "bar"
        assert data["num"] == 42
