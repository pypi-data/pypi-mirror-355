import aiohttp
import urllib.parse

TRACKERS = [
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:80",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://glotorrents.pw:6969/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://torrent.gresille.org:80/announce",
    "udp://p4p.arenabg.com:1337",
    "udp://tracker.leechers-paradise.org:6969",
]

def build_magnet(hash_, title):
    trackers = "&".join(f"tr={urllib.parse.quote(tr)}" for tr in TRACKERS)
    dn = urllib.parse.quote(title)
    return f"magnet:?xt=urn:btih:{hash_}&dn={dn}&{trackers}"

async def search(query, limit=30, page=1, sort_by="seeds"):
    results = []
    url = "https://yts.am/api/v2/list_movies.json"
    params = {
        "query_term": query,
        "limit": limit,
        "page": page,
        "sort_by": sort_by,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

                if data["status"] != "ok" or not data["data"].get("movies"):
                    return []

                for movie in data["data"]["movies"]:
                    for torrent in movie["torrents"]:
                        magnet = build_magnet(torrent["hash"], movie["title"])
                        results.append({
                            "title": movie["title"],
                            "magnet": magnet,
                            "size": torrent["size"],
                            "uploaded": movie["date_uploaded"],
                            "uploader": "YTS",
                            "category": "Movies",
                            "seeders": torrent["seeds"],
                            "leechers": torrent["peers"],
                            "source": "yts",
                        })
    except Exception:
        pass

    return results