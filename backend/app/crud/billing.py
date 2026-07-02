"""請求金額の自動計算（純粋関数）。

DBやORMに依存しないプリミティブ引数のみを受け取り、単体テストしやすくする。
精算幅ロジック:
  - worked_hours が [settlement_lower, settlement_upper] の範囲内 → unit_price
  - worked_hours > settlement_upper → unit_price + (超過時間 × overtime_rate)
  - worked_hours < settlement_lower → unit_price - (不足時間 × deduction_rate)
  - settlement_lower / settlement_upper が未設定(None)の側は精算しない(固定単価)
金額は円単位の整数で返す（端数は四捨五入）。
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class BillingTerms:
    """請求計算に必要な契約条件。"""

    unit_price: int
    settlement_lower: int | None = None
    settlement_upper: int | None = None
    overtime_rate: int = 0
    deduction_rate: int = 0


def _to_int_yen(value: Decimal) -> int:
    """円未満を四捨五入して整数化。"""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calc_billed_amount(terms: BillingTerms, worked_hours: Decimal | float | int) -> int:
    """稼働時間から請求金額を算出する。

    Args:
        terms: 契約条件
        worked_hours: 当月の稼働時間（時間単位、小数可）
    Returns:
        請求金額（円・整数、0未満にはならない）
    """
    hours = Decimal(str(worked_hours))
    base = Decimal(terms.unit_price)

    upper = terms.settlement_upper
    lower = terms.settlement_lower

    amount = base
    if upper is not None and hours > Decimal(upper):
        over = hours - Decimal(upper)
        amount = base + over * Decimal(terms.overtime_rate)
    elif lower is not None and hours < Decimal(lower):
        short = Decimal(lower) - hours
        amount = base - short * Decimal(terms.deduction_rate)

    result = _to_int_yen(amount)
    return max(result, 0)


def calc_gross_profit(upper_billed: int, lower_paid: int) -> tuple[int, float | None]:
    """粗利と粗利率を算出する。

    Args:
        upper_billed: 上位契約の請求額（売上）
        lower_paid: 下位契約の支払額（原価）
    Returns:
        (粗利額, 粗利率パーセント) — 売上が0なら粗利率はNone
    """
    profit = upper_billed - lower_paid
    if upper_billed == 0:
        return profit, None
    rate = round(profit / upper_billed * 100, 1)
    return profit, rate
