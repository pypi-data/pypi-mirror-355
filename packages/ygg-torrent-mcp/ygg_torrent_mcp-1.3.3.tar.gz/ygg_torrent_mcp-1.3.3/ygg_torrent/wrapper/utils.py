from datetime import datetime
from math import floor, log
from math import pow as pw
from typing import Any

from .categories import get_category_id, get_category_name
from .models import Torrent


def format_size(size_bytes: int | None) -> str:
    """Converts a size in bytes to a human-readable string."""
    if size_bytes is None:
        return "N/A"
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pw(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def format_date(date_str: str | None) -> str:
    """Converts an ISO date string to a human-readable string 'YYYY-MM-DD HH:MM:SS' or 'N/A' if input is None."""
    if date_str is None:
        return "N/A"
    return datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M:%S")


def format_torrent(torrent: dict[str, Any], torrent_id: int | None = None) -> Torrent:
    """Converts a torrent data dictionary from the API into a Torrent model instance."""
    cat_id: int | str = torrent.get("category_id") or "N/A"
    return Torrent(
        id=torrent_id or torrent.get("id") or 0,
        filename=torrent.get("title") or "N/A",
        category=(
            get_category_name(cat_id) or str(cat_id)
            if isinstance(cat_id, int)
            else str(cat_id)
        ),
        size=format_size(torrent.get("size")),
        seeders=torrent.get("seeders") or 0,
        leechers=torrent.get("leechers") or 0,
        downloads=torrent.get("downloads") or 0,
        date=format_date(torrent.get("uploaded_at")),
        magnet_link=None,
    )


def check_categories(categories: list[int] | list[str] | None = None) -> list[int]:
    """Checks if the categories are valid."""
    processed_category_ids: list[int] = []
    if categories:
        if all(isinstance(cat, int) for cat in categories):
            processed_category_ids = list(set(categories))  # type: ignore
        elif all(isinstance(cat, str) for cat in categories):
            temp_ids: list[int] = []
            for keyword_val in categories:
                cat_id = get_category_id(str(keyword_val).lower())
                if cat_id is not None:
                    temp_ids.append(cat_id)
            if temp_ids:
                processed_category_ids = list(set(temp_ids))
            if not processed_category_ids:
                print(
                    f"Warning: None of the provided category keywords matched: {categories}."
                    " Proceeding without category filter."
                )
    return processed_category_ids
