# from fastapi.testclient import TestClient
# from main import app

# client = TestClient(app)


# def test_get_main_page():
#     response = client.get("/")
#     assert response.status_code == 200
#     assert "<html>" in response.text


# def test_health_check():
#     response = client.get("/health")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok"}
