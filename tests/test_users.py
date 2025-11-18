from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/register", json={
        "username": "Ann",
        "email": "ann@example.com",
        "password": "12345"
    })
    assert response.status_code == 200
