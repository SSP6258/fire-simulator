"""FIRE 模擬的純計算邏輯。

這個模組刻意**不 import streamlit**：所有函式都是純數值計算，
可以用 pytest 直接測試，不必啟動 app 或瀏覽器。

金額單位一律為「萬元」，比率一律為小數（0.07 代表 7%）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 預設亂數種子。固定住才能讓同一組參數每次算出同樣的結果，
# 否則使用者每動一下滑桿，圖就會整個跳動。
DEFAULT_SEED = 42


@dataclass(frozen=True)
class FireParams:
    """一整組 FIRE 試算參數。frozen=True 讓它可以被 st.cache_data 當快取鍵。"""

    current_age: int = 30
    current_savings: float = 100.0  # 目前資產（萬元）
    annual_income: float = 120.0  # 年收入（萬元）
    annual_expense: float = 70.0  # 年支出（萬元）
    expected_return: float = 0.07  # 預期年報酬率（算術平均）
    volatility: float = 0.15  # 年化波動度（標準差）
    inflation: float = 0.02  # 通膨率
    swr: float = 0.04  # 安全提領率，4% 法則
    retire_years: int = 30  # 退休後要撐幾年
    max_age: int = 90  # 推算到幾歲

    @property
    def annual_saving(self) -> float:
        """每年可投入的儲蓄（萬元）。可能為負，代表入不敷出。"""
        return self.annual_income - self.annual_expense

    @property
    def n_years(self) -> int:
        """累積期的年數。"""
        return max(self.max_age - self.current_age, 1)

    @property
    def real_return(self) -> float:
        """扣掉通膨後的實質報酬率。"""
        return (1 + self.expected_return) / (1 + self.inflation) - 1


def fire_target(annual_expense: float, swr: float) -> float:
    """FIRE 目標金額。

    4% 法則：年支出 / 0.04 = 年支出 x 25。
    """
    if swr <= 0:
        raise ValueError("提領率必須大於 0")
    return annual_expense / swr


def _growth_factors(
    mean: float, vol: float, shape: tuple[int, int], rng: np.random.Generator
) -> np.ndarray:
    """產生 log-normal 的年度成長因子（1 + 報酬率）。

    為什麼不直接用常態分佈？因為常態允許報酬率低於 -100%（資產變負數），
    在現實中不可能。log-normal 天然把成長因子鎖在 0 以上。

    這裡做了矩match：讓成長因子的算術平均等於 1 + mean、標準差等於 vol，
    使用者輸入「預期報酬 7%」時拿到的就真的是 7%。
    """
    if vol <= 0:
        return np.full(shape, 1.0 + mean)

    sigma_sq = np.log1p((vol / (1.0 + mean)) ** 2)
    sigma = np.sqrt(sigma_sq)
    mu = np.log1p(mean) - sigma_sq / 2.0
    return np.exp(rng.normal(mu, sigma, size=shape))


def deterministic_path(params: FireParams) -> dict[str, np.ndarray]:
    """確定性推演：假設每年都剛好賺到預期報酬率。

    回傳的每個陣列長度都是 n_years + 1（含起始年）。
    """
    n = params.n_years
    ages = np.arange(params.current_age, params.current_age + n + 1)
    inflator = (1.0 + params.inflation) ** np.arange(n + 1)

    wealth = np.empty(n + 1)
    wealth[0] = params.current_savings
    for t in range(n):
        # 年初的資產滾一年，年底再存入當年的儲蓄（儲蓄本身也跟著通膨成長）
        wealth[t + 1] = wealth[t] * (1.0 + params.expected_return) + (
            params.annual_saving * inflator[t]
        )
    np.maximum(wealth, 0.0, out=wealth)

    target_today = fire_target(params.annual_expense, params.swr)
    return {
        "ages": ages,
        "nominal": wealth,
        "real": wealth / inflator,
        "target_nominal": target_today * inflator,
        "target_real": np.full(n + 1, target_today),
    }


def first_reach_age(
    ages: np.ndarray, wealth: np.ndarray, target: np.ndarray
) -> int | None:
    """資產首次追上 FIRE 目標的年齡；一輩子都追不上就回傳 None。"""
    hit = np.flatnonzero(wealth >= target)
    return int(ages[hit[0]]) if hit.size else None


def simulate_accumulation(
    params: FireParams, n_sims: int = 1000, seed: int = DEFAULT_SEED
) -> dict[str, np.ndarray | float]:
    """蒙地卡羅：跑 n_sims 次人生，看資產累積的分佈。"""
    if n_sims < 1:
        raise ValueError("模擬次數必須至少 1 次")

    rng = np.random.default_rng(seed)
    n = params.n_years
    growth = _growth_factors(
        params.expected_return, params.volatility, (n_sims, n), rng
    )
    inflator = (1.0 + params.inflation) ** np.arange(n + 1)

    wealth = np.empty((n_sims, n + 1))
    wealth[:, 0] = params.current_savings
    for t in range(n):
        wealth[:, t + 1] = wealth[:, t] * growth[:, t] + (
            params.annual_saving * inflator[t]
        )
    np.maximum(wealth, 0.0, out=wealth)

    target = fire_target(params.annual_expense, params.swr) * inflator
    reached = wealth >= target

    ever = reached.any(axis=1)
    # argmax 找出第一個 True 的位置；沒達標的那幾條要另外標成 -1
    first_idx = reached.argmax(axis=1)
    reach_ages = np.where(ever, params.current_age + first_idx, -1)

    return {
        "ages": np.arange(params.current_age, params.current_age + n + 1),
        "wealth": wealth,
        "target": target,
        "percentiles": np.percentile(wealth, [10, 25, 50, 75, 90], axis=0),
        "success_rate": float(ever.mean()),
        "reach_ages": reach_ages,
        "median_reach_age": (
            float(np.median(reach_ages[ever])) if ever.any() else float("nan")
        ),
    }


def simulate_withdrawal(
    initial_wealth: float,
    annual_withdrawal: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation: float,
    n_sims: int = 1000,
    seed: int = DEFAULT_SEED,
) -> dict[str, np.ndarray | float]:
    """退休後的提領存活模擬（Trinity Study 的簡化版）。

    每年年初先提領當年生活費（隨通膨調升），剩下的錢再投資一年。
    資產一旦歸零就永久歸零 —— 破產是不可逆的。
    """
    if years < 1:
        raise ValueError("退休年數必須至少 1 年")

    rng = np.random.default_rng(seed)
    growth = _growth_factors(mean_return, volatility, (n_sims, years), rng)
    inflator = (1.0 + inflation) ** np.arange(years)

    wealth = np.empty((n_sims, years + 1))
    wealth[:, 0] = initial_wealth
    for t in range(years):
        after_withdrawal = np.maximum(wealth[:, t] - annual_withdrawal * inflator[t], 0.0)
        # 已歸零的路徑乘上成長因子還是 0，破產狀態會自然延續下去
        wealth[:, t + 1] = after_withdrawal * growth[:, t]

    survived = wealth[:, -1] > 0
    depleted = wealth <= 0
    ever_depleted = depleted.any(axis=1)
    depletion_year = np.where(ever_depleted, depleted.argmax(axis=1), -1)

    return {
        "years": np.arange(years + 1),
        "wealth": wealth,
        "percentiles": np.percentile(wealth, [10, 25, 50, 75, 90], axis=0),
        "success_rate": float(survived.mean()),
        "ruin_rate": float(1.0 - survived.mean()),
        "depletion_year": depletion_year,
    }


def withdrawal_rate_sweep(
    rates: np.ndarray | list[float],
    initial_wealth: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation: float,
    n_sims: int = 1000,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """掃描不同提領率的成功率。

    每個提領率都用**同一個 seed**，這樣差異純粹來自提領率本身，
    而不是來自不同的亂數序列。
    """
    return np.array(
        [
            simulate_withdrawal(
                initial_wealth=initial_wealth,
                annual_withdrawal=initial_wealth * rate,
                years=years,
                mean_return=mean_return,
                volatility=volatility,
                inflation=inflation,
                n_sims=n_sims,
                seed=seed,
            )["success_rate"]
            for rate in rates
        ]
    )
