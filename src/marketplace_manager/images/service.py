"""Safe local image validation, organization, and resizing."""
import shutil
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from marketplace_manager.core.config import DATA_DIR

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def validate_image(path: Path) -> tuple[bool, str | None]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format not in SUPPORTED_FORMATS: return False, "Unsupported image format. Use JPEG, PNG, WEBP, or GIF."
        return True, None
    except (UnidentifiedImageError, OSError): return False, "This file is not a valid image or is corrupted."


def organize_image(source: Path, product_id: int, max_size: int | None = None) -> Path:
    valid, error = validate_image(source)
    if not valid: raise ValueError(error)
    destination_dir = DATA_DIR / "images" / str(product_id); destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if destination.exists(): destination = destination_dir / f"{source.stem}_{destination.stat().st_mtime_ns}{source.suffix.lower()}"
    if max_size:
        with Image.open(source) as image:
            image.thumbnail((max_size, max_size)); image.save(destination)
    else: shutil.copy2(source, destination)
    return destination
