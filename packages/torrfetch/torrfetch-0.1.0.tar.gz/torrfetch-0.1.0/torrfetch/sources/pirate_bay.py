import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://tpirbay.xyz"

async def search(query):
    results = []
    search_url = f"{BASE_URL}/search/{query.replace(' ', '%20')}/1/7/0"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                for row in soup.select("table#searchResult tr"):
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue

                    title_tag = cols[1].find("a", class_="detLink")
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()

                    magnet_tag = cols[1].find("a", href=lambda h: h and h.startswith("magnet:?"))
                    magnet = magnet_tag["href"] if magnet_tag else None

                    seeders = int(cols[2].text.strip())
                    leechers = int(cols[3].text.strip())

                    desc_tag = cols[1].find("font", class_="detDesc")
                    size = uploaded = uploader = "Unknown"
                    if desc_tag:
                        desc = desc_tag.text
                        if "Uploaded" in desc and "Size" in desc:
                            parts = desc.split(",")
                            uploaded = parts[0].replace("Uploaded", "").replace("\xa0", " ").strip()
                            size = parts[1].replace("Size", "").replace("\xa0", " ").strip()
                        if "ULed by" in desc:
                            uploader = desc.split("ULed by")[1].strip()

                    category_tag = cols[0].find("a")
                    category = category_tag.text if category_tag else "Unknown"

                    results.append({
                        "title": title,
                        "magnet": magnet,
                        "size": size,
                        "uploaded": uploaded,
                        "uploader": uploader,
                        "category": category,
                        "seeders": seeders,
                        "leechers": leechers,
                        "source": "piratebay",
                    })
    except Exception:
        pass

    return results