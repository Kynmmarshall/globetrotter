"""Generate responsive destination image variants and JSON seeds.

Reads the canonical seed at scripts/data/destinations.seed.json, resizes each
source image from "destination images/" into a few WebP widths, and writes
the resulting files into EACH backend's own static/ folder (images are backend
static assets, not frontend-bundled assets; the frontend fetches them over
HTTP from whichever backend base URL it is configured against):

  - backend/monolith/static/destinations/<slug>-<width>.webp
  - backend/monolith/data/destinations.json
  - backend/microservice/recommendation_service/static/destinations/<slug>-<width>.webp
  - backend/microservice/recommendation_service/app/data/destinations.seed.json

Each JSON seed's "image" paths are root-relative ("/static/destinations/...")
and are meant to be resolved against that backend's own base URL, e.g.
f"{RECOMMENDATION_SERVICE_BASE_URL}{image['primary']}". The monolith and the
recommendation service each serve their own copy of the files from their own
static/ folder (mounted at "/static") so the two backends stay independently
deployable with no shared filesystem or import between them.

Run this once before starting either backend for the first time, and again
whenever "destination images/" or destinations.seed.json changes.

    python scripts/build_destination_assets.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "destination images"
SEED_PATH = ROOT / "scripts" / "data" / "destinations.seed.json"

MONOLITH_DIR = ROOT / "backend" / "monolith"
RECOMMENDATION_DIR = ROOT / "backend" / "microservice" / "recommendation_service"

# Each backend gets its own static/ image folder and its own JSON seed file.
BACKEND_TARGETS = [
    {
        "image_dir": MONOLITH_DIR / "static" / "destinations",
        "seed_path": MONOLITH_DIR / "data" / "destinations.json",
    },
    {
        "image_dir": RECOMMENDATION_DIR / "static" / "destinations",
        "seed_path": RECOMMENDATION_DIR / "app" / "data" / "destinations.seed.json",
    },
]

WIDTHS = (480, 960, 1440)
PRIMARY_WIDTH = 960
STATIC_URL_PREFIX = "/static/destinations"


def build() -> None:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    destinations = seed["destinations"]

    for target in BACKEND_TARGETS:
        target["image_dir"].mkdir(parents=True, exist_ok=True)
        target["seed_path"].parent.mkdir(parents=True, exist_ok=True)

    enriched_destinations: list[dict] = []

    for entry in destinations:
        source_path = SOURCE_DIR / entry["source_image"]
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source image for {entry['slug']!r}: {source_path}")

        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            original_width, original_height = image.size

            variants = []
            for target_width in WIDTHS:
                width = min(target_width, original_width)
                height = round(original_height * (width / original_width))
                resized = image.resize((width, height), Image.LANCZOS)
                out_name = f"{entry['slug']}-{target_width}.webp"

                # Write the same rendered variant into every backend's static/ folder.
                for target in BACKEND_TARGETS:
                    resized.save(target["image_dir"] / out_name, format="WEBP", quality=82, method=6)

                variants.append(
                    {
                        "width": width,
                        "height": height,
                        "path": f"{STATIC_URL_PREFIX}/{out_name}",
                    }
                )

        primary = next(
            (v for v in variants if v["width"] == min(PRIMARY_WIDTH, original_width)),
            variants[-1],
        )

        alt_text = f"{entry['name']} in {seed['city']}, {seed['country']}"

        enriched_destinations.append(
            {
                **entry,
                "city": seed["city"],
                "country": seed["country"],
                "currency": seed["currency"],
                "timezone": seed["timezone"],
                "image": {
                    "alt": alt_text,
                    "primary": primary["path"],
                    "variants": variants,
                },
            }
        )

    for target in BACKEND_TARGETS:
        target["seed_path"].write_text(json.dumps(enriched_destinations, indent=2), encoding="utf-8")
        print(f"Wrote seed: {target['seed_path'].relative_to(ROOT)}")
        print(f"Wrote images into: {target['image_dir'].relative_to(ROOT)}")

    print(f"Processed {len(enriched_destinations)} destinations.")


if __name__ == "__main__":
    build()
