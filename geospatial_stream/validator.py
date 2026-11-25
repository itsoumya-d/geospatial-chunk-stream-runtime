"""Geospatial chunk mesh validation and bounding box computation."""
from __future__ import annotations
import math
from typing import Optional, Tuple
from geospatial_stream.models import SpatialChunk, ChunkValidationResult, BoundingBox3D


def _triangle_area_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float], p3: Tuple[float, float, float]) -> float:
    # Cross product of (p2 - p1) and (p3 - p1)
    ax, ay, az = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    bx, by, bz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
    cx = ay * bz - az * by
    cy = az * bx - ax * bz
    cz = ax * by - ay * bx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def validate_chunk(
    chunk: SpatialChunk,
    max_boundary: Optional[BoundingBox3D] = None,
    allow_empty: bool = False,
) -> ChunkValidationResult:
    """Validates 3D coordinates, detects degenerate elements, and computes bounding geometry."""
    errors = []
    if not chunk.chunk_id:
        errors.append("chunk_id must not be empty")

    n_vertices = len(chunk.vertices)
    if n_vertices == 0:
        if not allow_empty:
            errors.append("chunk has zero vertices")
        return ChunkValidationResult(
            chunk_id=chunk.chunk_id,
            is_valid=len(errors) == 0,
            errors=errors,
            vertex_count=0,
            triangle_count=0,
        )

    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for i, v in enumerate(chunk.vertices):
        if len(v) != 3:
            errors.append(f"vertex at index {i} does not have 3 components: {v}")
            continue
        x, y, z = v
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            errors.append(f"vertex at index {i} contains non-finite coordinates: ({x}, {y}, {z})")
            continue

        if x < min_x: min_x = x
        if x > max_x: max_x = x
        if y < min_y: min_y = y
        if y > max_y: max_y = y
        if z < min_z: min_z = z
        if z > max_z: max_z = z

    if min_x == float("inf"):
        return ChunkValidationResult(
            chunk_id=chunk.chunk_id,
            is_valid=False,
            errors=errors or ["no valid vertices found"],
            vertex_count=n_vertices,
            triangle_count=len(chunk.triangles),
        )

    bbox = BoundingBox3D(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y, min_z=min_z, max_z=max_z)

    if max_boundary:
        if (
            bbox.min_x < max_boundary.min_x or bbox.max_x > max_boundary.max_x or
            bbox.min_y < max_boundary.min_y or bbox.max_y > max_boundary.max_y or
            bbox.min_z < max_boundary.min_z or bbox.max_z > max_boundary.max_z
        ):
            errors.append("chunk vertices exceed allowed global bounding boundary")

    total_surface_area = 0.0
    for idx, tri in enumerate(chunk.triangles):
        if len(tri) != 3:
            errors.append(f"triangle at index {idx} does not have 3 indices: {tri}")
            continue
        i1, i2, i3 = tri
        if not (0 <= i1 < n_vertices and 0 <= i2 < n_vertices and 0 <= i3 < n_vertices):
            errors.append(f"triangle at index {idx} references out-of-range vertex index: {tri}")
            continue
        if i1 == i2 or i2 == i3 or i1 == i3:
            errors.append(f"degenerate triangle with duplicated vertices at index {idx}: {tri}")
            continue

        area = _triangle_area_3d(chunk.vertices[i1], chunk.vertices[i2], chunk.vertices[i3])
        if area <= 1e-12:
            errors.append(f"degenerate colinear triangle (zero area) at index {idx}")
        total_surface_area += area

    return ChunkValidationResult(
        chunk_id=chunk.chunk_id,
        is_valid=len(errors) == 0,
        bounding_box=bbox,
        errors=errors,
        vertex_count=n_vertices,
        triangle_count=len(chunk.triangles),
        surface_area=total_surface_area,
    )
