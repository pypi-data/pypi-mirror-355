"""Tests for error handling in FastServeApi."""

from fastapi.testclient import TestClient
import pytest

from tests.services import TestService


class TestExceptionHandling:
    """Test exception handling in endpoints."""

    def test_endpoint_exception(self, app):
        """Test error handling when endpoint raises exception."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/raise_error", json={"message": "Test error"})
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Test error" in data["message"]
        assert "stack_trace" in data
        assert "status_code" in data
        assert data["status_code"] == 500

    def test_exception_stacktrace(self, app):
        """Test that stack trace is included in error response."""
        TestService.initialize(app)
        client = TestClient(app)

        response = client.post("/test/raise_error", json={"message": "Detailed error"})
        assert response.status_code == 500
        data = response.json()
        assert "ValueError: Detailed error" in data["stack_trace"]
        assert "raise_error" in data["stack_trace"]


class TestValidationErrors:
    """Test parameter validation errors."""

    def test_missing_required_parameter(self, app):
        """Test missing required parameter."""
        TestService.initialize(app)
        client = TestClient(app)

        # No JSON body at all
        response = client.post("/test/echo_string")
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_wrong_parameter_type(self, app):
        """Test wrong parameter type."""
        TestService.initialize(app)
        client = TestClient(app)

        # String instead of int
        response = client.post("/test/add_numbers", json={"a": "not_a_number", "b": 3})
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

        # Object instead of primitive
        response = client.post(
            "/test/echo_string", json={"message": {"nested": "object"}}
        )
        assert response.status_code == 422

    def test_extra_parameters(self, app):
        """Test that extra parameters are ignored."""
        TestService.initialize(app)
        client = TestClient(app)

        # Extra parameters should be ignored, not cause errors
        response = client.post(
            "/test/echo_string",
            json={"message": "Hello", "extra_field": "ignored", "another_extra": 123},
        )
        assert response.status_code == 200
        assert response.json() == "Hello"


class TestInitializationErrors:
    """Test initialization and setup errors."""

    def test_not_initialized_error(self):
        """Test that accessing _register_endpoints without initialization raises error."""
        from fast_serve_api import FastServeApi

        class UninitializedService(FastServeApi):
            @staticmethod
            def test_method() -> str:
                return "test"

        # Try to register endpoints without initialization
        with pytest.raises(ValueError) as exc_info:
            UninitializedService._register_endpoints()

        assert "must be initialized with a FastAPI app instance" in str(exc_info.value)

    def test_get_app_not_initialized(self):
        """Test get_app raises error when not initialized."""
        from fast_serve_api import FastServeApi

        class AnotherUninitializedService(FastServeApi):
            pass

        with pytest.raises(ValueError) as exc_info:
            AnotherUninitializedService.get_app()

        assert "has not been initialized" in str(exc_info.value)

    def test_get_app_after_initialization(self, app):
        """Test get_app returns app when initialized."""
        from fast_serve_api import FastServeApi

        class InitializedService(FastServeApi):
            pass

        InitializedService.initialize(app)
        assert InitializedService.get_app() == app
