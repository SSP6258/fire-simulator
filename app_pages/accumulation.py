"""頁1 · 資產累積推演（確定性）。

頁面檔案就是直接執行的腳本 —— 不包成函式，這是 st.navigation 的規範寫法。
標題由 streamlit_app.py 統一處理，所以這裡不用 st.title。
"""

import numpy as np
import pandas as pd
import streamlit as st

from core import charts
from core.fmt import age as fmt_age
from core.fmt import money
from core.simulate import deterministic_path, first_reach_age

params = st.session_state.params

st.caption(
    "假設每年都剛好賺到預期報酬率，沒有任何波動。"
    "這是最樂觀也最不真實的一種算法 —— 真實世界請看「蒙地卡羅模擬」那一頁。"
)

path = deterministic_path(params)

basis = st.segmented_control(
    "金額基準",
    options=["實質（今日購買力）", "名目（未來面額）"],
    default="實質（今日購買力）",
    key="acc_basis",
)
use_real = basis != "名目（未來面額）"

wealth = path["real"] if use_real else path["nominal"]
target = path["target_real"] if use_real else path["target_nominal"]
reach_age = first_reach_age(path["ages"], path["nominal"], path["target_nominal"])

with st.container(horizontal=True):
    st.metric(
        "FIRE 目標金額",
        money(target[0] if use_real else target[-1]),
        delta=f"年支出的 {1 / params.swr:.0f} 倍",
        delta_arrow="off",
        border=True,
        help="用今日購買力計算：年支出 ÷ 安全提領率。",
    )
    st.metric(
        "預計達成年齡",
        fmt_age(reach_age),
        delta=(
            f"還需 {reach_age - params.current_age} 年"
            if reach_age is not None
            else "推算期間內達不到"
        ),
        delta_arrow="off",
        border=True,
    )
    st.metric(
        f"{params.max_age} 歲時資產",
        money(wealth[-1]),
        delta="今日購買力" if use_real else "未來面額",
        delta_arrow="off",
        border=True,
    )
    st.metric(
        "實質報酬率",
        f"{params.real_return:.2%}",
        delta=f"名目 {params.expected_return:.1%} − 通膨 {params.inflation:.1%}",
        delta_arrow="off",
        border=True,
        help="通膨吃掉的部分。這才是購買力真正的成長速度。",
    )

with st.container(border=True):
    st.subheader("資產成長軌跡")
    st.altair_chart(
        charts.dual_line_chart(
            path["ages"],
            {"資產": wealth, "FIRE 目標": target},
            x_name="age",
            x_title="年齡",
            y_title="金額（萬元）",
            dashed={"FIRE 目標"},
        )
    )
    if reach_age is not None:
        st.success(
            f"在這組假設下，你會在 **{reach_age} 歲** 達成 FIRE ——"
            f"距離現在 **{reach_age - params.current_age} 年**。"
        )
    else:
        st.warning(
            f"在 {params.max_age} 歲之前追不上目標。"
            "試著提高儲蓄率、拉高預期報酬，或降低退休後的年支出。"
        )

with st.expander("逐年明細"):
    table = pd.DataFrame(
        {
            "年齡": path["ages"],
            "名目資產（萬）": np.round(path["nominal"], 1),
            "實質資產（萬）": np.round(path["real"], 1),
            "名目目標（萬）": np.round(path["target_nominal"], 1),
            "達標": path["nominal"] >= path["target_nominal"],
        }
    )
    st.dataframe(table, hide_index=True, height=320)
    st.download_button(
        "下載 CSV",
        table.to_csv(index=False).encode("utf-8-sig"),
        file_name="fire_accumulation.csv",
        mime="text/csv",
        icon=":material/download:",
    )
