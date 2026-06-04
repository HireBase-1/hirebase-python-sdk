"""Memory-efficient streaming of exported job files.

Hirebase JSON exports are written as JSON Lines (one job object per line),
which streams trivially. For robustness we also transparently handle a single
top-level JSON array using ``ijson`` (an optional dependency) so we never load
a multi-GB export fully into memory.

CSV exports are streamed row-by-row with the stdlib ``csv`` module.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterator, Optional, Type, Union

from .models.jobs import Job

# Raise CSV field-size limit so very long serialized cells (e.g. descriptions)
# don't blow up DictReader.
csv.field_size_limit(min(2**31 - 1, 10 * 1024 * 1024))


def _detect_format(path: str, fmt: Optional[str]) -> str:
    if fmt:
        return fmt.lower().lstrip(".")
    lower = path.lower()
    if lower.endswith(".csv"):
        return "csv"
    return "json"


def _coerce_record(record: dict, return_type: Optional[Type]) -> Union[Job, dict]:
    if return_type is dict:
        return record
    return Job.model_validate(record)


def _iter_json_bytes(stream: io.BufferedReader) -> Iterator[dict]:
    """Yield dict records from a binary stream of either JSONL or a JSON array."""
    first = _peek_first_nonspace(stream)
    if first == b"[":
        yield from _iter_json_array(stream)
    else:
        yield from _iter_jsonl(stream)


def _peek_first_nonspace(stream: io.BufferedReader) -> bytes:
    pos = stream.tell()
    try:
        while True:
            chunk = stream.read(1)
            if not chunk:
                return b""
            if not chunk.isspace():
                return chunk
    finally:
        stream.seek(pos)


def _iter_json_array(stream: io.BufferedReader) -> Iterator[dict]:
    try:
        import ijson  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dep
        raise RuntimeError(
            "The export file is a JSON array; install the optional 'ijson' "
            "dependency (pip install hirebase[streaming]) to stream it, or "
            "convert it to JSON Lines."
        ) from exc
    for item in ijson.items(stream, "item"):
        yield item


def _iter_jsonl(stream: io.BufferedReader) -> Iterator[dict]:
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        yield json.loads(line)


def stream_jobs_file(
    path: str,
    return_type: Optional[Type] = None,
    fmt: Optional[str] = None,
) -> Iterator[Union[Job, dict]]:
    """Stream jobs from a local export file.

    Args:
        path: Path to a ``.json`` (JSON Lines or array) or ``.csv`` export.
        return_type: ``dict`` to yield raw dicts, otherwise typed ``Job``
            objects (the default).
        fmt: Override the format detection ("json" or "csv").

    Yields:
        ``Job`` objects (default) or ``dict`` rows.
    """
    detected = _detect_format(path, fmt)
    if detected == "csv":
        with open(path, "r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                yield _coerce_csv_row(row, return_type)
    else:
        with open(path, "rb") as handle:
            for record in _iter_json_bytes(handle):
                yield _coerce_record(record, return_type)


def _coerce_csv_row(row: dict, return_type: Optional[Type]) -> Union[Job, dict]:
    if return_type is dict:
        return row
    # CSV cells are strings; some hold JSON (lists/objects). Best-effort decode
    # so the resulting Job is as faithful as possible.
    decoded = {}
    for key, value in row.items():
        if value is None or value == "":
            decoded[key] = None
            continue
        stripped = value.strip()
        if stripped and stripped[0] in "[{":
            try:
                decoded[key] = json.loads(stripped)
                continue
            except (ValueError, TypeError):
                pass
        decoded[key] = value
    return Job.model_validate(decoded)


def iter_jsonl_lines(
    lines: Iterator[bytes],
    return_type: Optional[Type] = None,
) -> Iterator[Union[Job, dict]]:
    """Coerce an iterator of raw JSONL byte lines into records.

    Used by the clients to stream jobs directly from an HTTP response without
    buffering the whole body.
    """
    for raw in lines:
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        line = raw.strip()
        if not line:
            continue
        record = json.loads(line)
        yield _coerce_record(record, return_type)
