# tests/test_auth.py
def test_can_get_token(client):
    res = client.post("/auth/token")
    assert res.status_code == 200
    assert "access_token" in res.get_json()

