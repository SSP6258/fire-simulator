"""FIRE 財務自由模擬器 —— 進入點。

職責只有四件事：
  1. set_page_config（必須是第一個 st 呼叫）
  2. 初始化 session state
  3. 畫出三頁共用的側邊欄，把參數存進 session state
  4. 交給 st.navigation 決定要跑哪一頁

每頁的內容都在 app_pages/ 底下，各自是一支獨立的腳本。
"""

import streamlit as st

from core.params import init_state, render_sidebar

st.set_page_config(
    page_title="FIRE 財務自由模擬器",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()

# 先把每一頁綁成變數，才能在下面用「物件比對」判斷目前在哪一頁。
# 不用標題字串比對 —— 改個標題就會安靜地失效，這種 bug 很難找。
ACCUMULATION = st.Page(
    "app_pages/accumulation.py",
    title="資產累積推演",
    icon=":material/trending_up:",
    default=True,
)
MONTE_CARLO = st.Page(
    "app_pages/monte_carlo.py",
    title="蒙地卡羅模擬",
    icon=":material/casino:",
)
WITHDRAWAL = st.Page(
    "app_pages/withdrawal.py",
    title="退休提領分析",
    icon=":material/beach_access:",
)
CLAUDE_VS_COWORK = st.Page(
    "app_pages/claude_vs_cowork.py",
    title="Claude Code vs Cowork",
    icon=":material/compare_arrows:",
)

# 需要財務參數的頁面。對照頁純粹是文字內容，不吃這些參數，
# 讓側邊欄在那頁出現只會佔版面又讓人以為調了會有影響。
PAGES_NEEDING_PARAMS = (ACCUMULATION, MONTE_CARLO, WITHDRAWAL)

page = st.navigation(
    [ACCUMULATION, MONTE_CARLO, WITHDRAWAL, CLAUDE_VS_COWORK],
    position="top",
)

# 側邊欄只畫在需要它的頁面。沒有任何東西寫進 sidebar 時，Streamlit 會整個收掉。
# 回傳值存進 session state，各頁面直接讀 st.session_state.params。
if page in PAGES_NEEDING_PARAMS:
    st.session_state.params = render_sidebar()

st.title(page.title, icon=page.icon)

page.run()

st.divider()
st.caption(
    "本工具為教學用途的簡化模型，假設報酬服從 log-normal 分佈且各年獨立，"
    "未考慮稅負、費用、報酬序列自相關與個人狀況。**不構成任何投資建議。**"
)
