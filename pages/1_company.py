import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from lib.ai import analyse_office
from lib.db import insert_office

st.set_page_config(page_title="事業所登録 - Good job", layout="centered")
st.title("🏢 事業所登録")
st.caption("あなたの事業所の価値観を登録してください")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY が設定されていません")
    st.stop()

# --- 基本情報 ---
st.subheader("基本情報")
company_name = st.text_input("会社名（法人名）", placeholder="例：株式会社グッドジョブ")
office_name = st.text_input("事業所名（拠点名・任意）", placeholder="例：大阪本社")

# --- 自由記述 ---
st.subheader("価値観を教えてください")
st.markdown("給与や条件ではなく、**日々の働き方や雰囲気**について自由に書いてください。")

personal_likes = st.text_area(
    "あなた個人として好きなこと",
    placeholder="例：新しいことに挑戦する、チームで助け合う、一人で集中する時間…",
    height=120,
)
personal_dislikes = st.text_area(
    "あなた個人として好きではないこと",
    placeholder="例：細かいルールが多い、急な予定変更、形式的な会議…",
    height=120,
)
workplace_likes = st.text_area(
    "職場の好きなところ",
    placeholder="例：風通しが良い、意見が言いやすい、裁量がある…",
    height=120,
)
workplace_dislikes = st.text_area(
    "職場の好きではないところ",
    placeholder="例：トップダウンすぎる、雑談がない、評価基準が不透明…",
    height=120,
)

# --- 分析 & 保存 ---
if st.button("AI分析して登録", type="primary"):
    if not company_name.strip():
        st.warning("会社名を入力してください")
        st.stop()
    if not (personal_likes.strip() or workplace_likes.strip()):
        st.warning("好きなことを少なくとも1つ入力してください")
        st.stop()

    with st.spinner("AIが価値観を分析中..."):
        profile = analyse_office(
            personal_likes, personal_dislikes,
            workplace_likes, workplace_dislikes,
        )

    st.success("分析完了！")

    # プレビュー
    st.subheader("分析結果プレビュー")
    st.write(profile.get("summary", ""))
    st.write("**働き方：**", " / ".join(profile.get("work_style", [])))
    st.write("**コミュニケーション：**", " / ".join(profile.get("communication", [])))
    st.write("**評価軸：**", " / ".join(profile.get("evaluation", [])))
    st.write("**避けたい環境：**", " / ".join(profile.get("avoid", [])))

    # DB保存
    insert_office(
        company_name=company_name.strip(),
        office_name=office_name.strip() or None,
        personal_likes=personal_likes,
        personal_dislikes=personal_dislikes,
        workplace_likes=workplace_likes,
        workplace_dislikes=workplace_dislikes,
        work_style=profile["work_style"],
        communication=profile["communication"],
        evaluation=profile["evaluation"],
        avoid=profile["avoid"],
    )
    st.success("事業所を登録しました！")
