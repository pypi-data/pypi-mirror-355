# torrfetch

**torrfetch** is a Python package that lets you search torrents across multiple public torrent indexers with deduplication and relevance sorting. Designed for developers building CLI tools or automation scripts around torrent discovery.

## Features

- Search multiple torrent providers in parallel or fallback mode  
- Automatic deduplication of results  
- Smart scoring by title relevance and seeders  
- Fast and extensible provider interface   

## Providers

Currently supports:
- The Pirate Bay
- yts

## Installation

```bash
pip install torrfetch
```

## Usage

### Parallel mode (default)
All providers are queried simultaneously, and the output is ranked by relevance and seeders
```python
torrfetch.search("oppenheimer 2023 1080p", mode="parallel")
```

### Fallback mode
Queries providers one by one, proceeding to the next if the current one is down or returns no results
```python
torrfetch.search("oppenheimer", mode="fallback")
```

### Restrict to specific providers
Use `only` to limit the search to a subset of sources (e.g., just YTS or YTS and Piratebay):
```python
torrfetch.search("oppenheimer", only=["yts"])
```

## Sample data returned
The first 30 results are returned, sorted by a combination of relevance and seeders:
```
[
  {
    "title": "Interstellar (2014)",
    "magnet": "magnet:?xt=urn:btih:...",
    "size": "2.2 GB",
    "uploaded": "2020-10-01",
    "uploader": "YTS",
    "category": "Movies",
    "seeders": 2145,
    "leechers": 198,
    "source": "yts"
  },
  {
    "title": "Interstellar.2014.1080p.BluRay.x264",
    "magnet": "magnet:?xt=urn:btih:...",
    "size": "3.1 GB",
    "uploaded": "2019-07-12",
    "uploader": "1337xUploader",
    "category": "Movies",
    "seeders": 1200,
    "leechers": 230,
    "source": "1337x"
  },
  ...
]
```