"""技術者CRUD・フィルタ・RBACの結合テスト。"""


def _create(client, headers, **over):
    payload = {
        "name": "山田 太郎",
        "name_kana": "ヤマダ タロウ",
        "skills": [{"name": "Python", "years": 5}],
        "unit_price": 600000,
        "status": "待機",
        "remote_ok": True,
    }
    payload.update(over)
    return client.post("/api/engineers", headers=headers, json=payload)


def test_作成と取得(client, admin_headers):
    res = _create(client, admin_headers)
    assert res.status_code == 201, res.text
    eid = res.json()["id"]
    got = client.get(f"/api/engineers/{eid}", headers=admin_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "山田 太郎"
    assert got.json()["skills"][0]["name"] == "Python"


def test_一覧ページング(client, admin_headers):
    for i in range(3):
        _create(client, admin_headers, name=f"技術者{i}")
    res = client.get("/api/engineers", headers=admin_headers, params={"page_size": 2})
    body = res.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page_size"] == 2


def test_ステータスフィルタ(client, admin_headers):
    _create(client, admin_headers, status="待機")
    _create(client, admin_headers, status="稼働中")
    res = client.get("/api/engineers", headers=admin_headers, params={"status": "稼働中"})
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "稼働中"


def test_スキルフィルタ(client, admin_headers):
    _create(client, admin_headers, skills=[{"name": "Python", "years": 3}])
    _create(client, admin_headers, skills=[{"name": "Java", "years": 3}])
    res = client.get("/api/engineers", headers=admin_headers, params={"skill": "Java"})
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["skills"][0]["name"] == "Java"


def test_更新(client, admin_headers):
    eid = _create(client, admin_headers).json()["id"]
    res = client.put(
        f"/api/engineers/{eid}", headers=admin_headers, json={"status": "稼働中"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "稼働中"


def test_削除(client, admin_headers):
    eid = _create(client, admin_headers).json()["id"]
    assert client.delete(f"/api/engineers/{eid}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/engineers/{eid}", headers=admin_headers).status_code == 404


def test_RBAC_salesは他人の登録分を編集不可(client, admin_headers, make_user):
    sales1 = make_user("sales1@example.com", "sales")
    sales2 = make_user("sales2@example.com", "sales")
    # sales1 が作成
    eid = _create(client, sales1).json()["id"]
    # sales2 は編集できない（403）
    res = client.put(f"/api/engineers/{eid}", headers=sales2, json={"status": "稼働中"})
    assert res.status_code == 403
    # 本人(sales1)は編集できる
    ok = client.put(f"/api/engineers/{eid}", headers=sales1, json={"status": "稼働中"})
    assert ok.status_code == 200


def test_RBAC_managerは他人の登録分も編集可(client, make_user):
    sales = make_user("sales@example.com", "sales")
    manager = make_user("manager@example.com", "manager")
    eid = _create(client, sales).json()["id"]
    res = client.put(f"/api/engineers/{eid}", headers=manager, json={"status": "離脱"})
    assert res.status_code == 200
