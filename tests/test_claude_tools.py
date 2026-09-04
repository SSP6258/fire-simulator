"""core/claude_tools.py 的資料完整性測試。

這裡沒有計算邏輯要驗，要防的是「手改資料時把結構弄壞」——
少一個欄位、欄位名打錯、連結貼成內部網址，這些在頁面上不一定看得出來。
"""

from core import claude_tools as t

EXPECTED_COLUMNS = {"面向", "Claude Code", "Claude Cowork"}


def test_comparison_rows_all_share_the_same_columns():
    """每一列都要有完全相同的欄位。

    這條專門抓「新增一列時漏打或打錯欄位名」——
    st.dataframe 遇到這種情況會安靜地多開一欄或填 None，畫面上很難察覺。
    """
    for row in t.COMPARISON:
        assert set(row) == EXPECTED_COLUMNS, f"欄位不一致：{row.get('面向')!r} → {set(row)}"


def test_comparison_has_no_empty_cells():
    for row in t.COMPARISON:
        for key, value in row.items():
            assert value.strip(), f"{row['面向']!r} 的 {key!r} 是空的"


def test_session_log_rows_all_share_the_same_columns():
    expected = {"今天發生的事", "怎麼發現的"}
    for row in t.SESSION_LOG:
        assert set(row) == expected, f"欄位不一致：{row}"


def test_sources_are_public_https_urls():
    """來源必須是能點得開的公開網址，不能是本機路徑或 http。"""
    assert t.SOURCES, "至少要有一個來源"
    for label, url in t.SOURCES:
        assert label.strip()
        assert url.startswith("https://"), f"{label} 的網址不是 https：{url}"


def test_verified_on_is_an_iso_date():
    """查證日期要是 YYYY-MM-DD，讀的人才知道資料多舊。"""
    from datetime import date

    date.fromisoformat(t.VERIFIED_ON)
