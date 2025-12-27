from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile, HTTPException
from PIL import Image

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB

CT_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

def _only_under_media_root(abs_path: Path) -> bool:
    """Evita borrar cosas fuera de MEDIA_ROOT."""
    try:
        abs_root = Path(settings.MEDIA_ROOT).resolve()
        abs_file = abs_path.resolve()
        return abs_root in abs_file.parents or abs_file == abs_root
    except Exception:
        return False

def _url_to_abs_path(url: str) -> Optional[Path]:
    """
    Convierte '/media/services/x.jpg' -> '<MEDIA_ROOT>/services/x.jpg'
    Devuelve None si no parece un path de media.
    """
    if not url:
        return None
    prefix = settings.MEDIA_URL_PREFIX.rstrip("/")  # ej: '/media'
    if not url.startswith(prefix + "/"):
        return None
    rel = url[len(prefix) + 1:]  # quita '/media/'
    return (Path(settings.MEDIA_ROOT) / rel)

def _delete_if_exists_by_url(url: Optional[str]) -> None:
    if not url:
        return
    p = _url_to_abs_path(url)
    if not p:
        return
    if not _only_under_media_root(p):
        return
    if p.exists() and p.is_file():
        try:
            p.unlink()
        except Exception:
            # no tumbar la request por no poder borrar
            pass

def _save_bytes(file: UploadFile) -> tuple[bytes, str]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Invalid image type. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}")

    data = file.file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "Image too large (max 5MB)")
    ext = CT_TO_EXT[file.content_type]
    return data, ext

def _write_file(abs_path: Path, data: bytes) -> None:
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)

def _make_thumbnail(abs_original: Path, abs_thumb: Path, max_size: int = 600, quality: int = 85) -> None:
    """
    Crea un thumbnail en JPG (más compatible para web).
    Mantiene proporción, max ancho/alto = max_size.
    """
    abs_thumb.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(abs_original) as img:
        img = img.convert("RGB")  # normaliza a JPG
        img.thumbnail((max_size, max_size))
        img.save(abs_thumb, format="JPEG", quality=quality, optimize=True)

def save_image_replace_and_thumb(
    *,
    file: UploadFile,
    folder: str,                 # 'services' | 'products' | 'employees'
    old_image_url: Optional[str] = None,
    old_thumb_url: Optional[str] = None,
    thumb_max_size: int = 600,
) -> Tuple[str, str]:
    """
    Guarda imagen + thumbnail.
    Borra imagen/thumbnail anteriores (si existían).
    Retorna (image_url, thumb_url)
    """

    # 1) borrar anteriores
    _delete_if_exists_by_url(old_image_url)
    _delete_if_exists_by_url(old_thumb_url)

    # 2) guardar nueva imagen original
    data, ext = _save_bytes(file)
    filename = f"{uuid.uuid4().hex}{ext}"

    rel_original = Path(folder) / filename
    abs_original = Path(settings.MEDIA_ROOT) / rel_original
    _write_file(abs_original, data)

    image_url = f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/{rel_original.as_posix()}"

    # 3) thumbnail
    thumb_name = f"{Path(filename).stem}_thumb.jpg"
    rel_thumb = Path(folder) / "thumbs" / thumb_name
    abs_thumb = Path(settings.MEDIA_ROOT) / rel_thumb

    _make_thumbnail(abs_original, abs_thumb, max_size=thumb_max_size)

    thumb_url = f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/{rel_thumb.as_posix()}"

    return image_url, thumb_url
