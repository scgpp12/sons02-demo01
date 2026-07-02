"""契約（上位/下位）→ 稼働実績 → 請求自動計算 → 粗利 の基幹フロー結合テスト。"""
from datetime import date, timedelta


def _engineer(client, h, name="技術者A"):
    return client.post(
        "/api/engineers", headers=h, json={"name": name, "status": "稼働中"}
    ).json()["id"]


def _client(client, h, name, btype):
    return client.post(
        "/api/clients", headers=h, json={"company_name": name, "business_type": btype}
    ).json()["id"]


def _contract(client, h, **over):
    payload = {
        "engineer_id": over.pop("engineer_id"),
        "contract_type": "上位",
        "unit_price": 700000,
        "settlement_lower": 140,
        "settlement_upper": 180,
        "overtime_rate": 4000,
        "deduction_rate": 4000,
        "start_date": "2026-04-01",
        "end_date": "2026-09-30",
        "status": "契約中",
    }
    payload.update(over)
    res = client.post("/api/contracts", headers=h, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_上位下位の作成と紐づけ(client, admin_headers):
    h = admin_headers
    eng = _engineer(client, h)
    end = _client(client, h, "エンド社", "エンド")
    bp = _client(client, h, "BP社", "BP")
    upper = _contract(client, h, engineer_id=eng, contract_type="上位", counterparty_client_id=end)
    lower = _contract(
        client,
        h,
        engineer_id=eng,
        contract_type="下位",
        counterparty_client_id=bp,
        parent_contract_id=upper["id"],
        unit_price=600000,
    )
    assert lower["parent_contract_id"] == upper["id"]
    assert upper["counterparty_name"] == "エンド社"


def test_請求自動計算_範囲内超過不足(client, admin_headers):
    h = admin_headers
    eng = _engineer(client, h)
    upper = _contract(client, h, engineer_id=eng)
    cid = upper["id"]

    # 範囲内(160h) → 単価そのまま
    client.post(
        "/api/work-records",
        headers=h,
        json={"contract_id": cid, "year_month": "2026-06-01", "worked_hours": 160},
    )
    invs = client.post("/api/invoices/generate", headers=h, json={"year_month": "2026-06-01"})
    assert invs.status_code == 200
    assert invs.json()[0]["billed_amount"] == 700000

    # 超過(190h) → 700000 + 10*4000 = 740000
    client.post(
        "/api/work-records",
        headers=h,
        json={"contract_id": cid, "year_month": "2026-07-01", "worked_hours": 190},
    )
    over = client.post("/api/invoices/generate", headers=h, json={"year_month": "2026-07-01"})
    amounts = {i["year_month"][:7]: i["billed_amount"] for i in over.json()}
    assert amounts["2026-07"] == 740000

    # 不足(130h) → 700000 - 10*4000 = 660000
    client.post(
        "/api/work-records",
        headers=h,
        json={"contract_id": cid, "year_month": "2026-08-01", "worked_hours": 130},
    )
    short = client.post("/api/invoices/generate", headers=h, json={"year_month": "2026-08-01"})
    amounts = {i["year_month"][:7]: i["billed_amount"] for i in short.json()}
    assert amounts["2026-08"] == 660000


def test_稼働実績はupsert(client, admin_headers):
    h = admin_headers
    eng = _engineer(client, h)
    cid = _contract(client, h, engineer_id=eng)["id"]
    body = {"contract_id": cid, "year_month": "2026-06-01", "worked_hours": 160}
    client.post("/api/work-records", headers=h, json=body)
    body["worked_hours"] = 175
    client.post("/api/work-records", headers=h, json=body)
    res = client.get(
        "/api/work-records", headers=h, params={"contract_id": cid, "year_month": "2026-06-01"}
    ).json()
    assert res["total"] == 1
    assert float(res["items"][0]["worked_hours"]) == 175.0


def test_粗利算出(client, admin_headers):
    h = admin_headers
    eng = _engineer(client, h)
    end = _client(client, h, "エンド社", "エンド")
    bp = _client(client, h, "BP社", "BP")
    upper = _contract(
        client, h, engineer_id=eng, counterparty_client_id=end, unit_price=700000
    )
    lower = _contract(
        client,
        h,
        engineer_id=eng,
        contract_type="下位",
        counterparty_client_id=bp,
        parent_contract_id=upper["id"],
        unit_price=600000,
    )
    # 両方160h（範囲内）→ 上位700000 / 下位600000 / 粗利100000
    for cid in (upper["id"], lower["id"]):
        client.post(
            "/api/work-records",
            headers=h,
            json={"contract_id": cid, "year_month": "2026-06-01", "worked_hours": 160},
        )
    gp = client.get(
        "/api/contracts/gross-profit", headers=h, params={"year_month": "2026-06-01"}
    ).json()
    assert len(gp) == 1
    row = gp[0]
    assert row["upper_billed"] == 700000
    assert row["lower_paid"] == 600000
    assert row["gross_profit"] == 100000
    assert abs(row["gross_margin"] - 14.3) < 0.1
    # 下位ちょうど1件: lower_count=1, lower_contract_id がセットされる
    assert row["lower_count"] == 1
    assert row["lower_contract_id"] == lower["id"]


def test_更新リマインド(client, admin_headers):
    h = admin_headers
    eng = _engineer(client, h)
    # 当月末で終了する契約 → リマインド対象
    today = date.today()
    month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    _contract(
        client,
        h,
        engineer_id=eng,
        start_date="2026-01-01",
        end_date=month_end.isoformat(),
        status="契約中",
    )
    # 1年後に終了する契約 → 対象外
    _contract(
        client,
        h,
        engineer_id=eng,
        start_date="2026-01-01",
        end_date=(today.replace(year=today.year + 1)).isoformat(),
        status="契約中",
    )
    res = client.get("/api/contracts/renewals", headers=h)
    assert res.status_code == 200
    ids_end = [c["end_date"] for c in res.json()]
    assert month_end.isoformat() in ids_end
    assert len(res.json()) == 1
