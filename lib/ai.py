import json
import os
from openai import OpenAI
from lib.tag_bank import TAG_BANK

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _tag_list_str():
    """TAG_BANK をプロンプト用の文字列にフォーマットする。"""
    lines = []
    for category, tags in TAG_BANK.items():
        lines.append(f"  {category}: {json.dumps(tags, ensure_ascii=False)}")
    return "\n".join(lines)


_TAG_CONSTRAINT = f"""
★重要★ 以下の各カテゴリについて、必ず下記の選択肢の中から当てはまるものだけを選んでください。
選択肢にないタグは絶対に使わないでください。該当なしなら空配列にしてください。

{_tag_list_str()}
"""


# ---------- Embedding ----------

def get_embedding(text: str) -> list[float]:
    """OpenAI Embeddings API でテキストをベクトル化する。"""
    res = _get_client().embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return res.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------- Seeker analysis ----------

_SEEKER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary":       {"type": "string"},
        "work_style":    {"type": "array", "items": {"type": "string"}},
        "communication": {"type": "array", "items": {"type": "string"}},
        "evaluation":    {"type": "array", "items": {"type": "string"}},
        "strengths":     {"type": "array", "items": {"type": "string"}},
        "avoid":         {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "work_style", "communication", "evaluation",
                  "strengths", "avoid"],
}


def analyse_seeker(likes: str, dislikes: str, prefs: str = "") -> dict:
    prompt = f"""あなたは採用のカルチャーフィット分析の専門家です。
以下の内容から、この人の働き方の特性を整理してください。

【好き】
{likes}

【嫌い】
{dislikes}

【こだわり】
{prefs}

{_TAG_CONSTRAINT}

以下のJSON形式で出力してください。
work_style, communication, evaluation, avoid は上記の選択肢から選んでください。
strengths だけは自由記述で構いません。

{{
  "summary": "この人の特性の要約（自由記述）",
  "work_style": [],
  "communication": [],
  "evaluation": [],
  "strengths": [],
  "avoid": []
}}
"""
    res = _get_client().responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "JSON形式でのみ出力してください。タグは指定された選択肢から選んでください。"},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "profile",
                "schema": _SEEKER_SCHEMA,
                "strict": True,
            }
        },
    )
    return json.loads(res.output_text)


# ---------- Office (company) analysis ----------

_OFFICE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary":       {"type": "string"},
        "work_style":    {"type": "array", "items": {"type": "string"}},
        "communication": {"type": "array", "items": {"type": "string"}},
        "evaluation":    {"type": "array", "items": {"type": "string"}},
        "avoid":         {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "work_style", "communication", "evaluation", "avoid"],
}


def analyse_office(personal_likes: str, personal_dislikes: str,
                   workplace_likes: str, workplace_dislikes: str) -> dict:
    prompt = f"""あなたは組織文化の分析専門家です。
ある事業所の担当者が回答した内容から、その事業所の文化・価値観を整理してください。

【個人として好きなこと】
{personal_likes}

【個人として好きではないこと】
{personal_dislikes}

【職場の好きなこと】
{workplace_likes}

【職場の好きではないこと】
{workplace_dislikes}

{_TAG_CONSTRAINT}

以下のJSON形式で出力してください。
work_style, communication, evaluation, avoid は上記の選択肢から選んでください。

{{
  "summary": "この事業所の文化の要約（自由記述）",
  "work_style": [],
  "communication": [],
  "evaluation": [],
  "avoid": []
}}
"""
    res = _get_client().responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "JSON形式でのみ出力してください。タグは指定された選択肢から選んでください。"},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "office_profile",
                "schema": _OFFICE_SCHEMA,
                "strict": True,
            }
        },
    )
    return json.loads(res.output_text)
