# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Image utils."""
from PIL import Image, ImageDraw, ImageFont
import datetime

FONT_PATH = "../fonts/FreeMono.ttf"


def compress_pil_image_timestamp(image_path):
    """Compress PIL image.

    Args:
        image (PIL.Image): Image to compress
        image_path (str): Output file path

    """
    image = Image.open(image_path)
    w, h = image.size
    ratio = max(float(w) / 1280.0, float(h) / 1024.0, 1.0)
    image = image.resize((int(w / ratio), int(h / ratio)) ) # , Image.Resampling.LANCZOS )
    d = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, 28, encoding="unic")
    t = str(datetime.datetime.now())
    d.text((9, 10), t, font=font, fill=(0, 0, 0))
    d.text((11, 10), t, font=font, fill=(0, 0, 0))
    d.text((10, 9), t, font=font, fill=(0, 0, 0))
    d.text((10, 11), t, font=font, fill=(0, 0, 0))
    d.text((10, 10), t, font=font, fill=(255, 0, 0))
    w, h = image.size
    image.save(image_path, optimize=True, quality=60)
