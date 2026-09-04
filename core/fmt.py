"""數字格式化。純函式，方便測試。"""

from __future__ import annotations

import math


def money(wan: float) -> str:
    """把「萬元」格式化成人看得懂的字串，超過一億自動換單位。"""
    if not math.isfinite(wan):
        return "—"
    if abs(wan) >= 10_000:
        return f"{wan / 10_000:,.2f} 億"
    return f"{wan:,.0f} 萬"


def age(value: float | None) -> str:
    """年齡；達不到目標時顯示破折號而不是 None。"""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "—"
    return f"{value:.0f} 歲"
