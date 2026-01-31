import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from lib.ai import analyse_seeker
from lib.db import aggregated_offices
from lib.matching import calc_match_score

st.set_page_config(page_title="求職者マッチング - Good job", layout="centered")
st.title("🔍 価値観マッチング")
st.caption("あなたの「好き」「好きではない」から、合う事業所を見つけます")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY が設定されていません")
    st.stop()

# --- 入力 ---
st.subheader("あなたのことを教えてください")

likes = st.text_area("好きなこと", height=140,
                      placeholder="例：チームで何かを作る、自分のペースで働く、新しい技術を試す…")
dislikes = st.text_area("好きではないこと", height=140,
                         placeholder="例：意味のない会議、細かい管理、変化のない日々…")
prefs = st.text_area("こだわり（譲れないこと）", height=100,
                      placeholder="例：リモートワーク、フラットな関係、成果で評価…")

# --- 分析 & マッチング ---
if st.button("分析開始", type="primary"):
    if not (likes.strip() or dislikes.strip() or prefs.strip()):
        st.warning("少なくとも1つは入力してください")
        st.stop()

    offices = aggregated_offices()
    if not offices:
        st.warning("まだ事業所が登録されていません。先に事業所登録を行ってください。")
        st.stop()

    with st.spinner("AIがあなたの価値観を分析中..."):
        person = analyse_seeker(likes, dislikes, prefs)

    # --- 自分の特性表示 ---
    st.divider()
    st.subheader("あなたの特性")
    st.write(person.get("summary", ""))
    st.write("**働き方：**", " / ".join(person.get("work_style", [])))
    st.write("**コミュニケーション：**", " / ".join(person.get("communication", [])))
    st.write("**評価軸：**", " / ".join(person.get("evaluation", [])))
    st.write("**強み：**", " / ".join(person.get("strengths", [])))
    st.write("**避けたい環境：**", " / ".join(person.get("avoid", [])))

    # --- マッチング ---
    st.divider()
    st.subheader("あなたに合いそうな事業所")

    results = []
    for o in offices:
        r = calc_match_score(person, o)
        label = o["company_name"]
        if o.get("office_name"):
            label += f"（{o['office_name']}）"
        label += f"【{o['response_count']}名回答】"
        results.append({"label": label, "office": o, **r})

    results.sort(key=lambda x: x["score"], reverse=True)

    matched = [r for r in results if r["score"] >= 1]

    if not matched:
        st.info("マッチする事業所が見つかりませんでした。")
    else:
        st.write(f"**{len(matched)}件**の事業所が見つかりました。")
        for r in matched:
            with st.expander(f"{r['label']}｜相性 {r['score']} 点"):
                if r["reasons"]:
                    st.write("**合いそうな点**")
                    for x in r["reasons"]:
                        st.write(f"- {x}")
                if r["risks"]:
                    st.write("**注意点**")
                    for x in r["risks"]:
                        st.write(f"- {x}")
