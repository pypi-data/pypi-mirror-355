"""File sharing API client."""

import hashlib
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from .common import get_api_client


class SharedFile(BaseModel):
    """Shared file information."""

    email: Optional[str] = None
    name: str
    size: int
    code: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    url: Optional[str] = None
    acl_type: Optional[str] = None
    version: Optional[int]


class Paged(BaseModel):
    """Paged response wrapper."""

    offset: int
    limit: int
    total: int
    items: List[SharedFile]


class PagingFilter(BaseModel):
    """Paging filter parameters."""

    limit: Optional[int] = 1000
    offset: Optional[int] = 0


class UploadResponse(BaseModel):
    """Upload response."""

    code: str
    url: str
    download_url: str


class ShareAPI:
    """File sharing API client."""

    async def upload_file(
        self,
        file_path: str,
        acl_type: str = "authenticated",
        force: bool = False,
        code: Optional[str] = None,
    ) -> UploadResponse:
        """Upload a file for sharing."""
        file_path_obj = Path(file_path)
        filename = file_path_obj.name
        size = file_path_obj.stat().st_size

        # Calculate SHA-256 checksum
        content = file_path_obj.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()

        client = await get_api_client()

        # Request upload URL
        upload_data = {
            "filename": filename,
            "size": size,
            "force": force,
            "acl_type": acl_type,
            "checksum": checksum,
        }

        if code:
            upload_data["code"] = code

        response = await client.post_json("/api/share/upload", upload_data)
        upload_url = response.get("url")
        file_code = response.get("code")

        if upload_url:
            # Upload the file
            await client.put_file(upload_url, file_path_obj, content)
            # Confirm upload
            await client.post_json(f"/api/share/upload/{file_code}", {})

        from hcli.env import ENV

        return UploadResponse(
            code=file_code,
            url=f"{ENV.HCLI_PORTAL_URL}/share/{file_code}",
            download_url=f"{ENV.HCLI_API_URL}/api/share/{file_code}/download",
        )

    async def delete_file(self, code: str) -> None:
        """Delete a shared file."""
        client = await get_api_client()
        await client.delete_json(f"/api/share/{code}")

    async def get_file(self, code: str, version: int = -1) -> SharedFile:
        """Get information about a shared file."""
        client = await get_api_client()
        data = await client.get_json(f"/api/share/{code}/{version}")
        return SharedFile(**data)

    async def get_file_versions(self, code: str) -> SharedFile:
        """Get all versions of a shared file."""
        client = await get_api_client()
        data = await client.get_json(f"/api/share/{code}/versions")
        return SharedFile(**data)

    async def get_files(self, filter_params: Optional[PagingFilter] = None) -> Paged:
        """Get all shared files for the current user."""
        if filter_params is None:
            filter_params = PagingFilter()

        client = await get_api_client()
        data = await client.get_json(f"/api/share?limit={filter_params.limit}&offset={filter_params.offset}")
        return Paged(**data)


# Global instance
share = ShareAPI()
