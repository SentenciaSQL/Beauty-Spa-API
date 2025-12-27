import os
import uuid
from typing import Optional
from fastapi import UploadFile
from PIL import Image

UPLOAD_ROOT = "media"
THUMB_SIZE = (300, 300)  # ideal para Angular cards / sliders

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _get_extension(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]

def _delete_if_exists(path: Optional[str]):
    if not path:
        return
    if path.startswith("/"):
        path = path[1:]
    if os.path.exists(path):
        os.remove(path)

def save_image_and_replace(
    *,
    file: UploadFile,
    folder: str,
    old_url: Optional[str] = None,
    filename_prefix: str,
    make_thumbnail: bool = True,
) -> str:
    """
    Guarda una imagen, borra la anterior y opcionalmente genera thumbnail.
    Retorna la URL pública del archivo principal.
    """

    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid image format")

    # Paths
    target_dir = os.path.join(UPLOAD_ROOT, folder)
    _ensure_dir(target_dir)

    uid = uuid.uuid4().hex[:10]
    filename = f"{filename_prefix}_{uid}{ext}"
    filepath = os.path.join(target_dir, filename)

    # Guardar archivo original
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    # Borrar anterior
    _delete_if_exists(old_url)

    # Thumbnail
    if make_thumbnail:
        thumb_name = f"{filename_prefix}_{uid}_thumb{ext}"
        thumb_path = os.path.join(target_dir, thumb_name)

        with Image.open(filepath) as img:
            img.thumbnail(THUMB_SIZE)
            img.save(thumb_path)

        # borrar thumbnail viejo si existía
        if old_url:
            old_thumb = old_url.replace(ext, f"_thumb{ext}")
            _delete_if_exists(old_thumb)

    return f"/{UPLOAD_ROOT}/{folder}/{filename}"
