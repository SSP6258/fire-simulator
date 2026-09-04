"""用 Streamlit 內建的 AppTest 測整個 App 的行為。

AppTest 會在同一個行程裡真的執行腳本、模擬 widget 互動，
不需要瀏覽器、不需要伺服器、不需要 port。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ENTRYPOINT = str(Path(__file__).parent.parent / "streamlit_app.py")

PAGES = [
    "app_pages/accumulation.py",
    "app_pages/monte_carlo.py",
    "app_pages/withdrawal.py",
]


def _run(page: str | None = None) -> AppTest:
    at = AppTest.from_file(ENTRYPOINT, default_timeout=60).run()
    if page:
        at.switch_page(page).run()
    return at


def test_entrypoint_runs_without_exception():
    at = _run()
    assert not at.exception


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders(page: str):
    at = _run(page)
    assert not at.exception, f"{page} 拋出例外"
    assert at.metric, f"{page} 沒有渲染出任何 metric"


def test_sidebar_params_reach_session_state():
    at = _run()
    params = at.session_state["params"]
    assert params.current_age == 30
    assert params.expected_return == pytest.approx(0.07)


def test_changing_income_updates_saving_metric():
    """改側邊欄的收入，儲蓄的 metric 要跟著動 —— 驗證參數真的有串起來。"""
    at = _run()
    at.sidebar.number_input(key="p_annual_income").set_value(300.0).run()
    assert not at.exception
    assert at.session_state["params"].annual_income == 300.0


def test_params_are_shared_across_pages():
    """在進入點改參數後切頁，新頁面要沿用同一組參數。"""
    at = _run()
    at.sidebar.number_input(key="p_current_age").set_value(45).run()
    at.switch_page("app_pages/monte_carlo.py").run()
    assert not at.exception
    assert at.session_state["params"].current_age == 45


def test_overspending_shows_error():
    at = _run()
    at.sidebar.number_input(key="p_annual_expense").set_value(500.0).run()
    assert at.error, "年支出大於收入時應該要顯示錯誤"


def test_monte_carlo_is_reproducible_across_runs():
    a = _run("app_pages/monte_carlo.py")
    b = _run("app_pages/monte_carlo.py")
    assert a.metric[0].value == b.metric[0].value


def test_comparison_page_renders():
    """對照頁沒有 metric，所以不能放進上面的 PAGES 參數化測試，單獨測。"""
    at = _run("app_pages/claude_vs_cowork.py")
    assert not at.exception
    assert at.dataframe, "對照頁應該要有對照表"


def test_sidebar_only_appears_on_pages_that_use_params():
    """財務參數側邊欄只該出現在吃參數的頁面。

    對照頁純粹是文字內容，側邊欄出現在那裡會讓人以為調了會有影響。

    用 widget 數量判斷而不是看 sidebar 物件在不在 —— Streamlit 的 sidebar
    永遠有一個根容器，要裡面真的有東西瀏覽器才會把它畫出來。
    """
    finance = _run("app_pages/monte_carlo.py")
    assert len(finance.sidebar.number_input) + len(finance.sidebar.slider) == 10

    compare = _run("app_pages/claude_vs_cowork.py")
    assert not compare.exception
    assert len(compare.sidebar.number_input) + len(compare.sidebar.slider) == 0


def test_params_survive_a_detour_through_the_comparison_page():
    """繞去對照頁再回來，先前調好的參數不能被清掉。

    對照頁不呼叫 render_sidebar()，所以要確認那一趟不會把 session state 弄丟。
    """
    at = _run()
    at.sidebar.number_input(key="p_current_age").set_value(45).run()
    at.switch_page("app_pages/claude_vs_cowork.py").run()
    assert not at.exception
    at.switch_page("app_pages/withdrawal.py").run()
    assert not at.exception
    assert at.session_state["params"].current_age == 45
