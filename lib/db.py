import os
from collections import Counter
from supabase import create_client

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_client = None


def _sb():
    global _client
    if _client is None:
        _client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    return _client


def insert_office(company_name, office_name,
                   personal_likes, personal_dislikes,
                   workplace_likes, workplace_dislikes,
                   work_style, communication, evaluation, avoid):
    _sb().table("offices").insert({
        "company_name": company_name,
        "office_name": office_name,
        "personal_likes": personal_likes,
        "personal_dislikes": personal_dislikes,
        "workplace_likes": workplace_likes,
        "workplace_dislikes": workplace_dislikes,
        "work_style": work_style,
        "communication": communication,
        "evaluation": evaluation,
        "avoid": avoid,
    }).execute()


def all_offices():
    res = _sb().table("offices").select("*").order("created_at", desc=True).execute()
    return res.data


def aggregated_offices():
    """Group responses by (company_name, office_name) and merge tags by majority vote."""
    rows = all_offices()
    groups = {}
    for r in rows:
        key = (r["company_name"], r.get("office_name") or "")
        groups.setdefault(key, []).append(r)

    result = []
    for (company_name, office_name), responses in groups.items():
        n = len(responses)
        threshold = max(1, n // 2)

        merged = {}
        for col in ("work_style", "communication", "evaluation", "avoid"):
            counter = Counter()
            for r in responses:
                counter.update(r[col])
            merged[col] = [tag for tag, cnt in counter.most_common() if cnt >= threshold]

        result.append({
            "company_name": company_name,
            "office_name": office_name or None,
            "work_style": merged["work_style"],
            "communication": merged["communication"],
            "evaluation": merged["evaluation"],
            "avoid": merged["avoid"],
            "response_count": n,
            "response_ids": [r["id"] for r in responses],
        })
    return result


def delete_office(office_id):
    _sb().table("offices").delete().eq("id", office_id).execute()
