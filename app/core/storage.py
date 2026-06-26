import os
import tempfile
import mimetypes
from pathlib import Path
from urllib.parse import unquote
from genblaze_core import ObjectStorageSink, KeyStrategy
from genblaze_core.storage import StorageBackend
from genblaze_s3 import S3StorageBackend

# ── Windows file:// patch ────────────────────────────────────────────────────
# Genblaze generates file://C:\path URLs on Windows which urlparse misreads.
# We patch _read_local_file in the transfer module to handle this correctly.
import genblaze_core.storage.transfer as _transfer

_tmp = Path(tempfile.gettempdir()).resolve()

def _patched_read_local_file(url, *, extra_roots=None):
    decoded_url = unquote(url)
    if decoded_url.startswith("file://"):
        path_str = decoded_url[7:]
        if (
            path_str.startswith('/')
            and len(path_str) > 2
            and path_str[1:3] in [c + ':' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
        ):
            path_str = path_str[1:]
    else:
        path_str = decoded_url

    resolved = Path(path_str).resolve()
    allowed = list(_transfer.ALLOWED_FILE_ROOTS)
    if extra_roots:
        allowed.extend(r.resolve() for r in extra_roots)
    if not any(resolved.is_relative_to(root) for root in allowed):
        raise _transfer.StorageError(
            f"Access denied: local file path {resolved} is outside allowed directories."
        )
    try:
        data = resolved.read_bytes()
    except Exception as exc:
        raise _transfer.StorageError(
            f"Failed to read local file {path_str}: {exc}"
        ) from exc
    content_type, _ = mimetypes.guess_type(str(resolved))
    return data, content_type

_transfer._read_local_file = _patched_read_local_file
_transfer.ALLOWED_FILE_ROOTS = (_tmp,)
# ── End patch ────────────────────────────────────────────────────────────────

from app.core.config import settings


def get_b2_backend() -> S3StorageBackend:
    return S3StorageBackend(
        settings.b2_bucket_name,
        endpoint_url=f"https://{settings.b2_endpoint}",
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_application_key,
        region="us-east-005",
    )


def get_b2_sink() -> ObjectStorageSink:
    return ObjectStorageSink(
        get_b2_backend(),
        key_strategy=KeyStrategy.HIERARCHICAL,
        prefix="narrateflow",
    )


def get_output_dir(job_id: str) -> Path:
    """Returns a temp-based output directory for a job."""
    output_dir = _tmp / "narrateflow" / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir