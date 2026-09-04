"""Claude Code 與 Claude Cowork 的對照資料。

這個模組刻意**不 import streamlit** —— 跟 simulate/charts/fmt 同一條規矩，
純資料才能用毫秒級的單元測試驗證。頁面只負責把這裡的東西畫出來。

資料有兩種來源，混在一起會誤導人，所以分開標示：
  · 官方文件（見 SOURCES，查證日期 VERIFIED_ON）
  · 使用者自己用 Cowork 做過 Streamlit App 的第一手經驗（見 FIRSTHAND）

第一版曾經把差異寫成「Code 寫程式、Cowork 做文件簡報」，那是錯的 ——
使用者實際用 Cowork 產出過 Streamlit App。修正後的分界見 HEADLINE。
"""

from __future__ import annotations

VERIFIED_ON = "2026-09-04"

# 一句話總結。
HEADLINE = (
    "**兩個都寫得出一支 Streamlit App。真正的差別是「誰把它跑起來」。** "
    "Cowork 把檔案交到你的資料夾；Claude Code 在你的機器上把它跑起來、"
    "撞到錯誤、然後改到好。"
)

# 標示哪些結論來自使用者自己的操作，而不是官方文件。
FIRSTHAND = (
    "標示 :material/person: 的項目來自你自己的使用經驗（用 Cowork 做過 Streamlit App，"
    "透過桌面 App 把檔案寫進本機資料夾，再自己在本機跑起來），不是從官方文件推論的。"
)

COMPARISON: list[dict[str, str]] = [
    {
        "面向": "能不能產出一支 Streamlit App",
        "Claude Code": "可以",
        "Claude Cowork": ":material/person: 可以 —— 這點實測過，不要被「它只做文件」的說法誤導",
    },
    {
        "面向": "程式碼在哪裡執行",
        "Claude Code": "你的機器。你的 venv、你的 port、你的 git",
        "Claude Cowork": "Anthropic 的雲端隔離環境",
    },
    {
        "面向": "檔案怎麼落到你的磁碟",
        "Claude Code": "本來就在你的工作目錄裡，沒有搬運這一步",
        "Claude Cowork": ":material/person: 透過桌面 App 寫進你指定的資料夾",
    },
    {
        "面向": "誰負責把 App 跑起來",
        "Claude Code": "它自己跑，看到 traceback 自己改，改完再跑",
        "Claude Cowork": ":material/person: 交件之後由你自己跑",
    },
    {
        "面向": "本機環境出問題時",
        "Claude Code": "在現場。能讀 exit code、netstat、venv 內部結構去診斷",
        "Claude Cowork": "看不到你的機器狀態，這類問題會落回你身上",
    },
    {
        "面向": "本機終端機／編輯器",
        "Claude Code": "有，這正是它的核心",
        "Claude Cowork": "沒有 —— 官方說明文件明列的限制",
    },
    {
        "面向": "介面",
        "Claude Code": "終端機 CLI、IDE 擴充（VS Code / JetBrains）、桌面與網頁",
        "Claude Cowork": "網頁、桌面（macOS / Windows / ChromeOS / Linux）、行動、Chrome 擴充",
    },
    {
        "面向": "專案脈絡怎麼傳遞",
        "Claude Code": "CLAUDE.md 自動載入；對話與記憶按工作目錄分桶存在本機",
        "Claude Cowork": "你指定資料夾與連接器，Claude 只看得到那些",
    },
    {
        "面向": "無人值守／排程",
        "Claude Code": "做得到，但要自己設（排程 agent、cron）",
        "Claude Cowork": "內建排程，裝置離線也能跑",
    },
    {
        "面向": "瀏覽器操作",
        "Claude Code": "非內建能力",
        "Claude Cowork": "內建瀏覽器，可登入網站、填表單",
    },
    {
        "面向": "分享",
        "Claude Code": "對話存在本機，換目錄就換一份",
        "Claude Cowork": "官方明列：工作階段無法分享給他人",
    },
]

# 今天這場演練的逐項對照。
# 重點不是「Cowork 做不到」，而是「這些事都得靠跑起來看結果才會發現」。
SESSION_LOG: list[dict[str, str]] = [
    {
        "今天發生的事": "venv 的 .exe 啟動器全部失效",
        "怎麼發現的": "跑 pip.exe 拿到 rc=1，但 python.exe 正常 —— 只看程式碼看不出來",
    },
    {
        "今天發生的事": "cmd.exe 的 /c 參數被 Git Bash 當成路徑轉換掉",
        "怎麼發現的": "run.bat 沒被執行，從輸出裡的 cmd 橫幅才看出來",
    },
    {
        "今天發生的事": "run.bat 錯誤時 exit code 是 0",
        "怎麼發現的": "刻意造一個沒有 venv 的目錄跑一次，讀回傳碼",
    },
    {
        "今天發生的事": "對照表有一列欄位順序不一致",
        "怎麼發現的": "寫測試比對每列的 key 集合才抓到",
    },
    {
        "今天發生的事": "GitHub repo 其實早就建好推過了",
        "怎麼發現的": "git ls-remote 對過 SHA，不然會多開一個重複的 repo",
    },
    {
        "今天發生的事": "舊路徑留下無法 resume 的孤兒對話桶",
        "怎麼發現的": "翻 ~/.claude/projects/ 底下的實際目錄",
    },
]

# 兩邊各自順手的事。
COWORK_FITS: list[str] = [
    "從零產出一支 App 的初版程式碼，再自己拿回本機跑",
    "把模擬結果整理成給同事看的簡報或報表",
    "讀一疊 PDF 合約或年報，整理成摘要",
    "定期上某個網站抓資料填進試算表 —— 它有內建瀏覽器",
    "排程跑的例行工作，裝置關機也不影響",
]

CODE_FITS: list[str] = [
    "在既有 repo 裡改程式，改完立刻跑測試確認沒改壞",
    "除錯本機環境 —— venv、PATH、port 被占用這類只在你機器上發生的問題",
    "處理 git 衝突、開 PR、review diff",
    "需要「跑起來 → 看錯誤 → 改 → 再跑」反覆迭代的工作",
]

SOURCES: list[tuple[str, str]] = [
    ("Claude Cowork 產品頁", "https://claude.com/product/cowork"),
    (
        "Get started with Claude Cowork（官方說明中心）",
        "https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork",
    ),
]
