import base64
from io import BytesIO
from pathlib import Path

from PIL import Image


def encode_image_to_jpeg(image_path: Path, max_size: int = 1024, jpeg_quality=75) -> str:
    """Resize image to optimize for token usage"""
    image = Image.open(image_path)
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size))
    buffered = BytesIO()
    if image.format != "JPEG":
        image = image.convert("RGB")
    image.save(buffered, format="JPEG", quality=jpeg_quality)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def encode_image_to_png(image_path: Path, max_size: int = 1024) -> str:
    """Resize image to optimize for token usage"""
    image = Image.open(image_path)
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size))
    buffered = BytesIO()
    if image.format != "PNG":
        image = image.convert("RGBA")
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def convert_webp_to_jpeg(image_path: Path, jpeg_quality=95) -> str:
    """Convert a WebP image to JPEG format."""
    image = Image.open(image_path)
    buffered = BytesIO()
    if image.format != "JPEG":
        image = image.convert("RGB")
    image.save(buffered, format="JPEG", quality=jpeg_quality)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
