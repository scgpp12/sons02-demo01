"""認証・認可の結合テスト。"""


def test_login成功でトークン取得(client):
    res = client.post(
        "/api/auth/login", data={"username": "admin@example.com", "password": "admin123"}
    )
    assert res.status_code == 200
    assert res.json()["access_token"]
    assert res.json()["token_type"] == "bearer"


def test_login失敗_パスワード誤り(client):
    res = client.post(
        "/api/auth/login", data={"username": "admin@example.com", "password": "wrong"}
    )
    assert res.status_code == 401


def test_認証なしは401(client):
    res = client.get("/api/engineers")
    assert res.status_code == 401


def test_me_で現在ユーザー取得(client, admin_headers):
    res = client.get("/api/auth/me", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "admin@example.com"
    assert body["role"] == "admin"


def test_ユーザー管理はadmin専用_salesは403(client, make_user):
    sales = make_user("sales@example.com", "sales")
    res = client.get("/api/users", headers=sales)
    assert res.status_code == 403
