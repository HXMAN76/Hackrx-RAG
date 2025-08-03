'''
# File: app/test_routes.py
# This file contains tests for the FastAPI application routes.
# It checks if the route for document processing exists.
# This is a simple test to ensure the API is set up correctly.'''

from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from main import app

def test_route_exists():
    client = TestClient(app)
    routes = [route.path for route in app.routes]
    assert "/api/v1/hackrx/document" in routes
