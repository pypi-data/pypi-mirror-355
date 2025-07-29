import json
from pathlib import Path
from typing import Dict, Iterable, List

from ..types import BoundingBox, ImageAnnotation


def read_coco(path: Path) -> List[ImageAnnotation]:
    data = json.loads(path.read_text())
    id_to_filename = {img["id"]: img["file_name"] for img in data.get("images", [])}
    id_to_size = {
        img["id"]: (img["width"], img["height"]) for img in data.get("images", [])
    }
    annotations: Dict[int, ImageAnnotation] = {}
    for ann in data.get("annotations", []):
        image_id = ann["image_id"]
        if image_id not in annotations:
            filename = id_to_filename[image_id]
            width, height = id_to_size[image_id]
            annotations[image_id] = ImageAnnotation(filename, width, height, [])
        bbox = ann["bbox"]  # xmin, ymin, w, h
        xmin, ymin, w, h = bbox
        boxes = annotations[image_id].boxes
        boxes.append(BoundingBox(ann["category_id"], xmin, ymin, xmin + w, ymin + h))
    return list(annotations.values())


def write_coco(anns: List[ImageAnnotation], path: Path, class_map: Iterable[str]):
    images = []
    annotations = []
    categories = [{"id": i, "name": name} for i, name in enumerate(class_map)]
    ann_id = 1
    for img_id, ann in enumerate(anns):
        images.append(
            {
                "id": img_id,
                "file_name": ann.filename,
                "width": ann.width,
                "height": ann.height,
            }
        )
        for box in ann.boxes:
            w = box.xmax - box.xmin
            h = box.ymax - box.ymin
            annotations.append(
                {
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": box.class_id,
                    "bbox": [box.xmin, box.ymin, w, h],
                    "area": w * h,
                    "iscrowd": 0,
                }
            )
            ann_id += 1
    data = {"images": images, "annotations": annotations, "categories": categories}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
