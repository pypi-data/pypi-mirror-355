import re
from difflib import SequenceMatcher

def normalize_title(title):
    return re.sub(r'[^a-zA-Z0-9]', '', title.lower())

def title_similarity(query, title):
    return SequenceMatcher(None, normalize_title(query), normalize_title(title)).ratio()

def deduplicate(torrents):
    seen = {}
    for t in torrents:
        key = normalize_title(t["title"])
        if key not in seen or t["seeders"] > seen[key]["seeders"]:
            seen[key] = t
    return list(seen.values())

def rank_results(query, deduped_results):
    for t in deduped_results:
        relevance = title_similarity(query, t["title"])
        seeders = t.get("seeders", 0)
        t["_score"] = relevance * 0.7 + (min(seeders, 1000) / 1000) * 0.3  # 70% relevance, 30% seeders
    return sorted(deduped_results, key=lambda x: x["_score"], reverse=True)
