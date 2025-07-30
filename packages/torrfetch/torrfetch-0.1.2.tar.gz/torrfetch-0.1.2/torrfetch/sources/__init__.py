from torrfetch.sources import pirate_bay, yts

def get_all():
    return {
        "piratebay": pirate_bay,
        "yts": yts,
    }
