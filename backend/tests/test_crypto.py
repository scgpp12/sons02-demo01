"""Fernet暗号化（マイナンバー等）の単体テスト。

対象: DD-18 encrypt / DD-19 decrypt / DD-20 _fernet
鍵は JWT_SECRET から決定的に導出（DD-20）。conftestで固定済みのため疑似純粋として扱う。
"""
from app.core.crypto import decrypt, encrypt


class TestEncryptDecrypt:
    def test_UT_60_ラウンドトリップ(self):
        """UT-60 / DD-18,DD-19 / 正常: encrypt→decrypt で元の平文に戻る。"""
        assert decrypt(encrypt("123456789012")) == "123456789012"

    def test_UT_61_日本語のラウンドトリップ(self):
        """UT-61 / DD-18,DD-19 / 正常: マルチバイト文字も往復可能(UTF-8)。"""
        assert decrypt(encrypt("マイナンバー氏名テスト")) == "マイナンバー氏名テスト"

    def test_UT_62_暗号文は毎回異なる(self):
        """UT-62 / DD-18 / 境界: 同じ平文でもFernetのIV/timestampで暗号文は毎回異なる。"""
        c1 = encrypt("same-value")
        c2 = encrypt("same-value")
        assert c1 != c2
        assert decrypt(c1) == decrypt(c2) == "same-value"

    def test_UT_63_不正トークンはNone(self):
        """UT-63 / DD-19 / 異常: 不正なトークンは例外を出さず None。"""
        assert decrypt("not-a-valid-fernet-token") is None

    def test_UT_64_空文字も往復可能(self):
        """UT-64 / DD-18,DD-19 / 境界: 空文字も暗号化・復号できる。"""
        assert decrypt(encrypt("")) == ""

    def test_UT_65_暗号文の改竄はNone(self):
        """UT-65 / DD-19 / 異常: 暗号文を改竄すると検証失敗で None。"""
        token = encrypt("secret")
        tampered = token[:-2] + ("AB" if token[-2:] != "AB" else "CD")
        assert decrypt(tampered) is None
