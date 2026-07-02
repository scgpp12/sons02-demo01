"""日付ユーティリティ（純粋関数）の単体テスト。

対象: DD-07 _month_start / DD-08 _add_months
いずれも date のみを扱う純粋関数。常に月初日(day=1)を返す。
"""
from datetime import date

import pytest

from app.crud.dashboard import _add_months, _month_start


class TestMonthStart:
    def test_UT_70_月初に正規化(self):
        """UT-70 / DD-07 / 正常: 月中の日付を月初(day=1)に丸める。"""
        assert _month_start(date(2026, 6, 20)) == date(2026, 6, 1)

    def test_UT_71_月初はそのまま(self):
        """UT-71 / DD-07 / 境界: 既に月初ならそのまま。"""
        assert _month_start(date(2026, 6, 1)) == date(2026, 6, 1)

    def test_UT_72_月末も月初へ(self):
        """UT-72 / DD-07 / 境界: 月末(31日)も月初へ。"""
        assert _month_start(date(2026, 12, 31)) == date(2026, 12, 1)


class TestAddMonths:
    @pytest.mark.parametrize(
        "d,n,expected",
        [
            (date(2026, 11, 1), 2, date(2027, 1, 1)),   # 年跨ぎ(+)
            (date(2026, 1, 15), -1, date(2025, 12, 1)), # 年跨ぎ(-)
            (date(2026, 6, 20), 0, date(2026, 6, 1)),   # n=0 でも月初へ正規化
            (date(2026, 6, 1), 12, date(2027, 6, 1)),   # +12ヶ月
            (date(2026, 6, 1), -6, date(2025, 12, 1)),  # -6ヶ月
            (date(2026, 12, 1), 1, date(2027, 1, 1)),   # 12月+1で年明け
        ],
    )
    def test_UT_73_月加算(self, d, n, expected):
        """UT-73 / DD-08 / 正常+境界: 月加算（負・年跨ぎ含む）。常に月初を返す。"""
        result = _add_months(d, n)
        assert result == expected
        assert result.day == 1

    def test_UT_74_大きな負の加算(self):
        """UT-74 / DD-08 / 境界: 24ヶ月遡及。"""
        assert _add_months(date(2026, 6, 10), -24) == date(2024, 6, 1)
