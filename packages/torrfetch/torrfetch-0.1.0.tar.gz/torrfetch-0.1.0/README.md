# torrfetch

**torrfetch** is a Python package that lets you search torrents across multiple public torrent indexers with deduplication and relevance sorting. Designed for developers building CLI tools or automation scripts around torrent discovery.

## Features

- Search multiple torrent providers in parallel  
- Automatic deduplication of results  
- Smart sorting by relevance and seeders  
- Fast and extensible provider interface  

## Providers

**Currently supports:**
- The Pirate Bay
- yts

## Installation

```bash
pip install torrfetch
```

## Usage

```bash
from torrfetch import search

results = search("oppenheimer 2023 1080p")
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