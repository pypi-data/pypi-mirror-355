CATEGORY_BY_NAME: dict[str, int] = {
    "karaoke": 2147,
    "music": 2148,
    "samples": 2149,
    "podcast radio": 2150,
    "audio book": 2151,
    "bds": 2152,
    "comics": 2153,
    "book": 2154,
    "manga": 2155,
    "press": 2156,
    "emulator": 2157,
    "rom": 2158,
    "game linux": 2159,
    "game macos": 2160,
    "game windows": 2161,
    "game microsoft": 2162,
    "game nintendo": 2163,
    "game sony": 2164,
    "game smartphone": 2165,
    "game tablette": 2166,
    "game other": 2167,
    "gps application": 2168,
    "gps map": 2169,
    "gps various": 2170,
    "app linux": 2171,
    "app macos": 2172,
    "app windows": 2173,
    "app smartphone": 2174,
    "app tablette": 2175,
    "app training": 2176,
    "app other": 2177,
    "anime movie": 2178,
    "anime serie": 2179,
    "concert": 2180,
    "documentary": 2181,
    "tv show": 2182,
    "movie": 2183,
    "tv serie": 2184,
    "spectacle": 2185,
    "sport": 2186,
    "video clip": 2187,
    "xxx film": 2189,
    "xxx hentai": 2190,
    "xxx image": 2191,
    "3d object": 2201,
    "3d character": 2202,
    "wordpress": 2301,
    "scripts php cms": 2302,
    "mobile": 2303,
    "various": 2304,
    "xxx ebook": 2401,
    "xxx game": 2402,
}

CATEGORY_BY_ID: dict[int, str] = {v: k for k, v in CATEGORY_BY_NAME.items()}


def get_categories() -> list[str]:
    return list(CATEGORY_BY_NAME.keys())


def get_category_ids() -> list[int]:
    return list(CATEGORY_BY_NAME.values())


def get_category_id(category: str) -> int | None:
    return CATEGORY_BY_NAME.get(category)


def get_category_name(category_id: int) -> str | None:
    return CATEGORY_BY_ID.get(category_id)
