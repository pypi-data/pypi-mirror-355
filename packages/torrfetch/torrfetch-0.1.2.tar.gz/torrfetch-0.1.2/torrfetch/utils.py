import re
from rapidfuzz.fuzz import token_sort_ratio

def normalize_title(title):
    return re.sub(r'[^a-zA-Z0-9]', ' ', title.lower())

def score(result, query):
    base_score = token_sort_ratio(result["title"], query)

    seed_score = min(result["seeders"], 1000) / 10

    exact_match_bonus = 50 if result["title"].lower() == query.lower() else 0

    penalty = -50 if base_score < 70 else 0

    return base_score + seed_score + exact_match_bonus + penalty

def deduplicate(torrents):
    seen = {}
    for t in torrents:
        key = normalize_title(t["title"])
        if key not in seen or t["seeders"] > seen[key]["seeders"]:
            seen[key] = t
    return list(seen.values())

def rank_results(query, results):
    for r in results:
        r["_score"] = score(r, query)
    return sorted(results, key=lambda x: x["_score"], reverse=True)
