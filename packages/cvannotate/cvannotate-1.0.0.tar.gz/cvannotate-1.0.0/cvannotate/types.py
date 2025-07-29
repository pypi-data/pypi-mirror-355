from dataclasses import dataclass, field
from typing import List


@dataclass
class BoundingBox:
    class_id: int
    xmin: float
    ymin: float
    xmax: float
    ymax: float


@dataclass
class ImageAnnotation:
    filename: str
    width: int
    height: int
    boxes: List[BoundingBox] = field(default_factory=list)
