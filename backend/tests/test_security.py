"""パスワードハッシュ(bcrypt)とJWTの単体テスト。

対象: DD-09 hash_password / DD-10 verify_password / DD-11 create_access_token /
      DD-12 decode_access_token / DD-13 _to_bytes
純粋関数（乱数salt・時刻依存はあるがIO非依存）。JWT_SECRETはconftestで固定。
"""
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.core.security import (
    _to_bytes,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------- DD-13 _to_bytes ----------------
class TestToBytes:
    def test_UT_30_短い文字列はそのままUTF8(self):
        """UT-30 / DD-13 / 正常: ASCII文字列はそのままUTF-8バイト列。"""
        assert _to_bytes("password") == b"password"

    def test_UT_31_72バイト超は切詰(self):
        """UT-31 / DD-13 / 境界: 73文字(ASCII=73バイト)は先頭72バイトに切り詰め。"""
        plain = "a" * 73
        result = _to_bytes(plain)
        assert len(result) == 72
        assert result == b"a" * 72

    def test_UT_32_72バイトちょうど(self):
        """UT-32 / DD-13 / 境界: 72バイトちょうどは全て保持。"""
        plain = "a" * 72
        assert len(_to_bytes(plain)) == 72

    def test_UT_33_空文字(self):
        """UT-33 / DD-13 / 異常: 空文字は空バイト列。"""
        assert _to_bytes("") == b""

    def test_UT_34_マルチバイト境界が壊れる_指摘事項(self):
        """UT-34 / DD-13 / 異常: 日本語(3バイト/字)で72バイト切詰めると文字境界が崩れる。

        '日' は UTF-8 で 3バイト。25文字=75バイト→72バイトで切ると24文字(72B)きれいに割れるが、
        24文字+1バイト残しのケースを作ると末尾が不正バイトになることを確認する（設計注記の検証）。
        """
        # 24文字(72バイト)は割り切れるが、'あ'(3B)を23個 + 'a'(1B)*3 = 72バイト 等は割れる。
        # 23文字の日本語=69バイト + 2バイト目で切れる文字を作る
        plain = "あ" * 24 + "い"  # 24*3 + 3 = 75バイト → 72で切ると 'い' が消え 'あ'*24 が残る
        result = _to_bytes(plain)
        assert len(result) == 72
        # ここは割り切れるケース（72バイト=あ*24）。デコードは成功する。
        assert result.decode("utf-8") == "あ" * 24
        # 境界が割り切れないケース: 'あ'*23(69B) + 'a'*4(4B)=73バイト → 72で切ると 'a'*3
        plain2 = "あ" * 23 + "aaaa"
        result2 = _to_bytes(plain2)
        assert len(result2) == 72
        assert result2.decode("utf-8") == "あ" * 23 + "aaa"
        # 真に文字を割るケース: 'あ'*24(72B) + 'a' → 72Bで切れ 'a' は落ちる（安全）。
        # 'a' + 'あ'*24 = 1 + 72 = 73B → 72で切ると 'a' + 'あ'*23(69B)=70B + 'あ'の先頭2バイト
        plain3 = "a" + "あ" * 24
        result3 = _to_bytes(plain3)
        assert len(result3) == 72
        # 末尾2バイトは不完全なマルチバイト → そのままdecodeすると UnicodeDecodeError
        import pytest

        with pytest.raises(UnicodeDecodeError):
            result3.decode("utf-8")


# ---------------- DD-09 / DD-10 ----------------
class TestPasswordHash:
    def test_UT_35_正しいPWはTrue(self):
        """UT-35 / DD-09,DD-10 / 正常: hashした平文をverifyするとTrue。"""
        h = hash_password("Secret123")
        assert verify_password("Secret123", h) is True

    def test_UT_36_誤りPWはFalse(self):
        """UT-36 / DD-10 / 正常: 異なる平文はFalse。"""
        h = hash_password("Secret123")
        assert verify_password("wrong", h) is False

    def test_UT_37_同一PWの2回hashは別値だが両方検証可(self):
        """UT-37 / DD-09 / 正常: saltにより毎回異なるハッシュ、両方verify可。"""
        h1 = hash_password("samepw")
        h2 = hash_password("samepw")
        assert h1 != h2
        assert verify_password("samepw", h1) is True
        assert verify_password("samepw", h2) is True

    def test_UT_38_不正なhashed文字列はFalse(self):
        """UT-38 / DD-10 / 異常: 不正なハッシュ文字列でも例外を出さずFalse。"""
        assert verify_password("any", "not-a-bcrypt-hash") is False

    def test_UT_39_73バイト超は先頭72一致で同一扱い(self):
        """UT-39 / DD-09,DD-10 / 境界: 72バイト超過部分は無視される（bcrypt仕様・設計注記）。"""
        base = "a" * 72
        h = hash_password(base + "X")  # 73バイト目以降は無視
        assert verify_password(base + "DIFFERENT", h) is True  # 73B目以降が違っても一致

    def test_UT_40_hashはbcrypt形式(self):
        """UT-40 / DD-09 / 正常: 出力は bcrypt の $2b$ プレフィクスを持つ。"""
        h = hash_password("x")
        assert h.startswith("$2")


# ---------------- DD-11 / DD-12 ----------------
class TestJwt:
    def test_UT_41_ラウンドトリップ(self):
        """UT-41 / DD-11,DD-12 / 正常: decode(create(5)) == "5"。"""
        token = create_access_token(5)
        assert decode_access_token(token) == "5"

    def test_UT_42_subjectはint入力でも文字列化(self):
        """UT-42 / DD-11 / 正常: int subject は sub に文字列で格納。"""
        token = create_access_token(123)
        sub = decode_access_token(token)
        assert sub == "123"
        assert isinstance(sub, str)

    def test_UT_43_署名鍵不一致はNone(self):
        """UT-43 / DD-12 / 異常: 異なる鍵で署名されたトークンは検証失敗でNone。"""
        bad = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            "wrong-secret",
            algorithm=settings.jwt_algorithm,
        )
        assert decode_access_token(bad) is None

    def test_UT_44_期限切れはNone(self):
        """UT-44 / DD-12 / 異常: exp が過去のトークンはNone。"""
        expired = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        assert decode_access_token(expired) is None

    def test_UT_45_不正形式はNone(self):
        """UT-45 / DD-12 / 異常: JWTでない文字列はNone。"""
        assert decode_access_token("garbage.token.value") is None
        assert decode_access_token("") is None
