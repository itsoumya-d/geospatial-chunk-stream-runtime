"""Domain models for 3D geospatial mesh and point-cloud chunks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import math


@dataclass(frozen=True)
class BoundingBox3D:
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def depth(self) -> float:
        return self.max_z - self.min_z

    @property
    def volume(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height) * max(0.0, self.depth)

    def contains(self, x: float, y: float, z: float) -> bool:
        return (
            self.min_x <= x <= self.max_x and
            self.min_y <= y <= self.min_y + self.height and
            self.min_z <= z <= self.max_z
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "min_x": self.min_x,
            "max_x": self.max_x,
            "min_y": self.min_y,
            "max_y": self.max_y,
            "min_z": self.min_z,
            "max_z": self.max_z,
            "volume": self.volume,
        }


@dataclass
class SpatialChunk:
    chunk_id: str
    layer_id: str
    vertices: List[Tuple[float, float, float]]
    triangles: List[Tuple[int, int, int]] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkValidationResult:
    chunk_id: str
    is_valid: bool
    bounding_box: Optional[BoundingBox3D] = None
    errors: List[str] = field(default_factory=list)
    vertex_count: int = 0
    triangle_count: int = 0
    surface_area: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "is_valid": self.is_valid,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "errors": self.errors,
            "vertex_count": self.vertex_count,
            "triangle_count": self.triangle_count,
            "surface_area": round(self.surface_area, 4),
        }
