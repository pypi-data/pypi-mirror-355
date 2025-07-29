from pathlib import Path
from typing import Iterable, List

from ..types import BoundingBox, ImageAnnotation


def read_yolo(path: Path, width: int, height: int) -> ImageAnnotation:
    boxes: List[BoundingBox] = []
    with path.open() as f:
        for line in f:
            if line.strip() == "":
                continue
            parts = line.strip().split()
            class_id = int(parts[0])
            xc, yc, w, h = map(float, parts[1:])
            xmin = (xc - w / 2) * width
            ymin = (yc - h / 2) * height
            xmax = (xc + w / 2) * width
            ymax = (yc + h / 2) * height
            boxes.append(BoundingBox(class_id, xmin, ymin, xmax, ymax))
    return ImageAnnotation(path.stem, width, height, boxes)


def write_yolo(ann: ImageAnnotation, path: Path, class_map: Iterable[str]):
    lines = []
    for box in ann.boxes:
        xc = ((box.xmin + box.xmax) / 2) / ann.width
        yc = ((box.ymin + box.ymax) / 2) / ann.height
        w = (box.xmax - box.xmin) / ann.width
        h = (box.ymax - box.ymin) / ann.height
        lines.append(f"{box.class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
