from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import httpx
from rich.console import Console
from rich.progress import (
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from hcli.env import ENV
from hcli.lib.auth import get_auth_service

console = Console()


class NotLoggedInError(Exception):
    """Raised when authentication is required but user is not logged in."""

    pass


class APIClient:
    """HTTP client with automatic authentication header injection."""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=ENV.HCLI_API_URL, timeout=60.0)
        self._cache_dir = Path.home() / ".hcli" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_headers(self, auth: bool = True) -> Dict[str, str]:
        """Get headers with authentication if required."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if auth:
            auth_service = get_auth_service()
            if auth_service.is_logged_in():
                auth_type = auth_service.get_auth_type()
                if auth_type["type"] == "interactive":
                    token = auth_service.get_access_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                else:
                    api_key = auth_service.get_api_key()
                    if api_key:
                        headers["x-api-key"] = api_key
            else:
                raise NotLoggedInError("Authentication required but user is not logged in")

        return headers

    async def get_json(self, url: str, auth: bool = True) -> Any:
        """GET request returning JSON."""
        headers = self._get_headers(auth)
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def post_json(self, url: str, data: Any, auth: bool = True) -> Any:
        """POST request with JSON body."""
        headers = self._get_headers(auth)
        response = await self.client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    async def delete_json(self, url: str, auth: bool = True) -> Any:
        """DELETE request returning JSON."""
        headers = self._get_headers(auth)
        response = await self.client.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def put_file(self, url: str, file_path: Union[str, Path], content: Optional[bytes] = None):
        """Upload file via PUT request."""
        file_path = Path(file_path)

        if content is None:
            content = file_path.read_bytes()

        # Determine content type
        if file_path.suffix == ".zip":
            content_type = "application/zip"
        elif file_path.suffix == ".json":
            content_type = "application/json"
        else:
            content_type = "application/octet-stream"

        headers = {"Content-Type": content_type}

        with console.status("[bold green]Uploading..."):
            response = await self.client.put(url, content=content, headers=headers)
            response.raise_for_status()

        console.print("[green]Upload complete[/green]")

    async def download_file(
        self,
        url: str,
        target_dir: Union[str, Path] = "./",
        target_filename: Optional[str] = None,
        force: bool = False,
        auth: bool = False,
    ) -> str:
        """Download file with progress bar and caching."""
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if target_filename:
            filename = target_filename
        else:
            parsed = urlparse(url)
            filename = Path(parsed.path).name or "download"

        cache_path = self._cache_dir / filename
        target_path = target_dir / filename

        # Check cache
        if cache_path.exists() and not force:
            try:
                # Check if cached file matches remote size
                headers = self._get_headers(auth) if auth else {}
                head_response = await self.client.head(url, headers=headers)
                content_length = head_response.headers.get("content-length")

                if content_length and cache_path.stat().st_size == int(content_length):
                    console.print(f"Using cached file: {cache_path}")
                    import shutil

                    shutil.copy2(cache_path, target_path)
                    return str(target_path)
            except Exception:
                # Continue with download if cache check fails
                pass

        # Download file
        headers = self._get_headers(auth) if auth else {}

        async with self.client.stream("GET", url, headers=headers) as response:
            if response.status_code == 404:
                console.print(f"[red]Error: File not found (404): {url}[/red]")
                raise httpx.HTTPStatusError(f"404 Not Found: {url}", request=response.request, response=response)

            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with Progress(
                "[progress.description]{task.description}",
                "[progress.percentage]{task.percentage:>3.0f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                download_task = progress.add_task(
                    f"Downloading {filename}",
                    total=total_size if total_size > 0 else None,
                )

                # Write to cache first
                with open(cache_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        if total_size > 0:
                            progress.update(download_task, advance=len(chunk))

        # Copy from cache to target
        import shutil

        shutil.copy2(cache_path, target_path)

        return str(target_path)


# Global API client instance
_api_client: Optional[APIClient] = None


async def get_api_client() -> APIClient:
    """Get or create the global API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
