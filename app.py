import os
import json
import streamlit as st
from openai import OpenAI

# ============================
# 初期設定
# ============================
st.set_page_config(
    page_title="Good job - マッチングMVP",
    layout="centered"
)

st.title("🔍 Good job｜価値観マッチング")
st.caption("あなたの「働き方」と合う会社を見つけます")

# OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY が設定されていません")
    st.stop()

# ============================
# 仮の企業データ（あとでDB化可）
# ============================
import random

# ============================
# 企業データを「実在しそうに見える架空名」で大量生成
# ============================

TAG_BANK = {
    "work_style": [
        "裁量が大きい", "スピード重視", "安定志向", "手順重視", "柔軟", "自走歓迎",
        "品質重視", "改善志向", "挑戦重視", "顧客志向", "データ重視", "現場主義",
        "リモート前提", "出社多め", "変化が多い", "役割分担明確"
    ],
    "communication": [
        "チャット中心", "会議少なめ", "会議多め", "対面中心", "丁寧", "フラット",
        "雑談多め", "ドキュメント重視", "報連相重視", "非同期中心"
    ],
    "evaluation": [
        "成果主義", "プロセス重視", "チーム重視", "個人重視", "挑戦を評価", "安定運用を評価",
        "顧客満足を評価", "数値目標重視"
    ],
    "avoid": [
        "指示待ち", "受け身", "曖昧さが多い", "急な変更", "個人主義", "細かい管理",
        "コミュニケーション不足", "マルチタスク過多"
    ]
}

# 会社名パーツ（架空だが“ありそう”寄り）
NAME_PARTS_1 = ["東和", "西京", "南星", "北辰", "大樹", "青海", "光葉", "瑞穂", "桜坂", "若葉", "翔陽", "明和", "京浜", "新都", "山陽"]
NAME_PARTS_2 = ["テック", "ソリューションズ", "システムズ", "パートナーズ", "デジタル", "インサイト", "リンク", "ラボ", "ネクスト", "ワークス", "アセット", "プランニング"]
INDUSTRIES = [
    "SaaS", "製造", "人材", "物流", "医療", "小売", "広告", "建設", "金融", "教育", "飲食", "エネルギー"
]

def pick_unique(rng, pool, k):
    return rng.sample(pool, k)

def generate_company_profile(rng):
    # ほどよく“偏り”が出るように数を固定
    work_style = pick_unique(rng, TAG_BANK["work_style"], k=3)
    communication = pick_unique(rng, TAG_BANK["communication"], k=3)
    evaluation = pick_unique(rng, TAG_BANK["evaluation"], k=2)
    avoid = pick_unique(rng, TAG_BANK["avoid"], k=2)

    return {
        "work_style": work_style,
        "communication": communication,
        "evaluation": evaluation,
        "avoid": avoid
    }

def generate_company_name(rng):
    p1 = rng.choice(NAME_PARTS_1)
    p2 = rng.choice(NAME_PARTS_2)
    industry = rng.choice(INDUSTRIES)
    suffix = rng.choice(["株式会社", "合同会社"])
    # 例：東和テック株式会社（SaaS）
    return f"{p1}{p2}{suffix}（{industry}）"

def generate_companies(n=50, seed=42):
    rng = random.Random(seed)
    names = set()
    companies = []
    while len(companies) < n:
        name = generate_company_name(rng)
        # 同名回避
        if name in names:
            continue
        names.add(name)
        companies.append({
            "name": name,
            "profile": generate_company_profile(rng)
        })
    return companies

# ここで社数を増やせる（例：50社）
COMPANIES = generate_companies(n=60, seed=2026)


# ============================
# マッチングロジック
# ============================
def calc_match_score(person, company):
    score = 0
    reasons = []
    risks = []

    for tag in person["work_style"]:
        if tag in company["profile"]["work_style"]:
            score += 10
            reasons.append(f"働き方が一致：{tag}")

    for tag in person["communication"]:
        if tag in company["profile"]["communication"]:
            score += 8
            reasons.append(f"コミュニケーションが合う：{tag}")

    for avoid in person["avoid"]:
        if avoid in company["profile"]["work_style"]:
            score -= 15
            risks.append(f"苦手な要素と衝突：{avoid}")

    return {
        "score": max(0, min(100, score)),
        "reasons": reasons,
        "risks": risks
    }

# ============================
# 入力UI
# ============================
st.subheader("あなたのことを教えてください")

likes = st.text_area("好きなもの", height=140)
dislikes = st.text_area("嫌いなもの", height=140)
prefs = st.text_area("こだわり（譲れないこと）", height=100)

# ============================
# 実行
# ============================
if st.button("分析開始", type="primary"):
    if not (likes and dislikes):
        st.warning("好き・嫌いは必須です")
        st.stop()

    with st.spinner("分析中..."):
        prompt = f"""
あなたは採用のカルチャーフィット分析の専門家です。
以下の内容から、この人の働き方の特性を整理してください。

【好き】
{likes}

【嫌い】
{dislikes}

【こだわり】
{prefs}

以下のJSON形式で出力してください。

{{
  "summary": "...",
  "work_style": [],
  "communication": [],
  "evaluation": [],
  "strengths": [],
  "avoid": []
}}
"""

        res = client.responses.create(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": "JSON形式でのみ出力してください。"},
                {"role": "user", "content": prompt}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "profile",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,  # ★必須
                        "properties": {
                            "summary": {"type": "string"},
                            "work_style": {"type": "array", "items": {"type": "string"}},
                            "communication": {"type": "array", "items": {"type": "string"}},
                            "evaluation": {"type": "array", "items": {"type": "string"}},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "avoid": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["summary", "work_style", "communication", "evaluation", "strengths", "avoid"]
                    },
                    "strict": True
                }
            }

        )

        person = json.loads(res.output_text)

    # ============================
    # 表示
    # ============================
    st.divider()
    st.subheader("🧠 あなたの特性")

    st.write(person["summary"])
    st.write("**働き方**:", " / ".join(person["work_style"]))
    st.write("**コミュニケーション**:", " / ".join(person["communication"]))
    st.write("**評価軸**:", " / ".join(person["evaluation"]))
    st.write("**強み**:", " / ".join(person["strengths"]))
    st.write("**避けたい環境**:", " / ".join(person["avoid"]))

    # ============================
    # マッチング
    # ============================
    st.divider()
    st.subheader("🏢 あなたに合いそうな会社")

    results = []
    for c in COMPANIES:
        r = calc_match_score(person, c)
        results.append({
            "name": c["name"],
            **r
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    for r in results:
        with st.expander(f"{r['name']}｜相性 {r['score']} 点"):
            st.write("✅ 合いそうな点")
            for x in r["reasons"]:
                st.write(f"- {x}")

            if r["risks"]:
                st.write("⚠ 注意点")
                for x in r["risks"]:
                    st.write(f"- {x}")
