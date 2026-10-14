"""Prepare the supplied Naiwa reference for the cover without changing its likeness.

Run from the project root with Python + Pillow + NumPy.
The original JPEG is preserved. White teeth and highlights enclosed within the
character are retained; only background connected to the outer edge is removed.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ref" / "img" / "fig-006-021.jpg"
OUTPUT = ROOT / "figures" / "cover_naiwa_cutout.png"


def main():
    image = Image.open(SOURCE).convert("RGB")
    rgb = np.asarray(image).astype(np.float64)
    high, low = rgb.max(axis=2), rgb.min(axis=2)

    # The supplied reference has neutral white/grey background and a saturated
    # yellow/brown subject. Connectivity protects the teeth inside the mouth.
    neutral_background = ((high - low) < 35) & (low > 135)
    candidate = Image.fromarray((neutral_background * 255).astype("uint8")).copy()
    ImageDraw.Draw(candidate).rectangle((0, 0, image.width - 1, image.height - 1), outline=255)
    ImageDraw.floodfill(candidate, (0, 0), 128)
    background = np.asarray(candidate) == 128
    foreground = ~background

    # Discard isolated JPEG specks outside the main character.
    components = Image.fromarray((foreground * 255).astype("uint8")).copy()
    subject_seed = (image.width // 2, image.height // 2)
    if not foreground[subject_seed[1], subject_seed[0]]:
        raise ValueError("The reference changed: expected character at image centre.")
    ImageDraw.floodfill(components, subject_seed, 128)
    foreground = np.asarray(components) == 128
    matte = Image.fromarray((foreground * 255).astype("uint8"))
    matte = matte.filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.GaussianBlur(0.65)
    )
    alpha = np.asarray(matte).astype(np.float64) / 255

    # Remove the white fringe from antialiased boundary pixels only.
    safe_alpha = np.maximum(alpha, 0.03)
    unpremultiplied = (rgb - (1 - alpha[..., None]) * 250) / safe_alpha[..., None]
    clean_rgb = np.clip(unpremultiplied, 0, 255).astype("uint8")
    clean_rgb[alpha < 0.015] = 0
    rgba = np.dstack((clean_rgb, np.asarray(matte)))
    result = Image.fromarray(rgba)
    box = result.getbbox()
    if box is None:
        raise ValueError("Background extraction produced an empty mask.")
    cropped = result.crop(box)
    padding = 28
    asset = Image.new("RGBA", (cropped.width + padding * 2, cropped.height + padding * 2))
    asset.paste(cropped, (padding, padding))
    asset.save(OUTPUT, dpi=(300, 300), optimize=True)
    print(f"Source: {SOURCE}")
    print(f"Character bounds: {box}")
    print(f"Output: {OUTPUT} ({asset.width} x {asset.height}, RGBA)")


if __name__ == "__main__":
    main()
