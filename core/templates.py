from __future__ import annotations

import json
import math
from pathlib import Path


def check_templates(path: Path, required: set[str]) -> None:
    if not path.is_file():
        raise ValueError(f"模板文件不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        categories = {category["id"]: category["name"] for category in data["categories"]}
        images = {image["id"]: image for image in data["images"]}
        available = set()
        boxes = {}
        for annotation in data["annotations"]:
            image = images[annotation["image_id"]]
            name = categories[annotation["category_id"]]
            x, y, w, h = annotation["bbox"]
            bounds = (x, y, w, h, image["width"], image["height"])
            if not all(type(value) in (int, float) and math.isfinite(value) for value in bounds):
                raise ValueError(f"模板 {name} 的标注尺寸无效")
            if not (0 <= x < x + w <= image["width"] and 0 <= y < y + h <= image["height"]):
                raise ValueError(f"模板 {name} 的标注超出截图")
            box = (round(x), round(y), round(x + w), round(y + h))
            if box[0] == box[2] or box[1] == box[3]:
                raise ValueError(f"模板 {name} 的标注小于 1 像素")
            if boxes.setdefault(name, box) != box:
                raise ValueError(f"模板 {name} 存在不同位置的重复标注")
            available.add(name)

        for image in images.values():
            if not (path.parent / image["file_name"]).is_file():
                raise ValueError(f"找不到模板截图：{image['file_name']}")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"无效的 COCO 模板文件：{path}") from exc

    missing = required - available
    if missing:
        raise ValueError(f"缺少模板标注：{', '.join(sorted(missing))}")
