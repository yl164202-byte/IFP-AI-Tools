import streamlit as st
import json
import jieba
import re
import os
import pandas as pd

# --- 核心邏輯函數 ---

def get_numeric_key(text):
    """
    從字串中提取數字並轉為 int，用於精確的數值排序。
    """
    if text is None: return 0
    match = re.search(r'\d+', str(text))
    return int(match.group()) if match else 0

def load_and_standardize_data(json_path):
    """
    載入並標準化數據：
    解決「第十一課」被誤轉為「第101課」的邏輯斷層。
    """
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 關鍵修正：將對照表改為有序列表，並將複合詞排在單個詞前面
        # 這樣「十一」會先被匹配為 11，而不會被拆成 10 和 1
        cn_to_num_pairs = [
            ('十五', '15'), ('十四', '14'), ('十三', '13'), ('十二', '12'), ('十一', '11'),
            ('十', '10'), ('九', '9'), ('八', '8'), ('七', '7'), ('六', '6'), 
            ('五', '5'), ('四', '4'), ('三', '3'), ('二', '2'), ('一', '1')
        ]
        
        for entry in data:
            v_str = str(entry.get("第幾冊", ""))
            l_str = str(entry.get("第幾課", ""))
            
            # 依序進行字串替換
            for cn, num in cn_to_num_pairs:
                v_str = v_str.replace(cn, num)
                l_str = l_str.replace(cn, num)
            
            # 清洗並儲存標準化後的結果
            entry["第幾冊"] = v_str.strip()
            entry["第幾課"] = l_str.strip()
            # 同時清洗詞彙與語法點內容
            entry["詞彙"] = [str(w).strip() for w in entry.get("詞彙", [])]
            entry["語法點"] = [str(w).strip() for w in entry.get("語法點", [])]
            
        return data
    except Exception as e:
        st.error(f"資料標準化處理失敗: {e}")
        return None

def get_vocab_maps(data):
    """建立全域詞彙映射表，用於追蹤詞彙首次出現的出處"""
    full_vocab_map = {}
    # 物理排序：先冊後課，確保索引記錄的是最早出現位置
    sorted_data = sorted(data, key=lambda e: (get_numeric_key(e["第幾冊"]), get_numeric_key(e["第幾課"])))
    
    for entry in sorted_data:
        loc_str = f"{entry['第幾冊']}{entry['第幾課']}"
        # 同時掃描詞彙與語法點欄位
        all_items = entry.get("詞彙", []) + entry.get("語法點", [])
        for word in all_items:
            clean_word = str(word).strip()
            if clean_word and clean_word not in full_vocab_map:
                full_vocab_map[clean_word] = loc_str
    return full_vocab_map

# --- Streamlit 介面 UI ---

st.set_page_config(page_title="當代中文分析器", layout="wide")
st.title("📖 當代中文：超綱詞檢驗 (數位標準化版)")

# 1. 載入並修正數據
vocab_data = load_and_standardize_data('augmented_vocabulary.json')

if vocab_data:
    # 建立詞彙與出處映射表
    full_vocab_map = get_vocab_maps(vocab_data)
    
    # 設定繁體斷詞字典
    if os.path.exists('dict.txt.big'):
        jieba.set_dictionary('dict.txt.big')
    
    # --- 2. 側邊欄：進度設定 (已修正 101 與排序問題) ---
    st.sidebar.header("進度設定")
    
    # 冊數：按數值排序
    unique_vols = sorted(list(set(e["第幾冊"] for e in vocab_data)), key=get_numeric_key)
    sel_vol = st.sidebar.selectbox("選擇冊數", unique_vols)
    
    # 課數：按數值排序
    unique_lessons = sorted(list(set(e["第幾課"] for e in vocab_data if e["第幾冊"] == sel_vol)), key=get_numeric_key)
    sel_lesson = st.sidebar.selectbox("選擇課數", unique_lessons)

    # 計算權重用於比對已學過的範圍
    target_weight = get_numeric_key(sel_vol) * 1000 + get_numeric_key(sel_lesson)

    # --- 3. 分析與交互區 ---
    input_text = st.text_area("請輸入待分析文本：", height=250, placeholder="在此輸入文章內容...")

    if st.button("開始分析"):
        if not input_text.strip():
            st.warning("請先輸入文本。")
        else:
            # A. 提取目前進度前的所有詞彙 (白名單)
            known_vocab = set()
            for entry in vocab_data:
                w = get_numeric_key(entry["第幾冊"]) * 1000 + get_numeric_key(entry["第幾課"])
                if w <= target_weight:
                    known_vocab.update(entry.get("詞彙", []))
                    known_vocab.update(entry.get("語法點", []))

            # B. 文本清理與動態注入全域詞庫 (確保分詞邊界精準)
            clean_content = "".join(re.findall(r'[\u4e00-\u9fa5]+', input_text))
            for w in full_vocab_map.keys():
                jieba.add_word(w)
            
            # C. 斷詞分析與超綱檢索
            seg_list = list(jieba.cut(clean_content))
            oob_details = []
            seen = set()
            for word in seg_list:
                word = word.strip()
                if len(word) > 1 and word not in known_vocab and word not in seen:
                    source = full_vocab_map.get(word, "未收錄")
                    oob_details.append((word, source))
                    seen.add(word)
            
            # D. 結果排序：按冊課數值排序，未收錄置於末尾
            def final_oob_sort(item):
                src = item[1]
                if src == "未收錄": return (True, 0, 0)
                nums = re.findall(r'\d+', src)
                v = int(nums[0]) if len(nums) > 0 else 0
                l = int(nums[1]) if len(nums) > 1 else 0
                return (False, v, l)
            
            oob_details.sort(key=final_oob_sort)

            # --- E. 結果顯示與提示詞生成 ---
            st.divider()
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📊 分析結果")
                st.write(f"當前設定進度：**{sel_vol} {sel_lesson}**")
                st.metric("超綱詞總數", len(oob_details))
                if oob_details:
                    df = pd.DataFrame(oob_details, columns=["超綱詞彙", "教材出處"])
                    st.table(df)
                else:
                    st.success("本段文字完全符合學生當前進度。")

            with col2:
                st.subheader("🤖 AI 改寫助手提示詞")
                if oob_details:
                    # 隨機挑選 15 個已學詞範例作為難度參考
                    sample_known = "、".join(list(known_vocab)[:15])
                    oob_str = "、".join([f"{w}({s})" for w, s in oob_details])
                    
                    prompt_template = f"""你現在是一位專業的對外華語老師。請針對以下【原始文本】中標註為【超綱詞】的部分進行優化：

【當前學生程度】：截至《當代中文課程》{sel_vol} {sel_lesson}
【已知詞彙範例】：{sample_known}
【超綱詞清單（附出處）】：{oob_str}

【原始文本】：
{input_text}

【修改要求】：
1. 僅針對清單中的超綱詞進行修改，其餘部分盡量保持原狀。
2. 若該詞標註為「未收錄」，代表不在教材範圍內，請優先替換。
3. 若該詞標註為「第X冊」，代表學生未來才會學到，請嘗試替換為學生已學過的簡單詞彙。
4. 若該詞為關鍵專有名詞且無法替換，請予以保留。
5. 請整理並輸出：
   - 超綱詞處理清單（原詞 -> 修改後詞彙 / 理由）。
   - 修改後的完整文本。"""

                    st.text_area("生成的 AI 提示詞 (可直接複製)：", prompt_template, height=400)
                else:
                    st.info("符合進度，無需修正。")

else:
    st.error("錯誤：找不到 'augmented_vocabulary.json' 檔案。")
