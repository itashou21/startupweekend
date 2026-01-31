import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from lib.db import all_offices, aggregated_offices, delete_office

st.set_page_config(page_title="登録事業所一覧 - Good job", layout="centered")
st.title("📋 登録事業所一覧")

agg = aggregated_offices()

if not agg:
    st.info("まだ事業所が登録されていません。サイドバーの「事業所登録」から追加してください。")
    st.stop()

st.write(f"**{len(agg)}事業所**（合計 {sum(a['response_count'] for a in agg)} 名回答）")

for a in agg:
    label = a["company_name"]
    if a.get("office_name"):
        label += f"（{a['office_name']}）"
    label += f" - {a['response_count']}名回答"

    with st.expander(label):
        # --- 集約プロフィール ---
        st.markdown("**統合プロフィール**（多数決で集約）")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**働き方**")
            for tag in a["work_style"]:
                st.write(f"- {tag}")
            st.markdown("**コミュニケーション**")
            for tag in a["communication"]:
                st.write(f"- {tag}")
        with col2:
            st.markdown("**評価軸**")
            for tag in a["evaluation"]:
                st.write(f"- {tag}")
            st.markdown("**避けたい環境**")
            for tag in a["avoid"]:
                st.write(f"- {tag}")

        # --- 個別回答 ---
        if a["response_count"] > 1:
            st.markdown("---")
            st.markdown(f"**個別回答（{a['response_count']}件）**")

            raw = all_offices()
            individual = [r for r in raw if r["id"] in a["response_ids"]]

            for i, r in enumerate(individual, 1):
                st.markdown(f"回答 {i}（{r['created_at']}）")
                tags = []
                for col_name, col_label in [("work_style", "働き方"), ("communication", "コミュ"),
                                             ("evaluation", "評価"), ("avoid", "回避")]:
                    tags.append(f"**{col_label}:** {', '.join(r[col_name])}")
                st.caption(" ｜ ".join(tags))

        # --- 削除 ---
        st.markdown("---")
        for rid in a["response_ids"]:
            if st.button(f"回答 ID {rid} を削除", key=f"del_{rid}"):
                delete_office(rid)
                st.rerun()
