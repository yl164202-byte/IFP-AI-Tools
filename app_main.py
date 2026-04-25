import streamlit as st

st.set_page_config(page_title="華語教學 AI 工具組", layout="wide")

st.title("🧧 華語教學 AI 邏輯建構工具箱")

st.markdown("""
歡迎使用 AI 輔助華語教學系統。

### 請從側邊欄選擇功能：

1. **高複現文本分析與難度調整** (`Article_difficulty_adjustment.py`)
   - 針對文本進行詞彙等級與複現率掃描。
   
2. **文本生成與自動測驗系統** (`Highly_reproducible_text.py`)
   - 生成符合特定進度的高複現文本，並自動產生不超綱的測驗題。

---
#### 使用說明：
- 本系統基於教材資料庫進行雙層邏輯攔截，確保教學內容不超綱。
- 若側邊欄未顯示功能，請確認 `pages` 資料夾結構是否正確。
""")

st.sidebar.success("請由上方選單切換功能")
