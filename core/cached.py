"""把重運算包上 Streamlit 快取。

蒙地卡羅一次要跑幾千條路徑；使用者每動一次滑桿 Streamlit 就會重跑整個腳本，
沒有快取的話同一組參數會被重算無數次。

快取鍵是函式的所有參數 —— 所以 FireParams 才做成 frozen dataclass。
"""

from __future__ import annotations

import streamlit as st

from core.simulate import (
    FireParams,
    simulate_accumulation,
    simulate_withdrawal,
    withdrawal_rate_sweep,
)


@st.cache_data(show_spinner="模擬中…", max_entries=32)
def cached_accumulation(params: FireParams, n_sims: int, seed: int):
    return simulate_accumulation(params, n_sims=n_sims, seed=seed)


@st.cache_data(show_spinner="模擬中…", max_entries=32)
def cached_withdrawal(
    initial_wealth: float,
    annual_withdrawal: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation: float,
    n_sims: int,
    seed: int,
):
    return simulate_withdrawal(
        initial_wealth=initial_wealth,
        annual_withdrawal=annual_withdrawal,
        years=years,
        mean_return=mean_return,
        volatility=volatility,
        inflation=inflation,
        n_sims=n_sims,
        seed=seed,
    )


@st.cache_data(show_spinner="掃描各提領率…", max_entries=16)
def cached_rate_sweep(
    rates: tuple[float, ...],
    initial_wealth: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation: float,
    n_sims: int,
    seed: int,
):
    return withdrawal_rate_sweep(
        list(rates),
        initial_wealth=initial_wealth,
        years=years,
        mean_return=mean_return,
        volatility=volatility,
        inflation=inflation,
        n_sims=n_sims,
        seed=seed,
    )
