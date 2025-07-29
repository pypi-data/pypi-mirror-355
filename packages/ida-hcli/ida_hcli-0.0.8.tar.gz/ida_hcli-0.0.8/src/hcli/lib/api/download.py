"""Download API client."""

from typing import Dict, List, Union

from pydantic import BaseModel

from .common import get_api_client


class DownloadResource(BaseModel):
    """Download resource information."""

    id: str
    name: str
    description: str
    category: str
    version: str
    os: str
    arch: str


class DownloadResources(BaseModel):
    """Download resources wrapper."""

    resources: List[DownloadResource]


class VirtualFileSystem:
    """Virtual file system for organizing download resources."""

    def __init__(self, resources: List[DownloadResource]):
        self.resources = resources
        self.structure: Dict[str, Dict[str, List[DownloadResource]]] = {}
        self._build_structure()

    def _build_structure(self):
        """Build the hierarchical structure from resources."""
        for resource in self.resources:
            version = resource.version
            category = resource.category

            if version not in self.structure:
                self.structure[version] = {}

            if category not in self.structure[version]:
                self.structure[version][category] = []

            self.structure[version][category].append(resource)

    def get_folders(self, path: str = "") -> List[str]:
        """Get folders at the given path."""
        parts = [p for p in path.split("/") if p]
        current_level: Union[
            Dict[str, Dict[str, List[DownloadResource]]],
            Dict[str, List[DownloadResource]],
            List[DownloadResource],
        ] = self.structure

        for part in parts:
            if isinstance(current_level, dict) and part in current_level:
                current_level = current_level[part]
            else:
                return []

        if len(parts) < 2:
            if isinstance(current_level, dict):
                return list(current_level.keys())
        return []

    def get_files(self, path: str = "") -> List[DownloadResource]:
        """Get files at the given path."""
        parts = [p for p in path.split("/") if p]
        current_level: Union[
            Dict[str, Dict[str, List[DownloadResource]]],
            Dict[str, List[DownloadResource]],
            List[DownloadResource],
        ] = self.structure

        for part in parts:
            if isinstance(current_level, dict) and part in current_level:
                current_level = current_level[part]
            else:
                return []

        if isinstance(current_level, list):
            return current_level

        return []


class DownloadAPI:
    """Download API client."""

    async def get_downloads(self) -> List[DownloadResource]:
        """Get all available downloads."""
        try:
            client = await get_api_client()
            data = await client.get_json("/api/downloads")
            download_resources = DownloadResources(**data)
            return download_resources.resources
        except Exception:
            return []

    async def get_download(self, slug: str) -> str:
        """Get download URL for a specific slug."""
        client = await get_api_client()
        return await client.get_json(f"/api/downloads/{slug}")


# Global instance
download = DownloadAPI()
