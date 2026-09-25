"""
Security tests for web app query handling.
"""
from scripts.web_app import app


def test_home_allows_normal_q_param():
    client = app.test_client()
    response = client.get("/", query_string={"q": "restaurant"})
    assert response.status_code == 200


def test_home_blocks_sqli_q_param():
    client = app.test_client()
    response = client.get("/", query_string={"q": "1' or '1'='1"})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid query parameter"}
