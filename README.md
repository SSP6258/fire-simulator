# 🔥 FIRE 財務自由模擬器

用蒙地卡羅模擬回答一個問題：**照你現在的儲蓄速度，幾歲能財務自由？而運氣的影響有多大？**

多數理財試算器只給你一個數字。這個工具給你**一整片機率分佈** —— 因為「平均年報酬 7%」從來不代表你每年都賺 7%。

## 三個頁面

| 頁面 | 回答的問題 |
|---|---|
| 📈 資產累積推演 | 每年剛好賺到預期報酬的話，幾歲達標？（最樂觀的算法） |
| 🎲 蒙地卡羅模擬 | 跑 1000 次人生，達標機率多少？運氣好壞會差幾倍？ |
| 🏖️ 退休提領分析 | 退休後每年提領，這筆錢撐得過餘生嗎？破產機率多少？ |

三頁共用側邊欄的同一組參數，改一次全部同步。

## 本機執行

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS / Linux 用 source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

瀏覽器會自動開啟 http://localhost:8501。

## 跑測試

```bash
pytest
```

34 個測試，約 2 秒跑完，**不需要瀏覽器**：

- `tests/test_simulate.py` — 純計算邏輯的單元測試（pytest）
- `tests/test_app.py` — 整個 App 的行為測試（Streamlit 內建的 `AppTest`，在記憶體裡執行腳本並模擬 widget 互動）

## 專案結構

```
streamlit_app.py     進入點：set_page_config → 側邊欄 → st.navigation
core/
  simulate.py        純計算，完全不 import streamlit ← 所以能直接用 pytest 測
  charts.py          Altair 圖表建構器
  params.py          側邊欄輸入，唯一碰 session_state 的地方
  cached.py          用 @st.cache_data 包住重運算
  fmt.py             數字格式化
app_pages/           三個頁面，各自是獨立腳本
tests/               單元測試 + AppTest
```

### 兩個刻意的設計決定

**1. `core/simulate.py` 不 import streamlit。**
計算與顯示徹底分離。好處是計算邏輯可以用毫秒級的單元測試驗證，不必啟動伺服器或瀏覽器。這也是為什麼 34 個測試只花 2 秒。

**2. 頁面放 `app_pages/` 而不是 `pages/`。**
`pages/` 是 Streamlit 舊版自動多頁面機制的保留字，跟 `st.navigation` 併用會出現重複的導覽列。

## 關於 requirements.txt

版本號是在 Python 3.13.15 上**實際安裝、實際跑過測試**之後才釘下來的。

反面教材：把 `numpy==1.21.0`（2021 年）這種版本釘死，在新版 Python 上根本沒有預編譯 wheel，pip 會退回原始碼編譯然後失敗，部署直接掛掉。**釘版本要釘你驗證過的版本，不是你以為的版本。**

## 部署到 Streamlit Community Cloud

1. 把 repo 推上 GitHub
2. 到 [share.streamlit.io](https://share.streamlit.io) → **New app**
3. 選這個 repo，主檔案填 `streamlit_app.py`
4. **Advanced settings → Python version 選 3.13**（跟本機一致，避免版本落差）
5. Deploy

這個 App 沒有任何外部 API 或金鑰依賴，所以部署不需要設定 secrets。

## 模型假設與限制

- 年報酬服從 **log-normal 分佈**且各年獨立。用 log-normal 而非常態，是為了避免出現「報酬率低於 -100%、資產變負數」這種不可能的情況
- 儲蓄金額隨通膨等比成長
- 退休後**年初提領**當年生活費（隨通膨調升），餘額再投資一年
- 資產一旦歸零就永久歸零（破產不可逆）
- **未考慮**：稅負、交易費用、報酬序列自相關、勞保勞退、房產、非投資收入

> ⚠️ 本工具為教學用途的簡化模型，**不構成任何投資建議**。

## 授權

MIT
