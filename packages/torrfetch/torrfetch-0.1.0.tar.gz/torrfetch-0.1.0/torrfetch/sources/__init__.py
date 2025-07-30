from torrfetch.sources import pirate_bay, yts

def get_all():
    return {
        "pirate_bay": pirate_bay,
        "yts": yts,
    }
