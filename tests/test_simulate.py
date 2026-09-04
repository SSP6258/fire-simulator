"""core.simulate 的單元測試。

這些測試完全不碰 Streamlit —— 因為 core/simulate.py 本身就沒有 import 它。
所以跑起來是毫秒等級，不需要瀏覽器、不需要伺服器。
"""

from __future__ import annotations

import numpy as np
import pytest

from core.simulate import (
    FireParams,
    deterministic_path,
    fire_target,
    first_reach_age,
    simulate_accumulation,
    simulate_withdrawal,
    withdrawal_rate_sweep,
)


# --------------------------------------------------------------------------
# fire_target
# --------------------------------------------------------------------------


def test_fire_target_is_25x_at_4_percent():
    """4% 法則就是 25 倍年支出。"""
    assert fire_target(70.0, 0.04) == pytest.approx(1750.0)


def test_fire_target_rejects_zero_rate():
    with pytest.raises(ValueError):
        fire_target(70.0, 0.0)


# --------------------------------------------------------------------------
# deterministic_path
# --------------------------------------------------------------------------


def test_zero_return_zero_inflation_matches_closed_form():
    """沒有報酬也沒有通膨時，資產就是「本金 + 年數 x 年儲蓄」。

    這是整個推演最重要的一條測試：有解析解可以對答案，
    抓得到 off-by-one 之類的迴圈錯誤。
    """
    p = FireParams(
        current_age=30,
        max_age=40,
        current_savings=100.0,
        annual_income=120.0,
        annual_expense=70.0,
        expected_return=0.0,
        inflation=0.0,
    )
    path = deterministic_path(p)

    expected = 100.0 + np.arange(11) * 50.0  # 年儲蓄 = 120 - 70 = 50
    np.testing.assert_allclose(path["nominal"], expected)


def test_path_lengths_are_consistent():
    p = FireParams(current_age=30, max_age=90)
    path = deterministic_path(p)
    n = p.n_years + 1
    assert all(len(path[k]) == n for k in path)


def test_real_wealth_is_below_nominal_under_inflation():
    """有通膨時，實質購買力必然低於名目金額。"""
    p = FireParams(inflation=0.03, expected_return=0.07)
    path = deterministic_path(p)
    assert (path["real"][1:] < path["nominal"][1:]).all()


def test_target_grows_with_inflation():
    p = FireParams(inflation=0.02)
    path = deterministic_path(p)
    assert path["target_nominal"][-1] > path["target_nominal"][0]
    # 用今日購買力衡量的目標則是固定的
    assert np.allclose(path["target_real"], path["target_real"][0])


def test_first_reach_age_returns_none_when_unreachable():
    ages = np.arange(30, 41)
    wealth = np.zeros(11)
    target = np.full(11, 1000.0)
    assert first_reach_age(ages, wealth, target) is None


def test_first_reach_age_finds_crossing():
    ages = np.arange(30, 35)
    wealth = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    target = np.full(5, 25.0)
    assert first_reach_age(ages, wealth, target) == 33


# --------------------------------------------------------------------------
# simulate_accumulation
# --------------------------------------------------------------------------


def test_zero_volatility_reproduces_deterministic_path():
    """波動度設 0 時，蒙地卡羅必須退化成確定性推演。

    這條測試把兩條獨立的程式路徑綁在一起 —— 改壞任何一邊都會被抓到。
    """
    p = FireParams(volatility=0.0)
    mc = simulate_accumulation(p, n_sims=5)
    det = deterministic_path(p)
    np.testing.assert_allclose(mc["wealth"][0], det["nominal"], rtol=1e-9)


def test_same_seed_is_reproducible():
    p = FireParams()
    a = simulate_accumulation(p, n_sims=100, seed=7)
    b = simulate_accumulation(p, n_sims=100, seed=7)
    np.testing.assert_array_equal(a["wealth"], b["wealth"])


def test_different_seed_gives_different_paths():
    p = FireParams()
    a = simulate_accumulation(p, n_sims=100, seed=1)
    b = simulate_accumulation(p, n_sims=100, seed=2)
    assert not np.array_equal(a["wealth"], b["wealth"])


def test_percentiles_are_ordered():
    """10 < 25 < 50 < 75 < 90 百分位，任何一年都該成立。"""
    p = FireParams()
    result = simulate_accumulation(p, n_sims=500)
    pct = result["percentiles"]
    assert (np.diff(pct, axis=0) >= 0).all()


def test_mean_growth_matches_expected_return():
    """使用者輸入 7%，長期下來拿到的就該是 7%（統計上）。

    驗證 log-normal 的參數換算沒寫錯。
    """
    p = FireParams(
        current_age=30,
        max_age=31,
        current_savings=100.0,
        annual_income=0.0,
        annual_expense=0.0,
        expected_return=0.07,
        volatility=0.15,
        inflation=0.0,
    )
    result = simulate_accumulation(p, n_sims=200_000, seed=123)
    assert result["wealth"][:, 1].mean() == pytest.approx(107.0, rel=2e-3)


def test_wealth_never_goes_negative():
    p = FireParams(annual_income=50.0, annual_expense=90.0, volatility=0.3)
    result = simulate_accumulation(p, n_sims=300)
    assert (result["wealth"] >= 0).all()


def test_success_rate_is_a_probability():
    p = FireParams()
    result = simulate_accumulation(p, n_sims=200)
    assert 0.0 <= result["success_rate"] <= 1.0


def test_higher_savings_raise_success_rate():
    lean = FireParams(annual_income=100.0, annual_expense=90.0)
    rich = FireParams(annual_income=200.0, annual_expense=90.0)
    assert (
        simulate_accumulation(rich, n_sims=400)["success_rate"]
        >= simulate_accumulation(lean, n_sims=400)["success_rate"]
    )


def test_rejects_zero_simulations():
    with pytest.raises(ValueError):
        simulate_accumulation(FireParams(), n_sims=0)


# --------------------------------------------------------------------------
# simulate_withdrawal
# --------------------------------------------------------------------------


def test_no_withdrawal_never_ruins():
    result = simulate_withdrawal(
        initial_wealth=1000.0,
        annual_withdrawal=0.0,
        years=30,
        mean_return=0.07,
        volatility=0.15,
        inflation=0.02,
        n_sims=200,
    )
    assert result["success_rate"] == 1.0


def test_absurd_withdrawal_always_ruins():
    result = simulate_withdrawal(
        initial_wealth=100.0,
        annual_withdrawal=60.0,
        years=30,
        mean_return=0.05,
        volatility=0.15,
        inflation=0.02,
        n_sims=200,
    )
    assert result["success_rate"] == 0.0


def test_ruin_is_absorbing():
    """一旦破產就回不去了 —— 資產歸零後不該又長回來。"""
    result = simulate_withdrawal(
        initial_wealth=100.0,
        annual_withdrawal=25.0,
        years=30,
        mean_return=0.07,
        volatility=0.2,
        inflation=0.02,
        n_sims=200,
    )
    w = result["wealth"]
    for row in w:
        zeros = np.flatnonzero(row <= 0)
        if zeros.size:
            assert (row[zeros[0]:] == 0).all()


def test_success_and_ruin_rates_sum_to_one():
    result = simulate_withdrawal(
        initial_wealth=1000.0,
        annual_withdrawal=45.0,
        years=30,
        mean_return=0.07,
        volatility=0.15,
        inflation=0.02,
        n_sims=200,
    )
    assert result["success_rate"] + result["ruin_rate"] == pytest.approx(1.0)


def test_rejects_zero_years():
    with pytest.raises(ValueError):
        simulate_withdrawal(1000.0, 40.0, 0, 0.07, 0.15, 0.02)


# --------------------------------------------------------------------------
# withdrawal_rate_sweep
# --------------------------------------------------------------------------


def test_success_rate_decreases_as_withdrawal_rate_rises():
    """提領越兇，撐過 30 年的機率只會越低，不可能變高。"""
    rates = [0.03, 0.035, 0.04, 0.045, 0.05, 0.06, 0.08]
    success = withdrawal_rate_sweep(
        rates,
        initial_wealth=1000.0,
        years=30,
        mean_return=0.07,
        volatility=0.15,
        inflation=0.02,
        n_sims=500,
    )
    assert (np.diff(success) <= 0).all()


# --------------------------------------------------------------------------
# core.fmt
# --------------------------------------------------------------------------


def test_money_switches_to_yi_above_ten_thousand_wan():
    from core.fmt import money

    assert money(1750.0) == "1,750 萬"
    assert money(12_345.0) == "1.23 億"
    assert money(float("nan")) == "—"


def test_age_handles_missing_value():
    from core.fmt import age

    assert age(None) == "—"
    assert age(float("nan")) == "—"
    assert age(47.0) == "47 歲"
