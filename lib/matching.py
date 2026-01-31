def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def calc_match_score(person, office, person_embedding=None, office_embedding=None):
    """Calculate match score combining embedding similarity and tag matching.

    - Embedding similarity (summary): main score (0-100)
    - Tag matching: used for explainability (reasons / risks)
    """
    # --- Embedding-based score (main) ---
    if person_embedding is not None and office_embedding is not None:
        sim = _cosine_similarity(person_embedding, office_embedding)
        # cosine similarity typically ranges 0.3-0.9 for related texts
        # normalize to 0-100 scale: map 0.4-0.9 -> 0-100
        score = int(max(0, min(100, (sim - 0.4) / 0.5 * 100)))
    else:
        score = 0

    # --- Tag matching (explainability) ---
    reasons = []
    risks = []

    for tag in person.get("work_style", []):
        if tag in office.get("work_style", []):
            reasons.append(f"働き方が一致：{tag}")

    for tag in person.get("communication", []):
        if tag in office.get("communication", []):
            reasons.append(f"コミュニケーションが合う：{tag}")

    for tag in person.get("evaluation", []):
        if tag in office.get("evaluation", []):
            reasons.append(f"評価軸が合う：{tag}")

    for av in person.get("avoid", []):
        if av in office.get("work_style", []):
            risks.append(f"苦手な要素と衝突：{av}")
        if av in office.get("communication", []):
            risks.append(f"苦手なコミュニケーション：{av}")

    for av in office.get("avoid", []):
        if av in person.get("work_style", []):
            risks.append(f"事業所が避けたい傾向と一致：{av}")

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
    }
