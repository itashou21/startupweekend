def calc_match_score(person, office):
    """Calculate match score between a seeker profile and an office profile.

    person: dict with keys work_style, communication, evaluation, avoid (lists)
    office: dict with keys work_style, communication, evaluation, avoid (lists)
    """
    score = 0
    reasons = []
    risks = []

    for tag in person.get("work_style", []):
        if tag in office.get("work_style", []):
            score += 10
            reasons.append(f"働き方が一致：{tag}")

    for tag in person.get("communication", []):
        if tag in office.get("communication", []):
            score += 8
            reasons.append(f"コミュニケーションが合う：{tag}")

    for tag in person.get("evaluation", []):
        if tag in office.get("evaluation", []):
            score += 6
            reasons.append(f"評価軸が合う：{tag}")

    # person's avoid vs office's work_style/communication
    for av in person.get("avoid", []):
        if av in office.get("work_style", []):
            score -= 15
            risks.append(f"苦手な要素と衝突：{av}")
        if av in office.get("communication", []):
            score -= 10
            risks.append(f"苦手なコミュニケーション：{av}")

    # office's avoid vs person's work_style
    for av in office.get("avoid", []):
        if av in person.get("work_style", []):
            score -= 8
            risks.append(f"事業所が避けたい傾向と一致：{av}")

    return {
        "score": max(0, min(100, score)),
        "reasons": reasons,
        "risks": risks,
    }
