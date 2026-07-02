"""ダッシュボード集計の結合テスト。"""


def test_稼働率と待機人数(client, admin_headers):
    h = admin_headers
    # 稼働中2名・待機1名 → 稼働率 約66.7%
    client.post("/api/engineers", headers=h, json={"name": "A", "status": "稼働中"})
    client.post("/api/engineers", headers=h, json={"name": "B", "status": "稼働中"})
    client.post("/api/engineers", headers=h, json={"name": "C", "status": "待機"})

    res = client.get("/api/dashboard", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["total_engineers"] == 3
    assert body["working_count"] == 2
    assert body["waiting_count"] == 1
    assert abs(body["utilization_rate"] - 66.7) < 0.1
    assert isinstance(body["monthly_trend"], list)
    assert isinstance(body["renewal_alerts"], list)


def test_空でもエラーにならない(client, admin_headers):
    res = client.get("/api/dashboard", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["total_engineers"] == 0
    assert res.json()["utilization_rate"] == 0
