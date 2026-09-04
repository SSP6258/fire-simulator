"""頁2 · 蒙地卡羅模擬 —— 跑 N 次人生，看運氣的影響有多大。"""

import numpy as np
import streamlit as st

from core import charts
from core.cached import cached_accumulation
from core.fmt import age as fmt_age
from core.fmt import money

params = st.session_state.params

st.caption(
    "同樣的儲蓄率、同樣的預期報酬，只是把「每年剛好賺 7%」換成「平均 7%、上下震盪」，"
    "結果就散開成一大片。**這片扇形就是運氣的寬度。**"
)

with st.container(horizontal=True):
    n_sims = st.select_slider(
        "模擬次數", options=[200, 500, 1000, 2000, 5000], value=1000, key="mc_n_sims"
    )
    seed = st.number_input(
        "亂數種子",
        min_value=0,
        max_value=9999,
        value=42,
        step=1,
        key="mc_seed",
        help="固定種子讓結果可重現。換一個數字就是換一組平行宇宙。",
    )

result = cached_accumulation(params, int(n_sims), int(seed))

final = result["wealth"][:, -1]
reached = result["reach_ages"][result["reach_ages"] > 0]

with st.container(horizontal=True):
    st.metric(
        "達成 FIRE 的機率",
        f"{result['success_rate']:.1%}",
        delta=f"{int(result['success_rate'] * n_sims):,} / {n_sims:,} 次人生",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "中位數達成年齡",
        fmt_age(result["median_reach_age"]),
        delta=(
            f"比確定性推演晚 {result['median_reach_age'] - params.current_age:.0f} 年後達成"
            if reached.size
            else "多數情境達不到"
        ),
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "最差 10% 的期末資產",
        money(np.percentile(final, 10)),
        delta="運氣很背的情況",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "最好 10% 的期末資產",
        money(np.percentile(final, 90)),
        delta="運氣很好的情況",
        delta_arrow="off",
        border=True,
    )

with st.container(border=True):
    st.subheader("資產路徑分佈")
    show_paths = st.toggle(
        "疊上個別路徑", value=True, key="mc_show_paths", help="看單一人生的曲折程度"
    )
    sample = result["wealth"][:60] if show_paths else None
    st.altair_chart(
        charts.fan_chart(
            result["ages"],
            result["percentiles"],
            x_name="age",
            x_title="年齡",
            y_title="名目資產（萬元）",
            target=result["target"],
            sample_paths=sample,
            height=440,
        )
    )
    st.caption(
        "深藍色帶 = 中間 50% 的情境，淺藍色帶 = 中間 80%，"
        "深藍實線 = 中位數，紅色虛線 = FIRE 目標（隨通膨上移）。"
    )

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("達成年齡分佈")
        if reached.size:
            st.altair_chart(
                charts.histogram(reached, x_title="達成 FIRE 的年齡", y_title="次數")
            )
        else:
            st.info("沒有任何一次模擬達成目標。")

with col2:
    with st.container(border=True):
        st.subheader("期末資產分佈")
        st.altair_chart(
            charts.histogram(final, x_title="期末資產（萬元）", y_title="次數")
        )

spread = np.percentile(final, 90) / max(np.percentile(final, 10), 1e-9)
st.info(
    f"最好 10% 的結果是最差 10% 的 **{spread:,.1f} 倍**。"
    "同樣的紀律、同樣的假設，差別只在運氣 —— 這就是為什麼「平均報酬率」這個數字會騙人。",
    icon=":material/lightbulb:",
)
