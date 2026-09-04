"""頁4 · Claude Code vs Cowork —— 這個專案的副產品。

這頁跟財務無關。它記錄的是「用同一個真實任務比較兩個工具之後，看到的差異」。
資料在 core/claude_tools.py，這裡只負責畫。
"""

import streamlit as st

from core import claude_tools as ct

st.caption(
    "這頁不是財務內容。這個專案的初衷是拿一個真實任務來比較 **Claude Code** 與 "
    "**Claude Cowork**，這裡就是結論。"
)

st.info(ct.HEADLINE, icon=":material/compare_arrows:")

with st.container(border=True):
    st.subheader("功能對照")
    st.dataframe(
        ct.COMPARISON,
        width="stretch",
        hide_index=True,
        column_config={
            "面向": st.column_config.TextColumn(width="small"),
            "Claude Code": st.column_config.TextColumn(width="medium"),
            "Claude Cowork": st.column_config.TextColumn(width="medium"),
        },
    )
    st.caption(ct.FIRSTHAND)
    st.caption(
        f"其餘項目依官方文件整理，查證日期 {ct.VERIFIED_ON}。"
        "產品功能變動很快，要引用前請自己再確認一次。"
    )

with st.container(border=True):
    st.subheader("這些問題是「跑起來」才會發現的")
    st.caption(
        "以下每一項都發生在打造這個 App 的過程中。共通點不是它們有多難，"
        "而是**光看程式碼一個都看不出來** —— 得在你這台機器上跑一次、讀回傳碼、"
        "看它噴什麼，才會浮出來。"
    )
    st.dataframe(
        ct.SESSION_LOG,
        width="stretch",
        hide_index=True,
        column_config={
            "今天發生的事": st.column_config.TextColumn(width="medium"),
            "怎麼發現的": st.column_config.TextColumn(width="large"),
        },
    )
    st.caption(
        "所以分界不在「誰會寫程式」，而在**誰待在「跑 → 看錯誤 → 改 → 再跑」這個迴圈裡**。"
    )

st.subheader("那要怎麼選？")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("##### :material/terminal: 用 Claude Code")
        for item in ct.CODE_FITS:
            st.markdown(f"- {item}")
with col2:
    with st.container(border=True):
        st.markdown("##### :material/description: 用 Cowork")
        for item in ct.COWORK_FITS:
            st.markdown(f"- {item}")

st.success(
    "兩者不是互斥的。**Cowork 產出初版、你拿回本機**，接著在本機反覆迭代、除環境的錯、"
    "跑測試、推 GitHub —— 這段交給 Claude Code。這個 App 本身就是這樣長出來的。",
    icon=":material/lightbulb:",
)

with st.expander("資料來源"):
    for label, url in ct.SOURCES:
        st.markdown(f"- [{label}]({url})")
    st.caption(
        "標示為第一手經驗的項目沒有對應連結 —— 那是使用者自己的操作結果，不是文件記載。"
    )
