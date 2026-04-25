import streamlit as st
import json
import os
import random

@st.cache_data
def load_numeric_vocab(json_path='vocabulary_data.json'):
    if not os.path.exists(json_path): return None
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

st.title("🎯 精準高複現文本生成器 (數位邏輯版)")

data = load_numeric_vocab()

if data:
    # 側邊欄選單
    vols = sorted(list(set(e["vol"] for e in data)))
    sel_v = st.sidebar.selectbox("選擇冊數 (數字)", vols)
    
    lessons = sorted(list(set(e["lesson"] for e in data if e["vol"] == sel_v)))
    sel_l = st.sidebar.selectbox("選擇課數 (數字)", lessons)

    # 詞彙池分類邏輯 (純數字比較)
    target_set = set()
    review_set = set()
    base_set = set()

    for entry in data:
        v = entry["vol"]
        l = entry["lesson"]
        words = entry["vocab"]

        if v == sel_v:
            if l == sel_l:
                target_set.update(words)
            elif (sel_l - 2) <= l < sel_l:
                review_set.update(words)
            elif l < (sel_l - 2):
                base_set.update(words)
        elif v < sel_v:
            base_set.update(words)

    # UI 呈現
    st.sidebar.divider()
    st.sidebar.write(f"📊 **詞彙統計**")
    st.sidebar.write(f"- 本課目標詞: {len(target_set)}")
    st.sidebar.write(f"- 近課複習詞: {len(review_set)}")
    st.sidebar.write(f"- 背景已知詞: {len(base_set)}")

    theme = st.text_input("文章主題", "日常對話")
    
    if st.button("生成高複現 Prompt"):
        # 隨機背景詞
        bg_samples = random.sample(list(base_set), min(len(base_set), 20)) if base_set else []
        
        prompt = f"""你現在是專業華語老師。請撰寫適合學生的閱讀練習。
【程度】：第 {sel_v} 冊 第 {sel_l} 課
【主題】：{theme}
【要求】：
1. 核心詞彙必須出現 3 次以上：{", ".join(list(target_set))}
2. 重點複習詞彙：{", ".join(list(review_set))}
3. 嚴格禁止超綱。字數約 400 字。
"""
        st.text_area("生成的 Prompt", prompt, height=350)