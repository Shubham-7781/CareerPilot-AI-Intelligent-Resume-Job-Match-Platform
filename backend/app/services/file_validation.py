import os
import uuid
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

# Magic bytes for allowed types — checked in addition to extension,
# so a renamed .exe can't slip through as "resume.pdf".
MAGIC_BYTES = {
    ".pdf": [b"%PDF-"],
    ".docx": [b"PK\x03\x04"],  # docx is a zip container
}


def validate_and_save_upload(file: UploadFile) -> tuple[str, str]:
    """Validates extension, size and magic bytes; saves to disk.
    Returns (saved_path, extension)."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_UPLOAD_EXTENSIONS}",
        )

    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({size_mb:.1f}MB). Max is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    if not any(contents.startswith(sig) for sig in MAGIC_BYTES.get(ext, [])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its extension.",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4()}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        f.write(contents)

    return save_path, ext
