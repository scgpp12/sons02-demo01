"""請求金額の自動計算ロジックの単体テスト。"""
from decimal import Decimal

import pytest

from app.crud.billing import BillingTerms, calc_billed_amount, calc_gross_profit

# 単価60万、精算幅140-180h、超過3750円/h、控除3750円/h を基本ケースとする
BASE = BillingTerms(
    unit_price=600_000,
    settlement_lower=140,
    settlement_upper=180,
    overtime_rate=3_750,
    deduction_rate=3_750,
)


class TestRange:
    def test_範囲内は固定単価(self):
        assert calc_billed_amount(BASE, 160) == 600_000

    def test_下限ちょうどは固定単価(self):
        assert calc_billed_amount(BASE, 140) == 600_000

    def test_上限ちょうどは固定単価(self):
        assert calc_billed_amount(BASE, 180) == 600_000


class TestOvertime:
    def test_超過は加算(self):
        # 190h → 10h超過 × 3750 = 37500 加算
        assert calc_billed_amount(BASE, 190) == 637_500

    def test_超過_小数時間(self):
        # 180.5h → 0.5h × 3750 = 1875
        assert calc_billed_amount(BASE, Decimal("180.5")) == 601_875


class TestShortage:
    def test_不足は控除(self):
        # 130h → 10h不足 × 3750 = 37500 控除
        assert calc_billed_amount(BASE, 130) == 562_500

    def test_不足_小数時間(self):
        assert calc_billed_amount(BASE, Decimal("139.5")) == 598_125


class TestNullSettlement:
    def test_精算幅なしは常に固定単価(self):
        terms = BillingTerms(unit_price=500_000)
        assert calc_billed_amount(terms, 0) == 500_000
        assert calc_billed_amount(terms, 300) == 500_000

    def test_上限のみ設定(self):
        terms = BillingTerms(unit_price=500_000, settlement_upper=160, overtime_rate=3_000)
        assert calc_billed_amount(terms, 100) == 500_000  # 下限なし→不足控除なし
        assert calc_billed_amount(terms, 170) == 530_000  # 10h超過

    def test_下限のみ設定(self):
        terms = BillingTerms(unit_price=500_000, settlement_lower=140, deduction_rate=3_000)
        assert calc_billed_amount(terms, 300) == 500_000  # 上限なし→超過加算なし
        assert calc_billed_amount(terms, 130) == 470_000  # 10h不足


class TestEdge:
    def test_金額は0未満にならない(self):
        terms = BillingTerms(
            unit_price=10_000, settlement_lower=140, deduction_rate=3_750
        )
        assert calc_billed_amount(terms, 0) == 0

    def test_超過控除レート0なら固定(self):
        terms = BillingTerms(unit_price=600_000, settlement_lower=140, settlement_upper=180)
        assert calc_billed_amount(terms, 200) == 600_000
        assert calc_billed_amount(terms, 100) == 600_000

    @pytest.mark.parametrize(
        "hours,expected",
        [(140, 600_000), (160, 600_000), (180, 600_000), (181, 603_750), (139, 596_250)],
    )
    def test_境界パラメタ(self, hours, expected):
        assert calc_billed_amount(BASE, hours) == expected


class TestGrossProfit:
    def test_粗利と粗利率(self):
        profit, rate = calc_gross_profit(600_000, 500_000)
        assert profit == 100_000
        assert rate == pytest.approx(16.7, abs=0.05)

    def test_売上0なら率はNone(self):
        profit, rate = calc_gross_profit(0, 0)
        assert profit == 0
        assert rate is None

    def test_赤字(self):
        profit, rate = calc_gross_profit(400_000, 500_000)
        assert profit == -100_000
        assert rate == -25.0
