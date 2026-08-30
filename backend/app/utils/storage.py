"""Local filesystem storage abstraction (S3-compatible interface)."""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from app.config import settings


class LocalStorage:
    """Stores uploaded files in a local directory.

    Designed so it can be swapped for an S3/R2 implementation with the same
    `save`, `open`, `delete`, `exists` methods.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, project_id: str | uuid.UUID, vendor_id: str | uuid.UUID, filename: str) -> str:
        safe = filename.replace("..", "_").replace("/", "_")
        folder = self.base_dir / f"projects/{project_id}/{vendor_id}"
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder / f"{uuid.uuid4().hex}_{safe}")

    def save(self, project_id: str, vendor_id: str, filename: str, source: BinaryIO) -> tuple[str, int]:
        path = self.path_for(project_id, vendor_id, filename)
        size = 0
        with open(path, "wb") as out:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                size += len(chunk)
        return path, size

    def save_bytes(self, project_id: str, vendor_id: str, filename: str, data: bytes) -> tuple[str, int]:
        path = self.path_for(project_id, vendor_id, filename)
        with open(path, "wb") as out:
            out.write(data)
        return path, len(data)

    def delete(self, path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def open(self, path: str) -> BinaryIO:
        return open(path, "rb")


def get_storage() -> LocalStorage:
    return LocalStorage()
