from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB


def save_entry_image(file: FileStorage, entry_id: str) -> str | None:
    """Save an uploaded image for a vocabulary entry.

    Returns the relative path stored in the DB (e.g. 'data/images/<entry_id>.jpg'),
    or None if the file is missing / invalid.
    """
    if not file or not file.filename:
        return None

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None

    data = file.read()
    if len(data) > MAX_IMAGE_BYTES:
        return None

    images_dir = Path(current_app.root_path).parent / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{entry_id}.{ext}"
    dest = images_dir / filename
    dest.write_bytes(data)

    return f"data/images/{filename}"


def delete_entry_image(image_path: str | None) -> None:
    if not image_path:
        return
    full = Path(current_app.root_path).parent / image_path
    if full.exists():
        full.unlink()
