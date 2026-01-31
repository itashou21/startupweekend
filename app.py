import os
import json
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Good job - 特性要約プロトタイプ", layout="centered")
st.title("求職者の「好き/嫌い」から特性を要約（プロトタイプ）")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("環境変数 OPENAI_API_KEY を設定してください。")
    st.stop()

client = OpenAI(api_key=api_key)

# 入力UI
likes = st.text_area("好き（気持ちよく働けた瞬間・環境）", height=160, placeholder="例：裁量が大きいと燃える。目的が明確だと動きやすい…")
dislikes = st.text_area("嫌い（辛かった職場体験・苦手な環境）", height=160, placeholder="例：曖昧な指示、頻繁な方針転換、細かい管理…")
prefs = st.text_area("こだわり（譲れないこと）", height=120, placeholder="例：評価基準が明確、会議少なめ、チャット中心…")

use_schema = st.checkbox("JSONで構造化して返す（おすすめ）", value=True)

if st.button("AIで要約する", type="primary", disabled=not (likes.strip() and dislikes.strip())):
    with st.spinner("分析中..."):
        prompt = f"""
あなたは採用のカルチャーフィット分析の専門家です。
以下の自由記述から、求職者の働き方の特性を抽出してください。

【好き】
{likes}

【嫌い】
{dislikes}

【こだわり】
{prefs}
"""

        if use_schema:
            schema = {
                "name": "candidate_profile",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "summary": {"type": "string"},
                        "work_style": {"type": "array", "items": {"type": "string"}},
                        "communication": {"type": "array", "items": {"type": "string"}},
                        "evaluation": {"type": "array", "items": {"type": "string"}},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "avoid": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "work_style", "communication", "evaluation", "strengths", "avoid"],
                },
            }

            # Responses API（新規はこれ推奨）:contentReference[oaicite:2]{index=2}
            res = client.responses.create(
                model="gpt-5-nano",
                input=[
                    {"role": "system", "content": "出力は必ず指定JSONスキーマに従ってください。"},
                    {"role": "user", "content": prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema["name"],
                        "schema": schema["schema"],
                        "strict": True,
                    }
                },
            )

            data = json.loads(res.output_text)  # output_textが使えるSDKが多い :contentReference[oaicite:3]{index=3}
            st.subheader("要約（構造化）")
            st.json(data)

            st.subheader("読みやすい表示")
            st.write(data["summary"])
            st.write("**働き方**:", " / ".join(data["work_style"]))
            st.write("**コミュニケーション**:", " / ".join(data["communication"]))
            st.write("**評価・モチベ**:", " / ".join(data["evaluation"]))
            st.write("**強み**:", " / ".join(data["strengths"]))
            st.write("**避けたい環境**:", " / ".join(data["avoid"]))

        else:
            res = client.responses.create(
                model="gpt-5-nano",
                input=[
                    {"role": "system", "content": "短く、箇条書きで要約してください。"},
                    {"role": "user", "content": prompt},
                ],
            )
            st.subheader("要約（テキスト）")
            st.write(res.output_text)