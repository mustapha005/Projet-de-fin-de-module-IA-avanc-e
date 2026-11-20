"""Render a local-only contact sheet for quarantined duplicate components."""
import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = json.loads((ROOT / "data" / "dedup_report.json").read_text())
    inventory = pd.read_csv(ROOT / "data" / "manifests" / "busi_inventory.csv").set_index("image_id")
    clusters = [c for c in report["clusters"] if c["action"] == "quarantine_conflict"]
    width, row_height, columns = 320, 240, max(len(c["members"]) for c in clusters)
    sheet = Image.new("RGB", (width * columns, row_height * len(clusters)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for row, cluster in enumerate(clusters):
        for column, image_id in enumerate(cluster["members"]):
            image = Image.open(ROOT / inventory.loc[image_id, "path"]).convert("RGB")
            thumbnail = ImageOps.contain(image, (width - 12, row_height - 46))
            x, y = column * width + 6, row * row_height + 6
            sheet.paste(thumbnail, (x, y))
            draw.text((x, y + row_height - 42), image_id, font=font, fill="black")
            if cluster["conflicts_with_excluded_normal"]:
                draw.text((x, y + row_height - 23), "Published duplicate in normal class", font=font, fill="red")
    target = ROOT / "data" / "cache" / "qa_conflicts.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    print(target)


if __name__ == "__main__":
    main()
