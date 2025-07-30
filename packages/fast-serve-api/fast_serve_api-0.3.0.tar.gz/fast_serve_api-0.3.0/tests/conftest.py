import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a fresh FastAPI app for each test."""
    return FastAPI()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)