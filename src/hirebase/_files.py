"""Helpers for multipart file uploads."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union

FileInput = Union[str, Path, bytes, BinaryIO, Tuple[str, Any, Optional[str]]]

_ALLOWED_RESUME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/html",
}


def prepare_upload_file(file: FileInput) -> Dict[str, Tuple[str, Any, str]]:
    """Return a ``files`` dict suitable for requests/httpx multipart uploads."""
    if isinstance(file, tuple):
        if len(file) == 3:
            name, data, content_type = file
        elif len(file) == 2:
            name, data = file  # type: ignore[misc]
            content_type = None
        else:
            raise ValueError("file tuple must be (filename, data) or (filename, data, type)")
        ctype = content_type or _guess_type(name)
        return {"file": (name, data, ctype)}

    if isinstance(file, (str, Path)):
        path = Path(file)
        ctype = _guess_type(path.name)
        return {"file": (path.name, open(path, "rb"), ctype)}

    if isinstance(file, bytes):
        return {"file": ("resume.pdf", file, "application/pdf")}

    if hasattr(file, "read"):
        name = Path(getattr(file, "name", "resume.pdf")).name
        ctype = _guess_type(name)
        return {"file": (name, file, ctype)}

    raise TypeError(
        "file must be a path, bytes, a file-like object, or (filename, data[, type])"
    )


def _guess_type(filename: str) -> str:
    ctype, _ = mimetypes.guess_type(filename)
    return ctype or "application/octet-stream"
