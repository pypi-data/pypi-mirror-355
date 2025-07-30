import asyncio
from torrfetch import sources
from .utils import deduplicate, rank_results

async def search_torrents(query):
    """Asynchronously search all providers and return deduplicated torrent results."""
    tasks = []

    for _, provider in sources.get_all().items():
        tasks.append(provider.search(query))  # assume provider.search is async

    all_results = await asyncio.gather(*tasks)
    flat_results = [result for sublist in all_results if sublist for result in sublist]
    results = deduplicate(flat_results)
    ranked = rank_results(query, results)
    return ranked[:30]

def search(query):
    return asyncio.run(search_torrents(query))