"""Local folder artifact service implementation for Google ADK."""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import Optional

from google.adk.artifacts import BaseArtifactService
from google.genai import types
from typing_extensions import override

logger = logging.getLogger("adk_extra_services.artifacts.local_folder")


class LocalFolderArtifactService(BaseArtifactService):
    """Stores artifacts in the local filesystem."""

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path).expanduser().resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _file_has_user_namespace(self, filename: str) -> bool:
        return filename.startswith("user:")

    def _get_file_path(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        filename: str,
        version: int,
    ) -> Path:
        if self._file_has_user_namespace(filename):
            parts = [app_name, user_id, "user", filename, str(version)]
        else:
            parts = [app_name, user_id, session_id, filename, str(version)]
        return self.base_path.joinpath(*parts)

    @override
    async def save_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        filename: str,
        artifact: types.Part,
    ) -> int:
        versions = await self.list_versions(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            filename=filename,
        )
        version = 0 if not versions else max(versions) + 1

        path = self._get_file_path(app_name, user_id, session_id, filename, version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifact.inline_data.data)
        return version

    @override
    async def load_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        filename: str,
        version: Optional[int] = None,
    ) -> Optional[types.Part]:
        if version is None:
            versions = await self.list_versions(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                filename=filename,
            )
            if not versions:
                return None
            version = max(versions)

        path = self._get_file_path(app_name, user_id, session_id, filename, version)
        if not path.exists():
            return None

        data = path.read_bytes()
        mime, _ = mimetypes.guess_type(filename)
        if mime is None:
            mime = "text/plain"
        return types.Part.from_bytes(data=data, mime_type=mime)

    @override
    async def list_artifact_keys(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> list[str]:
        keys: set[str] = set()
        session_dir = self.base_path / app_name / user_id / session_id
        if session_dir.exists():
            for filename_dir in session_dir.iterdir():
                if filename_dir.is_dir():
                    keys.add(filename_dir.name)

        user_dir = self.base_path / app_name / user_id / "user"
        if user_dir.exists():
            for filename_dir in user_dir.iterdir():
                if filename_dir.is_dir():
                    keys.add(filename_dir.name)

        return sorted(keys)

    @override
    async def delete_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        filename: str,
    ) -> None:
        versions = await self.list_versions(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            filename=filename,
        )
        for ver in versions:
            path = self._get_file_path(app_name, user_id, session_id, filename, ver)
            if path.exists():
                try:
                    path.unlink()
                except OSError as exc:
                    logger.warning("Failed to delete %s: %s", path, exc)

    @override
    async def list_versions(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        filename: str,
    ) -> list[int]:
        if self._file_has_user_namespace(filename):
            dir_path = self.base_path / app_name / user_id / "user" / filename
        else:
            dir_path = self.base_path / app_name / user_id / session_id / filename
        if not dir_path.exists():
            return []
        versions: list[int] = []
        for item in dir_path.iterdir():
            if item.is_file():
                try:
                    versions.append(int(item.name))
                except ValueError:
                    continue
        return sorted(versions)
