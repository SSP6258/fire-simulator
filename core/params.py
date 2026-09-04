"""側邊欄參數輸入 —— 三個頁面共用同一組設定。

這是唯一會碰 st.session_state 的地方。所有預設值集中在 DEFAULTS，
初始化只在 init_state() 發生一次，避免「同一個 key 在好幾個地方被設定」
這種最難除錯的 Streamlit 問題。
"""

from __future__ import annotations

import streamlit as st

from core.simulate import FireParams

# 側邊欄每個 widget 的 key 與預設值。
# 用百分比呈現（7.0 代表 7%），送進 FireParams 前才除以 100。
DEFAULTS: dict[str, float | int] = {
    "p_current_age": 30,
    "p_max_age": 90,
    "p_current_savings": 100.0,
    "p_annual_income": 120.0,
    "p_annual_expense": 70.0,
    "p_return_pct": 7.0,
    "p_vol_pct": 15.0,
    "p_inflation_pct": 2.0,
    "p_swr_pct": 4.0,
    "p_retire_years": 30,
}

# 一鍵套用的情境範本。數字是台灣的粗略量級，單位萬元。
PRESETS: dict[str, dict[str, float | int]] = {
    "社會新鮮人": {
        "p_current_age": 26,
        "p_current_savings": 30.0,
        "p_annual_income": 70.0,
        "p_annual_expense": 52.0,
    },
    "雙薪家庭": {
        "p_current_age": 35,
        "p_current_savings": 300.0,
        "p_annual_income": 180.0,
        "p_annual_expense": 120.0,
    },
    "高儲蓄族": {
        "p_current_age": 32,
        "p_current_savings": 250.0,
        "p_annual_income": 200.0,
        "p_annual_expense": 80.0,
    },
}


def init_state() -> None:
    """每次 rerun 由進入點呼叫一次，確保 session state 是對的。

    做兩件事：補上還沒有的預設值，以及把既有的值重新指派給自己。

    第二件事看起來像廢話，但不能拿掉：Streamlit 會清掉「這一輪沒有被畫出來」的
    widget 狀態。對照頁不畫側邊欄，少了這一步，使用者調好的參數會在切過去的
    瞬間被回收，切回來就只剩 DEFAULTS —— 調了半天的數字無聲無息地歸零。
    重新指派一次就能讓它們活過那一輪。

    重新指派必須發生在 widget 被建立之前，所以這個函式只能在進入點最前面呼叫。
    """
    for key, value in DEFAULTS.items():
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
        else:
            st.session_state[key] = value


def _apply_preset() -> None:
    """套用範本。在 on_change callback 裡寫 session_state 是合法的 ——
    下一次 rerun 時 widget 就會讀到新值。"""
    preset = PRESETS.get(st.session_state.get("p_preset") or "")
    if preset:
        st.session_state.update(preset)


def current_params() -> FireParams:
    """把 session state 組成一個 FireParams。"""
    s = st.session_state
    return FireParams(
        current_age=int(s.p_current_age),
        current_savings=float(s.p_current_savings),
        annual_income=float(s.p_annual_income),
        annual_expense=float(s.p_annual_expense),
        expected_return=float(s.p_return_pct) / 100.0,
        volatility=float(s.p_vol_pct) / 100.0,
        inflation=float(s.p_inflation_pct) / 100.0,
        swr=float(s.p_swr_pct) / 100.0,
        retire_years=int(s.p_retire_years),
        max_age=int(s.p_max_age),
    )


def render_sidebar() -> FireParams:
    """畫出側邊欄並回傳目前的參數組合。"""
    with st.sidebar:
        st.segmented_control(
            "快速套用範本",
            options=list(PRESETS),
            key="p_preset",
            on_change=_apply_preset,
            help="套用後仍可自由微調下方每一個數字",
        )

        st.subheader("收支", divider="gray")
        st.number_input(
            "目前年齡", min_value=18, max_value=75, step=1, key="p_current_age"
        )
        st.number_input(
            "目前資產（萬元）",
            min_value=0.0,
            max_value=100_000.0,
            step=10.0,
            key="p_current_savings",
        )
        st.number_input(
            "年收入（萬元）",
            min_value=0.0,
            max_value=10_000.0,
            step=5.0,
            key="p_annual_income",
        )
        st.number_input(
            "年支出（萬元）",
            min_value=0.0,
            max_value=10_000.0,
            step=5.0,
            key="p_annual_expense",
        )

        st.subheader("市場假設", divider="gray")
        st.slider(
            "預期年報酬率", 0.0, 15.0, step=0.5, format="%.1f%%", key="p_return_pct"
        )
        st.slider(
            "年化波動度",
            0.0,
            40.0,
            step=1.0,
            format="%.0f%%",
            key="p_vol_pct",
            help="標準差。全球股票長期大約 15%，債券混合會更低。設 0 就退化成沒有風險的確定性推演。",
        )
        st.slider("通膨率", 0.0, 8.0, step=0.1, format="%.1f%%", key="p_inflation_pct")

        st.subheader("退休設定", divider="gray")
        st.slider(
            "安全提領率",
            2.0,
            8.0,
            step=0.1,
            format="%.1f%%",
            key="p_swr_pct",
            help="4% 法則來自 Trinity Study：退休後每年提領資產的 4%，歷史數據顯示有很高機率撐過 30 年。",
        )
        st.number_input(
            "退休後要撐幾年", min_value=10, max_value=60, step=5, key="p_retire_years"
        )
        st.number_input(
            "推算到幾歲", min_value=50, max_value=110, step=5, key="p_max_age"
        )

        params = current_params()

        st.subheader("目前的儲蓄狀況", divider="gray")
        saving = params.annual_saving
        rate = saving / params.annual_income if params.annual_income > 0 else 0.0
        st.metric(
            "年儲蓄",
            f"{saving:,.0f} 萬",
            delta=f"儲蓄率 {rate:.0%}",
            delta_arrow="off",
            border=True,
        )

        if saving <= 0:
            st.error("年支出大於等於年收入，資產不會累積。請調高收入或降低支出。")
        if params.max_age <= params.current_age:
            st.error("「推算到幾歲」必須大於「目前年齡」。")

    return params
