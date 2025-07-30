import asyncio
from torrfetch import sources
from .utils import deduplicate, rank_results

async def search_torrents_async(query, mode="parallel", only=None):
    all_providers = sources.get_all()

    if only:
        providers = {name: all_providers[name] for name in only if name in all_providers}
    else:
        providers = all_providers

    if not providers:
        raise ValueError("No valid providers available for search.")


    if mode == "parallel":
        tasks = [provider.search(query) for provider in providers.values()]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        flat_results = []
        for res in all_results:
            if isinstance(res, Exception):
                continue
            if res:
                flat_results.extend(res)

    elif mode == "fallback":
        flat_results = []
        for name, provider in providers.items():
            try:
                results = await provider.search(query)
                if results:
                    flat_results = results
                    break
            except Exception:
                continue
    else:
        raise ValueError(f"Unknown search mode: {mode}")


    if len(providers) == 1:
        return flat_results[:30]

    results = deduplicate(flat_results)
    ranked = rank_results(query, results)
    return ranked[:30]

def search_torrents(query, mode="parallel", only=None):
    return asyncio.run(search_torrents(query, mode, only))