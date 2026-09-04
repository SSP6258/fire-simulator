# CLAUDE.md

給 Claude Code 的專案說明。新對話會自動載入這個檔案。

## 工作交接（先讀這個）

`HANDOFF.md` 是跨對話的接續點。**每次新對話開始，先讀 `HANDOFF.md` 再往下做。**

**工作告一段落時要更新它** —— 完成一個任務、使用者要關機、或對話要結束時。
更新的是「目前狀態 / 進行中 / 最近完成 / 待決定」四個區塊，不是逐字抄對話。

只寫從程式碼和 `git log` 看不出來的東西：待辦、卡住的點、已排除的做法、
還沒定案的決策、踩過的環境雷。CLAUDE.md 已經有的規則不要重複。

`HANDOFF.md` 不進版控（在 `.gitignore` 裡），它是本機的工作筆記，不是專案文件。

## 這是什麼

Streamlit 多頁面 App：FIRE（財務自由）蒙地卡羅模擬器。零外部 API，部署在 Streamlit Community Cloud。

## 環境

Windows + Python 3.13.15。虛擬環境在 `.venv/`，**所有指令都要用它的直譯器**：

```bash
./.venv/Scripts/python.exe -m pytest      # 測試
./.venv/Scripts/streamlit.exe run streamlit_app.py
```

### 環境陷阱

**1. `streamlit docs` 在繁中 Windows 會炸。**
主控台預設 cp950，吃不下官方文件裡的 emoji，會噴 `UnicodeEncodeError`。前面加環境變數就好：

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/streamlit.exe docs st.metric
```

**2. `gh` 不在繼承的 PATH 裡。**
它裝在 machine PATH，但已啟動的行程拿的是舊環境變數。Bash 呼叫前先：

```bash
export PATH="$PATH:/c/Program Files/GitHub CLI"
```

**3. Windows 260 字元路徑上限。**
不要在很深的目錄底下建 venv。Streamlit 套件內含層次很深的 skill 資產，
在深路徑安裝會噴 `OSError: [WinError 3]`，訊息看起來完全不像路徑問題。

## 架構規則

**`core/simulate.py`、`core/charts.py`、`core/fmt.py` 絕對不能 import streamlit。**
這是這個專案最重要的一條約束。它們是純函式，所以能用毫秒級的單元測試驗證。要用到 Streamlit 的東西（快取、widget）請放 `core/cached.py` 或 `core/params.py`。

**頁面目錄叫 `app_pages/`，不是 `pages/`。**
`pages/` 是 Streamlit 舊版自動多頁面的保留名稱，跟 `st.navigation` 併用會產生重複導覽列。

**頁面檔案是直接執行的腳本，不要包成 `def app():`。**
這是 `st.navigation` 的規範寫法。標題由 `streamlit_app.py` 用 `st.title(page.title, icon=page.icon)` 統一處理，頁面內不要再呼叫 `st.title`。

**參數只有一個來源。**
`core/params.py` 的 `DEFAULTS` 定義所有 session state 鍵值，`init_state()` 只在進入點呼叫一次。頁面讀 `st.session_state.params`（一個 `FireParams` frozen dataclass），不要自己去讀個別的 `p_*` 鍵。

## Streamlit 版本相關（1.63）

寫任何 Streamlit 程式碼前，先跑 discovery 拿版本對應的官方文件：

```bash
python ~/.claude/skills/developing-with-streamlit/scripts/discover.py --project-dir .
```

已知的重點：

- **`use_container_width` 已棄用** → 用 `width="stretch"` 或 `width="content"`
- **用 Altair 不用 Plotly** —— Altair 隨 Streamlit 內建，少一個相依就少一個部署風險
- **導覽和按鈕用 Material Symbols**（`:material/icon_name:`）而不是 emoji
- **`st.components.v1` 已棄用** → 用 `st.components.v2`
- 版面優先用 `st.container(horizontal=True)`，`st.columns` 留給固定比例的格線

## 測試

```bash
pip install -r requirements-dev.txt   # pytest 在這份，不在 requirements.txt
pytest                                # 39 個測試，約 4 秒
```

- `tests/test_simulate.py` — 純計算的單元測試
- `tests/test_app.py` — 用 `streamlit.testing.v1.AppTest` 在記憶體裡跑整個 App，不需要瀏覽器
- `tests/test_claude_tools.py` — 對照頁的資料完整性（欄位一致、來源是 https）

**改任何計算邏輯後，一定要跑 `pytest`。** 特別注意這兩條保護性測試：

- `test_zero_volatility_reproduces_deterministic_path` — 把蒙地卡羅與確定性推演綁在一起，改壞任一邊都會被抓到
- `test_success_rate_decreases_as_withdrawal_rate_rises` — 提領率越高成功率只能越低，違反單調性代表邏輯錯了

`pytest.ini` 裡的 `pythonpath = .` 不能刪，否則直接下 `pytest` 會 `ModuleNotFoundError: No module named 'core'`。

## 不要做的事

- 不要把 `.venv/` 加進版控
- 不要在 `requirements.txt` 釘沒有實際驗證過的版本
- 不要引入需要 API 金鑰的相依 —— 這個 App 刻意保持零外部依賴
- 不要用 CSS 硬改樣式；先試 `.streamlit/config.toml` 的主題設定與原生元件
