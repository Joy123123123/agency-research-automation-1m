"""
Security tests for web app query handling.
"""
import pytest

from scripts.web_app import app


def test_home_allows_normal_q_param():
    client = app.test_client()
    response = client.get("/", query_string={"q": "restaurant"})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "query",
    [
        {"q": "1"},
        {"q": "1'"},
        {"q": '1"'},
        {"q": "[1]"},
        {"q[]": "1"},
        {"q": "1`"},
        {"q": "1\\"},
        {"q": "1/*'*/"},
        {"q": "1/*!1111'*/"},
        {"q": "1'||'asd'||'"},
        {"q": "1' or '1'='1"},
        {"q": "1 or 1=1"},
        {"q": "'or''='"},
    ],
)
def test_home_blocks_suspicious_q_payloads(query):
    client = app.test_client()
    response = client.get("/", query_string=query)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid query parameter"}
