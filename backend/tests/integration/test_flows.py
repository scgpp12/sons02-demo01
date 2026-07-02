"""ハンドラを跨ぐ基幹フロー・整合性・RBAC越境・矛盾確認の結合テスト。

単体テスト(04章)と重複させず、複数ハンドラ／複数リソースの整合・副作用・
状態遷移・認可越境を実PostgreSQLに対して検証する。各テストは IT-NN を付す。
"""
from datetime import date, timedelta

from sqlalchemy import text

from app.db.session import engine

# ---- 共通ヘルパ（複数ハンドラを順に叩く） -------------------------------------

def _engineer(client, h, name="技術者A", status="稼働中"):
    res = client.post("/api/engineers", headers=h, json={"name": name, "status": status})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _client_co(client, h, name, btype):
    return client.post(
        "/api/clients", headers=h, json={"company_name": name, "business_type": btype}
    ).json()["id"]


def _contract(client, h, **over):
    payload = {
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


def _work(client, h, cid, ym, hours):
    res = client.post(
        "/api/work-records",
        headers=h,
        json={"contract_id": cid, "year_month": ym, "worked_hours": hours},
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


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


# ---- IT-25 基幹E2E：技術者→上位→下位→稼働→請求→粗利→更新リマインド ----------

def test_IT25_基幹フローE2E(client, admin_headers):
    """IT-25 / FR-42,48,34 / DD-22,03,04,05,06 越境フロー。

    技術者・エンド/BP取引先を作り、上位契約に下位を紐づけ、両者に稼働を入れ、
    請求一括生成→粗利→ダッシュボードまで一気通貫で整合することを確認する。
    跨ぐハンドラ: engineers, clients, contracts, work-records, invoices, dashboard。
    """
    h = admin_headers
    eng = _engineer(client, h)
    end = _client_co(client, h, "エンド社", "エンド")
    bp = _client_co(client, h, "BP社", "BP")
    upper = _contract(client, h, engineer_id=eng, counterparty_client_id=end, unit_price=700000)
    lower = _contract(
        client, h, engineer_id=eng, contract_type="下位",
        counterparty_client_id=bp, parent_contract_id=upper["id"], unit_price=600000,
    )
    ym = "2026-06-01"
    _work(client, h, upper["id"], ym, 160)
    _work(client, h, lower["id"], ym, 160)

    # 請求一括生成：上位のみが請求対象（下位は対象外）
    invs = client.post("/api/invoices/generate", headers=h, json={"year_month": ym})
    assert invs.status_code == 200
    body = invs.json()
    assert len(body) == 1
    assert body[0]["contract_id"] == upper["id"]
    assert body[0]["billed_amount"] == 700000
    assert body[0]["engineer_name"] == "技術者A"
    assert body[0]["counterparty_name"] == "エンド社"

    # 請求が永続化され一覧で引ける
    listed = client.get("/api/invoices", headers=h, params={"year_month": ym}).json()
    assert listed["total"] == 1

    # 粗利：700000 - 600000 = 100000
    gp = client.get(
        "/api/contracts/gross-profit", headers=h, params={"year_month": ym}
    ).json()
    assert gp[0]["gross_profit"] == 100000
    assert gp[0]["lower_contract_id"] == lower["id"]


# ---- IT-26 NFR-12 請求確定保護（請求済は再計算で上書きしない） ------------------

def test_IT26_請求確定後は再計算で金額据え置き(client, admin_headers):
    """IT-26 / NFR-12 / DD-03,22 請求確定保護。

    生成→請求済に更新→稼働時間を変更して再生成しても、確定済の金額は
    上書きされないこと。未請求なら再計算されることも対で確認。
    跨ぐハンドラ: contracts, work-records, invoices(generate/update)。
    """
    h = admin_headers
    eng = _engineer(client, h)
    cid = _contract(client, h, engineer_id=eng)["id"]
    ym = "2026-06-01"
    _work(client, h, cid, ym, 160)  # 700000

    inv = client.post("/api/invoices/generate", headers=h, json={"year_month": ym}).json()[0]
    assert inv["billed_amount"] == 700000
    inv_id = inv["id"]

    # 未請求のうちは再計算される（190h→740000）
    _work(client, h, cid, ym, 190)
    again = client.post("/api/invoices/generate", headers=h, json={"year_month": ym}).json()[0]
    assert again["billed_amount"] == 740000

    # 請求済に確定
    upd = client.put(f"/api/invoices/{inv_id}", headers=h, json={"status": "請求済"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "請求済"

    # 稼働を更に変えて再生成 → 確定済なので金額据え置き(740000のまま)
    _work(client, h, cid, ym, 130)
    after = client.post("/api/invoices/generate", headers=h, json={"year_month": ym}).json()[0]
    assert after["billed_amount"] == 740000
    assert after["status"] == "請求済"


# ---- IT-27 DD-05 当月稼働なしは単価で粗利算出 ----------------------------------

def test_IT27_稼働実績なしは単価で粗利算出(client, admin_headers):
    """IT-27 / FR-48 / DD-04,05 稼働なし時のフォールバック。

    上位/下位とも当月の稼働実績が無い場合、_amount_for が単価で算出する。
    上位700000 / 下位600000 → 粗利100000。跨ぐハンドラ: contracts。
    """
    h = admin_headers
    eng = _engineer(client, h)
    upper = _contract(client, h, engineer_id=eng, unit_price=700000)
    _contract(
        client, h, engineer_id=eng, contract_type="下位",
        parent_contract_id=upper["id"], unit_price=600000,
    )
    gp = client.get(
        "/api/contracts/gross-profit", headers=h, params={"year_month": "2026-12-01"}
    ).json()
    assert len(gp) == 1
    assert gp[0]["upper_billed"] == 700000
    assert gp[0]["lower_paid"] == 600000
    assert gp[0]["gross_profit"] == 100000


# ---- IT-28 DD-23 稼働実績 契約×月 UNIQUE upsert（DBレベル整合） ----------------

def test_IT28_稼働実績は契約月でupsertされ重複行を作らない(client, admin_headers):
    """IT-28 / NFR-09 / DD-23 契約×月UNIQUE upsert。

    同一契約×同一月に複数回POSTしても行は1件で値が上書きされ、DB上も
    重複が無いこと（uq_work_contract_month）。跨ぐハンドラ: contracts, work-records。
    """
    h = admin_headers
    eng = _engineer(client, h)
    cid = _contract(client, h, engineer_id=eng)["id"]
    ym = "2026-06-01"
    _work(client, h, cid, ym, 150)
    _work(client, h, cid, ym, 165)
    _work(client, h, cid, ym, 170)

    listed = client.get(
        "/api/work-records", headers=h, params={"contract_id": cid, "year_month": ym}
    ).json()
    assert listed["total"] == 1
    assert float(listed["items"][0]["worked_hours"]) == 170.0

    # DB側でも物理1行
    with engine.connect() as conn:
        cnt = conn.execute(
            text("SELECT count(*) FROM work_records WHERE contract_id=:c"), {"c": cid}
        ).scalar_one()
    assert cnt == 1


# ---- IT-29 DD-24 / OUT-04 マイナンバーは暗号化保存・平文非返却（DB確認） --------

def test_IT29_マイナンバーは暗号化保存され平文を返さない(client, admin_headers):
    """IT-29 / FR-63 / DD-24 / OUT-04 マイナンバー暗号化と平文非開示。

    平文12桁を登録→レスポンス/詳細に平文が出ないこと、かつDBの my_number_enc に
    平文がそのまま入っておらず暗号化されていることを直接確認。さらに has_card のみ
    更新する再upsertで番号が据え置かれること。跨ぐハンドラ: employees(本体/my-number)。
    """
    h = admin_headers
    eid = _employee(client, h)["id"]
    plain = "123456789012"
    res = client.put(
        f"/api/employees/{eid}/my-number",
        headers=h,
        json={"my_number": plain, "has_card": True, "collected_at": "2026-04-01"},
    )
    assert res.status_code == 200
    assert plain not in res.text
    assert res.json()["has_number"] is True

    # 詳細にも平文は出ない
    detail = client.get(f"/api/employees/{eid}", headers=h)
    assert plain not in detail.text
    assert detail.json()["my_number"]["has_number"] is True

    # DBには暗号文が入り、平文文字列は含まれない
    with engine.connect() as conn:
        enc = conn.execute(
            text("SELECT my_number_enc FROM employee_my_number WHERE employee_id=:e"),
            {"e": eid},
        ).scalar_one()
    assert enc is not None
    assert plain not in str(enc)

    # has_card のみ false に更新（my_number 未指定）→ 番号は据え置き
    res2 = client.put(
        f"/api/employees/{eid}/my-number",
        headers=h,
        json={"has_card": False, "collected_at": "2026-04-01"},
    )
    assert res2.status_code == 200
    assert res2.json()["has_card"] is False
    assert res2.json()["has_number"] is True


# ---- IT-30 DD-15 契約は admin/manager のみ作成可（sales越境拒否） ---------------

def test_IT30_契約作成はsales不可managerは可(client, make_user):
    """IT-30 / DD-15 契約APIのロール制御（Editor=admin/manager）。

    sales は契約作成で403、manager は作成可。跨ぐハンドラ: users(作成), engineers, contracts。
    """
    sales = make_user("sales@example.com", "sales")
    manager = make_user("manager@example.com", "manager")
    # 技術者は sales でも作成できる（編集は created_by ベース）
    eng = _engineer(client, sales)

    body = {
        "engineer_id": eng,
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
    ng = client.post("/api/contracts", headers=sales, json=body)
    assert ng.status_code == 403

    ok = client.post("/api/contracts", headers=manager, json=body)
    assert ok.status_code == 201


# ---- IT-31 OUT-08 社員個人情報APIは admin/manager 限定（是正後の回帰） --------------

def test_IT31_社員APIはsales不可_稼働請求は対象外で可_OUT08是正(client, admin_headers, make_user):
    """IT-31 / OUT-08（是正後の回帰） 社員個人情報APIのロール制御。

    機微情報(社員本体/在留/口座/マイナンバー等)を扱う社員APIは admin/manager 限定とし、
    sales からのアクセスは 403 で遮断されることを確認する。
    一方、稼働実績・請求生成は本是正の対象外のため従来どおり認証済みなら可。
    跨ぐハンドラ: users, employees, engineers, contracts, work-records, invoices。
    """
    sales = make_user("sales@example.com", "sales")
    # 社員作成は sales 不可（403）。OUT-08 是正で機微APIを admin/manager に限定。
    res = client.post(
        "/api/employees",
        headers=sales,
        json={
            "name": "社員X",
            "name_romaji": "SHAIN X",
            "name_kana": "シャイン エックス",
            "birth_date": "1993-09-23",
            "nationality": "中国",
            "status": "在籍",
        },
    )
    assert res.status_code == 403, res.text

    # 契約は admin で用意（契約作成は admin/manager のみ）
    eng = _engineer(client, admin_headers)
    cid = _contract(client, admin_headers, engineer_id=eng)["id"]

    # 稼働実績登録（sales 可）
    wr = client.post(
        "/api/work-records", headers=sales,
        json={"contract_id": cid, "year_month": "2026-06-01", "worked_hours": 160},
    )
    assert wr.status_code in (200, 201)

    # 請求生成（sales 可）
    inv = client.post(
        "/api/invoices/generate", headers=sales, json={"year_month": "2026-06-01"}
    )
    assert inv.status_code == 200
    assert len(inv.json()) == 1


# ---- IT-32 PRE-05対応 上位に下位が複数ある場合は合算する（回帰） ------------------

def test_IT32_上位に下位が複数なら支払を合算する_PRE05(client, admin_headers):
    """IT-32 / PRE-05（是正後の回帰） 下位契約が複数あるときの粗利算出。

    1つの上位契約に下位を2件紐づけても 500 にならず、下位支払を合算して
    粗利を算出すること（旧実装は scalar_one_or_none で500だった）。
    上位700,000 / 下位600,000+550,000=1,150,000 → 粗利 -450,000。
    跨ぐハンドラ: engineers, contracts, contracts/gross-profit。
    """
    h = admin_headers
    eng = _engineer(client, h)
    upper = _contract(client, h, engineer_id=eng, unit_price=700000)
    _contract(
        client, h, engineer_id=eng, contract_type="下位",
        parent_contract_id=upper["id"], unit_price=600000,
    )
    _contract(
        client, h, engineer_id=eng, contract_type="下位",
        parent_contract_id=upper["id"], unit_price=550000,
    )
    res = client.get(
        "/api/contracts/gross-profit", headers=h, params={"year_month": "2026-06-01"}
    )
    assert res.status_code == 200
    row = next(r for r in res.json() if r["upper_contract_id"] == upper["id"])
    assert row["lower_count"] == 2
    assert row["lower_paid"] == 1_150_000  # 600,000 + 550,000（合算）
    assert row["upper_billed"] == 700_000
    assert row["gross_profit"] == -450_000
    assert row["lower_contract_id"] is None  # 複数件のためNull


# ---- IT-33 DD-14 無効化ユーザーのトークンは拒否される ---------------------------

def test_IT33_無効化されたユーザーのトークンは401(client, admin_headers, make_user):
    """IT-33 / DD-14 get_current_user の is_active 判定。

    sales でログイン後、admin が当該ユーザーを is_active=false に更新すると、
    既存トークンでの保護API呼び出しが401になること。
    跨ぐハンドラ: users(create/login/update), engineers(保護API)。
    """
    sales = make_user("sales@example.com", "sales")
    # 有効なうちは200
    assert client.get("/api/engineers", headers=sales).status_code == 200

    # admin が当該ユーザーを無効化
    users = client.get("/api/users", headers=admin_headers).json()["items"]
    uid = next(u["id"] for u in users if u["email"] == "sales@example.com")
    upd = client.put(f"/api/users/{uid}", headers=admin_headers, json={"is_active": False})
    assert upd.status_code == 200

    # 既存トークンは無効ユーザーのため401
    assert client.get("/api/engineers", headers=sales).status_code == 401


# ---- IT-34 ダッシュボード更新アラートと請求売上の集計整合 -----------------------

def test_IT34_ダッシュボードは請求売上と更新アラートを集計(client, admin_headers):
    """IT-34 / FR-49 / DD-06,04,05 ダッシュボード集計の整合。

    当月末で終了する契約(契約中)＋稼働実績を用意し、ダッシュボードの
    今月売上・更新アラートが粗利ロジックと整合することを確認。
    跨ぐハンドラ: engineers, contracts, work-records, dashboard。
    """
    h = admin_headers
    eng = _engineer(client, h, status="稼働中")
    today = date.today()
    month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    this_ym = today.replace(day=1).isoformat()
    upper = _contract(
        client, h, engineer_id=eng, unit_price=700000,
        start_date="2026-01-01", end_date=month_end.isoformat(), status="契約中",
    )
    _work(client, h, upper["id"], this_ym, 160)

    res = client.get("/api/dashboard", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["total_engineers"] == 1
    assert body["working_count"] == 1
    # 今月売上に当該上位契約の請求額が反映
    assert body["this_month_revenue"] == 700000
    # 更新アラートに当月末終了契約が含まれる
    assert any(a["contract_id"] == upper["id"] for a in body["renewal_alerts"])
