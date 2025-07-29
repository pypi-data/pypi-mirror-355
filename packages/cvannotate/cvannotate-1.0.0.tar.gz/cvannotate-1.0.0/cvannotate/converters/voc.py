import xml.etree.ElementTree as StandardET  # nosec B405 - only used for writing, not parsing
from pathlib import Path
from typing import Iterable

import defusedxml.ElementTree as ET

from ..types import BoundingBox, ImageAnnotation


def read_voc(path: Path) -> ImageAnnotation:
    # Use defusedxml for parsing (security)
    tree = ET.parse(path)
    root = tree.getroot()
    size = root.find("size")
    width = int(size.find("width").text)
    height = int(size.find("height").text)
    filename = root.findtext("filename") or path.stem
    boxes = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        bndbox = obj.find("bndbox")
        xmin = float(bndbox.findtext("xmin"))
        ymin = float(bndbox.findtext("ymin"))
        xmax = float(bndbox.findtext("xmax"))
        ymax = float(bndbox.findtext("ymax"))
        class_id = int(obj.findtext("name_id") or 0)
        boxes.append(BoundingBox(class_id, xmin, ymin, xmax, ymax))
    return ImageAnnotation(filename, width, height, boxes)


def write_voc(ann: ImageAnnotation, path: Path, class_map: Iterable[str]):
    # Use standard ElementTree for writing (creation)
    root = StandardET.Element("annotation")
    StandardET.SubElement(root, "filename").text = ann.filename
    size = StandardET.SubElement(root, "size")
    StandardET.SubElement(size, "width").text = str(ann.width)
    StandardET.SubElement(size, "height").text = str(ann.height)
    StandardET.SubElement(size, "depth").text = "3"

    for box in ann.boxes:
        obj = StandardET.SubElement(root, "object")
        name = list(class_map)[box.class_id]
        StandardET.SubElement(obj, "name").text = name
        bndbox = StandardET.SubElement(obj, "bndbox")
        StandardET.SubElement(bndbox, "xmin").text = str(int(box.xmin))
        StandardET.SubElement(bndbox, "ymin").text = str(int(box.ymin))
        StandardET.SubElement(bndbox, "xmax").text = str(int(box.xmax))
        StandardET.SubElement(bndbox, "ymax").text = str(int(box.ymax))
    tree = StandardET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path)
