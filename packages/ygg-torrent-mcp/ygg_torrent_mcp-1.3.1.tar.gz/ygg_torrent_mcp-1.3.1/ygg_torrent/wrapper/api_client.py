from pathlib import Path
from sys import argv
from typing import Any

from requests import Session, exceptions  # type: ignore

from .categories import get_categories
from .models import Torrent
from .torrent_editor import (
    DUMMY_PASSKEY,
    edit_torrent_bytes,
    make_magnet_from_torrent_bytes,
)
from .utils import check_categories, format_torrent


class YggTorrentApi:
    """A client for interacting with the Ygg Torrent API."""

    def __init__(self) -> None:
        """
        Initializes the API client.
        """
        self.base_url = "https://yggapi.eu/"
        self.session = Session()  # type: ignore

    def get_torrent_categories(self) -> list[str]:
        """
        Get a list of available torrent categories.

        Returns:
            A list of category names.
        """
        return get_categories()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Makes an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: URL query parameters.
            json_data: JSON body for POST/PUT requests.
            **kwargs: Additional arguments for request.

        Returns:
            The JSON response from the API or bytes for file downloads.

        Raises:
            exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        url = f"{self.base_url}{endpoint.lstrip('/')}"
        try:
            response = self.session.request(
                method, url, params=params, json=json_data, **kwargs
            )  # type: ignore
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            elif response.content:
                return response.content
            return None
        except exceptions.RequestException as e:
            print(f"Request to {url} failed: {e}")
            return None

    def search_torrents(
        self,
        query: str,
        categories: list[int] | list[str] | None = None,
        page: int = 1,
        per_page: int = 25,
        order_by: str = "seeders",
    ) -> list[Torrent]:
        """
        Get a list of torrents.
        Corresponds to GET /torrents

        Args:
            query: Search query.
            categories: Optional list of category IDs (int) or keywords (str).
            page: Page number.
            per_page: Number of results per page (25, 50, 100).
            order_by: Field to order by (descending). Valid values: uploaded_at, seeders, downloads.

        Returns:
            A list of torrent results or an error dictionary.

        Raises:
            TypeError: If 'categories' is a mixed list of integers and strings,
                       or contains types other than int or str.
        """
        params = {"q": query, "page": page, "per_page": per_page, "order_by": order_by}

        processed_category_ids: list[int] = (
            check_categories(categories) if categories else []
        )
        if processed_category_ids:
            params["category_id"] = processed_category_ids

        torrents = self._request("GET", "torrents", params=params)
        if torrents:
            return [format_torrent(torrent) for torrent in torrents]
        return []

    def get_torrent_details(
        self, torrent_id: int, with_magnet_link: bool = False
    ) -> Torrent | None:
        """
        Get details about a specific torrent.
        Corresponds to GET /torrent/{torrent_id}

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            Detailed torrent result.
        """
        if torrent_id < 1:
            print("torrent_id must be >= 1")
            return None
        resp = self._request("GET", f"torrent/{torrent_id}")
        if not resp:
            print("Failed to get torrent details")
            return None
        torrent = format_torrent(resp, torrent_id)
        if with_magnet_link:
            torrent.magnet_link = self.get_magnet_link(torrent_id)
        return torrent

    def _download_torrent_file_bytes(
        self, torrent_id: int
    ) -> bytes | dict[str, Any] | None:
        """
        Download the .torrent file.
        Corresponds to GET /torrent/{torrent_id}/download

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent file content as bytes or an error dictionary.
        """
        if torrent_id < 1:
            print("torrent_id must be >= 1")
            return None
        params = {
            "passkey": DUMMY_PASSKEY,
            "tracker_domain": "tracker.p2p-world.net",  # will also add "connect.maxp2p.org" later
        }
        return self._request("GET", f"torrent/{torrent_id}/download", params=params)  # type: ignore

    def get_magnet_link(self, torrent_id: int) -> str | None:
        """
        Get the magnet link for a specific torrent.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The magnet link as a string or None.
        """
        try:
            file_bytes = self._download_torrent_file_bytes(torrent_id)
            if file_bytes and isinstance(file_bytes, bytes):
                return make_magnet_from_torrent_bytes(file_bytes)
        except Exception as e:
            print(f"Failed to generate magnet link: {e}")
        return None

    def download_torrent_file(
        self, torrent_id: int, output_dir: str | Path = "."
    ) -> str | None:
        """
        Download the .torrent file.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The filename of the downloaded .torrent file or None.
        """
        try:
            file_bytes = self._download_torrent_file_bytes(torrent_id)
            if file_bytes and isinstance(file_bytes, bytes):
                file_bytes = edit_torrent_bytes(file_bytes)
                filename = f"{torrent_id}.torrent"
                with open(Path(output_dir) / filename, "wb") as f:
                    f.write(file_bytes)
                return filename
        except Exception as e:
            print(f"Error: {e}")
        print("Failed to download torrent file")
        return None


if __name__ == "__main__":
    QUERY = argv[1] if len(argv) > 1 else None
    if not QUERY:
        print("Please provide a search query.")
        exit(1)
    CATEGORIES = argv[2].split(",") if len(argv) > 2 else None
    client = YggTorrentApi()
    found_torrents: list[Torrent] = client.search_torrents(QUERY, CATEGORIES)
    if found_torrents and found_torrents[0].id:
        print(client.get_torrent_details(found_torrents[0].id, with_magnet_link=True))
    else:
        print("No torrents found")
