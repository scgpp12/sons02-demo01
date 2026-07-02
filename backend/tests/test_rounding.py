"""円未満四捨五入（純粋関数）の単体テスト。

対象: DD-21 _to_int_yen
Decimal を ROUND_HALF_UP で整数化する。負値も四捨五入する
（0未満化の保護は呼出側 calc_billed_amount が担保）。
"""
from decimal import Decimal

import pytest

from app.crud.billing import _to_int_yen


class TestToIntYen:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal("0.5"), 1),       # 0.5 → 切上(HALF_UP)
            (Decimal("0.4"), 0),       # 0.4 → 切捨
            (Decimal("0.6"), 1),
            (Decimal("1.5"), 2),       # 1.5 → 2(HALF_UP, 銀行丸めではない)
            (Decimal("2.5"), 3),       # 2.5 → 3(銀行丸めなら2になるが本実装はHALF_UP)
            (Decimal("100000"), 100000),
            (Decimal("750000.49"), 750000),
            (Decimal("750000.50"), 750001),
        ],
    )
    def test_UT_80_四捨五入(self, value, expected):
        """UT-80 / DD-21 / 正常+境界: ROUND_HALF_UP で整数化。"""
        assert _to_int_yen(value) == expected

    def test_UT_81_負値の四捨五入(self):
        """UT-81 / DD-21 / 境界: 負値も HALF_UP（-0.5→0方向＝-0、絶対値で切上）。

        ROUND_HALF_UP は「ゼロから遠ざかる」丸めのため -0.5 → -1。
        実挙動を検証する（負化保護は呼出側の責務）。
        """
        assert _to_int_yen(Decimal("-0.5")) == -1
        assert _to_int_yen(Decimal("-0.4")) == 0
        assert _to_int_yen(Decimal("-1.5")) == -2
