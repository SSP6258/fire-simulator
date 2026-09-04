"""頁3 · 退休提領存活分析 —— Trinity Study 的簡化重現。"""

import numpy as np
import streamlit as st

from core import charts
from core.cached import cached_rate_sweep, cached_withdrawal
from core.fmt import money
from core.simulate import fire_target

params = st.session_state.params

st.caption(
    "累積期結束只是上半場。真正的問題是：**退休後每年提領，這筆錢撐不撐得過餘生？**"
    "市場報酬的順序（早期是熊市還是牛市）會造成天差地別的結果。"
)

default_pot = fire_target(params.annual_expense, params.swr)

with st.container(horizontal=True):
    pot = st.number_input(
        "退休時的資產（萬元）",
        min_value=0.0,
        max_value=200_000.0,
        value=float(round(default_pot)),
        step=50.0,
        key="wd_pot",
        help=f"預設值是你的 FIRE 目標金額（年支出 ÷ {params.swr:.1%}）。",
    )
    n_sims = st.select_slider(
        "模擬次數", options=[200, 500, 1000, 2000, 5000], value=1000, key="wd_n_sims"
    )
    seed = st.number_input(
        "亂數種子", min_value=0, max_value=9999, value=42, step=1, key="wd_seed"
    )

annual_withdrawal = pot * params.swr

result = cached_withdrawal(
    initial_wealth=float(pot),
    annual_withdrawal=float(annual_withdrawal),
    years=int(params.retire_years),
    mean_return=params.expected_return,
    volatility=params.volatility,
    inflation=params.inflation,
    n_sims=int(n_sims),
    seed=int(seed),
)

with st.container(horizontal=True):
    st.metric(
        f"撐過 {params.retire_years} 年的機率",
        f"{result['success_rate']:.1%}",
        delta=f"提領率 {params.swr:.1%}",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "破產機率",
        f"{result['ruin_rate']:.1%}",
        delta="錢在餘生結束前用完",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "第一年提領金額",
        money(annual_withdrawal),
        delta="之後每年隨通膨調升",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "期末資產中位數",
        money(float(np.median(result["wealth"][:, -1]))),
        delta="留給下一代的部分",
        delta_arrow="off",
        border=True,
    )

with st.container(border=True):
    st.subheader("退休後的資產軌跡")
    st.altair_chart(
        charts.fan_chart(
            result["years"],
            result["percentiles"],
            x_name="year",
            x_title="退休後第幾年",
            y_title="資產（萬元）",
            sample_paths=result["wealth"][:60],
            height=420,
        )
    )
    st.caption("觸底到 0 的路徑就是破產 —— 一旦歸零就再也長不回來。")

with st.container(border=True):
    st.subheader("提領率敏感度")
    st.markdown("同樣一筆退休金，只改變每年提領的比例，成功率的變化：")
    rates = (0.03, 0.035, 0.04, 0.045, 0.05, 0.06)
    success = cached_rate_sweep(
        rates,
        initial_wealth=float(pot),
        years=int(params.retire_years),
        mean_return=params.expected_return,
        volatility=params.volatility,
        inflation=params.inflation,
        n_sims=int(n_sims),
        seed=int(seed),
    )
    st.altair_chart(charts.success_bar_chart(np.array(rates), success))

    safe = [r for r, s in zip(rates, success) if s >= 0.95]
    if safe:
        st.success(
            f"在你的市場假設下，**{max(safe):.1%}** 是還能維持 95% 以上成功率的最高提領率。",
            icon=":material/verified:",
        )
    else:
        st.warning(
            "沒有任何一個提領率能達到 95% 成功率。"
            "退休金太少、退休期太長，或波動度太高。",
            icon=":material/warning:",
        )

ruined = result["depletion_year"][result["depletion_year"] > 0]
if ruined.size:
    with st.container(border=True):
        st.subheader("破產發生在第幾年")
        st.altair_chart(
            charts.histogram(ruined, x_title="退休後第幾年破產", y_title="次數")
        )
        st.caption(
            f"{ruined.size:,} 次模擬破產，中位數發生在第 {np.median(ruined):.0f} 年。"
        )
