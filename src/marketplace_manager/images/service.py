"""Safe local image validation, organization, and simple processing."""
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from marketplace_manager.core.config import DATA_DIR

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def validate_image(path: Path) -> tuple[bool, str | None]:
    """Return whether the file is a supported local image and a friendly error message."""
    if not path.exists() or not path.is_file():
        return False, "Image file was not found."
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format is None or image.format.upper() not in SUPPORTED_FORMATS:
                return False, "Unsupported image format. Use JPEG, PNG, WEBP, or GIF."
        return True, None
    except (UnidentifiedImageError, OSError, ValueError):
        return False, "This file is not a valid image or is corrupted."


def get_image_dimensions(path: Path) -> tuple[int, int] | None:
    """Return the image width and height if the file is valid."""
    if not path.exists():
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _destination_path(source: Path, action: str) -> Path:
    stem = f"{source.stem}_{action}"
    return source.with_name(f"{stem}{source.suffix.lower()}")


def process_image(path: Path, action: str, *, max_size: int | None = None, degrees: int = 90, quality: int = 80) -> Path | None:
    """Apply a simple local image operation without changing the original file."""
    valid, error = validate_image(path)
    if not valid or not path.exists():
        return None

    target = _destination_path(path, action)
    if target.exists():
        target = path.with_name(f"{path.stem}_{action}_{abs(hash(path)) % 100000}{path.suffix.lower()}")

    try:
        with Image.open(path) as image:
            if action == "resize":
                resized = image.copy()
                if max_size is None:
                    max_size = 1200
                resized.thumbnail((max_size, max_size))
                resized.save(target, optimize=True, quality=quality)
            elif action == "crop":
                width, height = image.size
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                cropped = image.crop((left, top, left + size, top + size))
                cropped.save(target, optimize=True, quality=quality)
            elif action == "rotate":
                rotated = image.rotate(degrees, expand=True)
                rotated.save(target, optimize=True, quality=quality)
            elif action == "optimize":
                image.save(target, optimize=True, quality=quality)
            else:
                raise ValueError(f"Unsupported image action: {action}")
        return target
    except (OSError, ValueError, UnidentifiedImageError):
        return None


def organize_image(source: Path, product_id: int, max_size: int | None = None) -> Path:
    valid, error = validate_image(source)
    if not valid: raise ValueError(error)
    destination_dir = DATA_DIR / "images" / str(product_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if destination.exists():
        destination = destination_dir / f"{source.stem}_{destination.stat().st_mtime_ns}{source.suffix.lower()}"
    if max_size:
        with Image.open(source) as image:
            resized = image.copy()
            resized.thumbnail((max_size, max_size))
            resized.save(destination)
    else:
        shutil.copy2(source, destination)
    return destination
