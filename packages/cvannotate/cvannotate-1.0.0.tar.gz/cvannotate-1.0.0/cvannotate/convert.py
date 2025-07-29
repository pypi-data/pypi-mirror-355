"""Core conversion functions for annotation formats."""

from pathlib import Path
from typing import Iterable, List

from .converters import coco, voc, yolo
from .types import ImageAnnotation


def read_annotation(
    path: Path, fmt: str, width: int = None, height: int = None
) -> List[ImageAnnotation]:
    """Read annotation from file in specified format.

    Args:
        path: Path to annotation file
        fmt: Format ('yolo', 'voc', 'coco')
        width: Image width (required for YOLO)
        height: Image height (required for YOLO)

    Returns:
        List of ImageAnnotation objects
    """
    fmt = fmt.lower()
    if fmt == "yolo":
        if width is None or height is None:
            raise ValueError("width and height required for YOLO")
        ann = yolo.read_yolo(path, width, height)
        return [ann]
    if fmt == "voc":
        ann = voc.read_voc(path)
        return [ann]
    if fmt == "coco":
        return coco.read_coco(path)
    raise ValueError(f"Unsupported format {fmt}")


def write_annotation(
    anns: List[ImageAnnotation], out_dir: Path, fmt: str, class_map: Iterable[str]
):
    """Write annotations to files in specified format.

    Args:
        anns: List of ImageAnnotation objects to write
        out_dir: Output directory
        fmt: Output format ('yolo', 'voc', 'coco')
        class_map: List of class names
    """
    fmt = fmt.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    if fmt == "yolo":
        for ann in anns:
            yolo.write_yolo(ann, out_dir / f"{ann.filename}.txt", class_map)
    elif fmt == "voc":
        for ann in anns:
            voc.write_voc(ann, out_dir / f"{ann.filename}.xml", class_map)
    elif fmt == "coco":
        coco.write_coco(anns, out_dir / "annotations.json", class_map)
    else:
        raise ValueError(f"Unsupported format {fmt}")
