import shutil
import tempfile
from pathlib import Path as PathLibPath

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .wrapper import Torrent, YggTorrentApi

app = FastAPI(
    title="Ygg Torrent FastAPI",
    description="FastAPI server for Ygg Torrent API.",
)

api_client = YggTorrentApi()


def cleanup_temp_dir(dir_path: str) -> None:
    """Safely removes a directory and its contents."""
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print(f"Error removing temporary directory {dir_path}: {e}")


# --- API Endpoints ---
@app.get("/", summary="Health Check", tags=["General"], response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """
    Endpoint to check the health of the service.
    """
    return {"status": "ok"}


@app.get(
    "/torrents/categories",
    summary="Get Torrent Categories",
    tags=["Torrents"],
    response_model=list[str],
)
async def get_torrent_categories() -> list[str]:
    """
    Get a list of available torrent categories.
    Corresponds to `YggTorrentApi.get_torrent_categories()`.
    """
    return api_client.get_torrent_categories()


@app.post(
    "/torrents/search",
    summary="Search Torrents",
    tags=["Torrents"],
    response_model=list[Torrent],
)
async def search_torrents(
    query: str,
    categories: list[str] | None = None,
    page: int = 1,
    per_page: int = 25,
    order_by: str = "seeders",
) -> list[Torrent]:
    """
    Search for torrents on YggTorrent.
    Corresponds to `YggTorrentApi.search_torrents()`.
    """
    return api_client.search_torrents(
        query=query,
        categories=categories,
        page=page,
        per_page=per_page,
        order_by=order_by,
    )


@app.get(
    "/torrents/{torrent_id}",
    summary="Get Torrent Details",
    tags=["Torrents"],
    response_model=Torrent,
)
async def get_torrent_details(
    torrent_id: int = Path(..., ge=1, description="The ID of the torrent."),
    with_magnet_link: bool = Query(
        False, description="Include magnet link in the response."
    ),
) -> Torrent:
    """
    Get details for a specific torrent.
    Corresponds to `YggTorrentApi.get_torrent_details()`.
    """
    torrent = api_client.get_torrent_details(
        torrent_id, with_magnet_link=with_magnet_link
    )
    if not torrent:
        raise HTTPException(
            status_code=404, detail=f"Torrent with ID {torrent_id} not found."
        )
    return torrent


@app.get(
    "/torrents/{torrent_id}/magnet",
    summary="Get Magnet Link",
    tags=["Torrents"],
    response_model=str,
)
async def get_magnet_link(
    torrent_id: int = Path(..., ge=1, description="The ID of the torrent."),
) -> str:
    """
    Get the magnet link for a specific torrent.
    Corresponds to `YggTorrentApi.get_magnet_link()`.
    """
    magnet_link = api_client.get_magnet_link(torrent_id)
    if not magnet_link:
        raise HTTPException(
            status_code=404, detail="Magnet link not found or could not be generated."
        )
    return magnet_link


@app.get(
    "/torrents/{torrent_id}/download",
    summary="Download .torrent File",
    tags=["Torrents"],
    response_class=FileResponse,
)
async def download_torrent_file(
    torrent_id: int = Path(..., ge=1, description="The ID of the torrent."),
) -> FileResponse:
    """
    Download the .torrent file for a specific torrent.
    Corresponds to `YggTorrentApi.download_torrent_file()`.
    The file is downloaded to a temporary location on the server and then streamed.
    The temporary file is cleaned up afterwards.
    """
    temp_dir_path = None
    try:
        temp_dir_path = tempfile.mkdtemp()
        downloaded_filename = api_client.download_torrent_file(
            torrent_id=torrent_id, output_dir=temp_dir_path
        )

        if not downloaded_filename:
            if temp_dir_path:
                cleanup_temp_dir(temp_dir_path)
            raise HTTPException(
                status_code=404, detail="Torrent file not found or download failed."
            )

        full_file_path = PathLibPath(temp_dir_path) / downloaded_filename
        if not full_file_path.is_file():
            if temp_dir_path:
                cleanup_temp_dir(temp_dir_path)
            raise HTTPException(
                status_code=500,
                detail="Torrent file was not saved correctly on server.",
            )

        return FileResponse(
            path=str(full_file_path),
            media_type="application/x-bittorrent",
            filename=downloaded_filename,
            background=BackgroundTask(cleanup_temp_dir, temp_dir_path),
        )
    except Exception as e:
        if temp_dir_path:
            cleanup_temp_dir(temp_dir_path)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the torrent download: {str(e)}",
        ) from e
