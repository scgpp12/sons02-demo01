"""社員管理（本体＋サブリソース＋マイナンバー暗号化）の結合テスト。"""


def _employee(client, h, **over):
    payload = {
        "name": "張 偉",
        "name_romaji": "ZHANG WEI",
        "name_kana": "チョウ イ",
        "birth_date": "1993-09-23",
        "nationality": "中国",
        "status": "在籍",
    }
    payload.update(over)
    res = client.post("/api/employees", headers=h, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_社員作成と詳細取得(client, admin_headers):
    emp = _employee(client, admin_headers)
    detail = client.get(f"/api/employees/{emp['id']}", headers=admin_headers).json()
    assert detail["name_romaji"] == "ZHANG WEI"
    assert detail["residence_cards"] == []
    assert detail["my_number"] is None


def test_サブリソース追加と集約(client, admin_headers):
    h = admin_headers
    eid = _employee(client, h)["id"]
    client.post(
        f"/api/employees/{eid}/residence-cards",
        headers=h,
        json={
            "residence_status": "技術・人文知識・国際業務",
            "card_number": "TR123",
            "expiry_date": "2027-03-31",
            "is_current": True,
        },
    )
    client.post(
        f"/api/employees/{eid}/bank-accounts",
        headers=h,
        json={"bank_name": "みずほ", "account_number": "1234567", "is_primary": True},
    )
    client.post(
        f"/api/employees/{eid}/emergency-contacts",
        headers=h,
        json={"kind": "母国親族", "contact_name": "張 父", "phone": "000"},
    )
    detail = client.get(f"/api/employees/{eid}", headers=h).json()
    assert len(detail["residence_cards"]) == 1
    assert len(detail["bank_accounts"]) == 1
    assert len(detail["emergency_contacts"]) == 1


def test_マイナンバーは平文を返さない(client, admin_headers):
    h = admin_headers
    eid = _employee(client, h)["id"]
    res = client.put(
        f"/api/employees/{eid}/my-number",
        headers=h,
        json={"my_number": "123456789012", "has_card": True, "collected_at": "2026-04-01"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["has_number"] is True
    assert body["has_card"] is True
    # レスポンスに平文が含まれないこと
    assert "123456789012" not in res.text
    assert "my_number" not in body


def test_在留期限アラート抽出(client, admin_headers):
    h = admin_headers
    eid = _employee(client, h)["id"]
    # 近い満了
    client.post(
        f"/api/employees/{eid}/residence-cards",
        headers=h,
        json={
            "residence_status": "技人国",
            "card_number": "SOON",
            "expiry_date": "2026-01-01",
            "is_current": True,
        },
    )
    res = client.get(
        "/api/employees/expiring-residence", headers=h, params={"within_days": 365}
    )
    assert res.status_code == 200
    assert any(c["card_number"] == "SOON" for c in res.json())


def test_社員個人情報APIはsales不可managerは可_OUT08是正(client, admin_headers, make_user):
    """OUT-08 是正の回帰: 社員個人情報（本体/詳細/マイナンバー/口座）は
    admin/manager 限定。sales は 403、manager は許可されることを確認する。"""
    eid = _employee(client, admin_headers)["id"]
    sales = make_user("sales_emp@example.com", "sales")
    manager = make_user("manager_emp@example.com", "manager")

    # --- sales は社員個人情報にアクセスできない（403） ---
    assert client.get("/api/employees", headers=sales).status_code == 403
    assert client.get(f"/api/employees/{eid}", headers=sales).status_code == 403
    assert client.get(f"/api/employees/{eid}/my-number", headers=sales).status_code == 403
    assert (
        client.post(
            f"/api/employees/{eid}/bank-accounts",
            headers=sales,
            json={"bank_name": "X銀行", "account_number": "1234567", "is_primary": True},
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"/api/employees/{eid}/my-number",
            headers=sales,
            json={"my_number": "123456789012", "has_card": True, "collected_at": "2026-04-01"},
        ).status_code
        == 403
    )

    # --- manager は許可される ---
    assert client.get("/api/employees", headers=manager).status_code == 200
    assert client.get(f"/api/employees/{eid}", headers=manager).status_code == 200
    assert client.get(f"/api/employees/{eid}/my-number", headers=manager).status_code == 200
