from typing import Any

from fastmcp import FastMCP

from .wrapper import Torrent, YggTorrentApi

mcp: FastMCP[Any] = FastMCP(
    "YggTorrent Server",
    instructions="This server provides tools for interacting with the Ygg Torrent API.",
)
ygg_api = YggTorrentApi()


@mcp.resource("data://torrent_categories")
def torrent_categories() -> list[str]:
    """Get a list of available torrent categories."""
    return ygg_api.get_torrent_categories()


@mcp.tool()
def search_torrents(
    query: str,
    categories: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
    order_by: str = "seeders",
    limit: int | None = None,
) -> list[Torrent]:
    """Search for torrent files."""
    return (ygg_api.search_torrents(query, categories, page, per_page, order_by) or [])[
        : limit or per_page
    ]


@mcp.tool()
def get_torrent_details(
    torrent_id: int,
    with_magnet_link: bool = False,
) -> Torrent | None:
    """Get details about a specific torrent."""
    return ygg_api.get_torrent_details(torrent_id, with_magnet_link)


@mcp.tool()
def get_magnet_link(torrent_id: int) -> str | None:
    """Get the magnet link for a specific torrent."""
    return ygg_api.get_magnet_link(torrent_id)


@mcp.tool()
def download_torrent_file(
    torrent_id: int,
    output_dir: str,
) -> str | None:
    """Download the torrent file."""
    return ygg_api.download_torrent_file(torrent_id, output_dir)
