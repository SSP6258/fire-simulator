"""Altair 圖表建構器。

只 import altair / pandas / numpy，不 import streamlit ——
頁面負責「顯示」，這裡負責「畫成什麼樣子」。

用 Altair 而非 Plotly 的原因：Altair 隨 Streamlit 內建，
少一個相依套件就少一個部署時會出錯的地方。
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd

# 百分位帶由外而內顏色漸深，中位數最實。
BAND_OUTER = "#3b82f6"
BAND_INNER = "#60a5fa"
MEDIAN = "#bfdbfe"
TARGET = "#f87171"
PATH = "#94a3b8"


def _band_frame(x: np.ndarray, percentiles: np.ndarray, x_name: str) -> pd.DataFrame:
    """把 (5, n) 的百分位陣列攤平成一張寬表。"""
    p10, p25, p50, p75, p90 = percentiles
    return pd.DataFrame(
        {x_name: x, "p10": p10, "p25": p25, "p50": p50, "p75": p75, "p90": p90}
    )


def fan_chart(
    x: np.ndarray,
    percentiles: np.ndarray,
    *,
    x_name: str,
    x_title: str,
    y_title: str,
    target: np.ndarray | None = None,
    sample_paths: np.ndarray | None = None,
    height: int = 400,
) -> alt.LayerChart:
    """扇形圖：百分位帶 + 中位數 + 可選的目標線與個別路徑。

    這是整個 app 的視覺主秀 —— 一眼看出「同樣的策略，運氣不同會差多少」。
    """
    df = _band_frame(x, percentiles, x_name)
    x_enc = alt.X(f"{x_name}:Q", title=x_title, scale=alt.Scale(nice=False, zero=False))
    y_axis = alt.Axis(title=y_title, format=",.0f")

    layers: list[alt.Chart] = [
        alt.Chart(df)
        .mark_area(opacity=0.35, color=BAND_OUTER)
        .encode(x=x_enc, y=alt.Y("p10:Q", axis=y_axis), y2="p90:Q"),
        alt.Chart(df)
        .mark_area(opacity=0.45, color=BAND_INNER)
        .encode(x=x_enc, y=alt.Y("p25:Q", axis=y_axis), y2="p75:Q"),
    ]

    # 個別路徑疊在色帶上，讓「單一人生」的曲折感出得來
    if sample_paths is not None and len(sample_paths):
        long = pd.DataFrame(
            {
                x_name: np.tile(x, len(sample_paths)),
                "value": sample_paths.ravel(),
                "path": np.repeat(np.arange(len(sample_paths)), len(x)),
            }
        )
        layers.append(
            alt.Chart(long)
            .mark_line(opacity=0.18, strokeWidth=1, color=PATH)
            .encode(x=x_enc, y=alt.Y("value:Q", axis=y_axis), detail="path:N")
        )

    layers.append(
        alt.Chart(df)
        .mark_line(strokeWidth=2.5, color=MEDIAN)
        .encode(
            x=x_enc,
            y=alt.Y("p50:Q", axis=y_axis),
            tooltip=[
                alt.Tooltip(f"{x_name}:Q", title=x_title, format=".0f"),
                alt.Tooltip("p10:Q", title="最差 10%", format=",.0f"),
                alt.Tooltip("p50:Q", title="中位數", format=",.0f"),
                alt.Tooltip("p90:Q", title="最好 10%", format=",.0f"),
            ],
        )
    )

    if target is not None:
        target_df = pd.DataFrame({x_name: x, "target": target})
        layers.append(
            alt.Chart(target_df)
            .mark_line(strokeDash=[6, 4], strokeWidth=2, color=TARGET)
            .encode(x=x_enc, y=alt.Y("target:Q", axis=y_axis))
        )

    return alt.layer(*layers).properties(height=height).interactive(bind_y=False)


def dual_line_chart(
    x: np.ndarray,
    series: dict[str, np.ndarray],
    *,
    x_name: str,
    x_title: str,
    y_title: str,
    dashed: set[str] | None = None,
    height: int = 400,
) -> alt.Chart:
    """多條具名折線，可指定哪幾條畫成虛線（通常用來標目標線）。"""
    dashed = dashed or set()
    frames = [
        pd.DataFrame({x_name: x, "value": values, "series": name})
        for name, values in series.items()
    ]
    df = pd.concat(frames, ignore_index=True)
    df["dash"] = np.where(df["series"].isin(dashed), "目標", "資產")

    return (
        alt.Chart(df)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X(f"{x_name}:Q", title=x_title, scale=alt.Scale(nice=False, zero=False)),
            y=alt.Y("value:Q", title=y_title, axis=alt.Axis(format=",.0f")),
            color=alt.Color("series:N", title=None),
            strokeDash=alt.StrokeDash("dash:N", legend=None),
            tooltip=[
                alt.Tooltip(f"{x_name}:Q", title=x_title, format=".0f"),
                alt.Tooltip("series:N", title="項目"),
                alt.Tooltip("value:Q", title=y_title, format=",.0f"),
            ],
        )
        .properties(height=height)
        .interactive(bind_y=False)
    )


def histogram(
    values: np.ndarray, *, x_title: str, y_title: str, height: int = 300
) -> alt.Chart:
    """達成年齡 / 破產年份之類的分佈圖。"""
    df = pd.DataFrame({"value": values})
    return (
        alt.Chart(df)
        .mark_bar(color=BAND_INNER, opacity=0.85)
        .encode(
            x=alt.X("value:Q", bin=alt.Bin(maxbins=30), title=x_title),
            y=alt.Y("count():Q", title=y_title),
            tooltip=[alt.Tooltip("count():Q", title="次數")],
        )
        .properties(height=height)
    )


def success_bar_chart(
    rates: np.ndarray, success: np.ndarray, *, height: int = 320
) -> alt.LayerChart:
    """提領率敏感度：每個提領率對應的成功率長條圖，柱上直接標數字。"""
    df = pd.DataFrame(
        {
            "rate": [f"{r:.1%}" for r in rates],
            "success": success,
            "label": [f"{s:.0%}" for s in success],
        }
    )
    base = alt.Chart(df).encode(
        x=alt.X("rate:N", title="年提領率", sort=None),
        y=alt.Y(
            "success:Q",
            title="撐過退休期的機率",
            axis=alt.Axis(format=".0%"),
            scale=alt.Scale(domain=[0, 1]),
        ),
    )
    bars = base.mark_bar(size=48).encode(
        color=alt.Color(
            "success:Q",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0, 1]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("rate:N", title="提領率"),
            alt.Tooltip("success:Q", title="成功率", format=".1%"),
        ],
    )
    text = base.mark_text(dy=-8, fontSize=13, fontWeight="bold").encode(text="label:N")
    return alt.layer(bars, text).properties(height=height)
