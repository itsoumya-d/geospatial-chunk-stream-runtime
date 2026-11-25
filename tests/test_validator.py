"""Unit tests for spatial chunk validation and serverless handler."""
import pytest
from geospatial_stream.models import SpatialChunk, BoundingBox3D
from geospatial_stream.validator import validate_chunk
from geospatial_stream.handler import serverless_ingest_handler


def test_bounding_box_geometry():
    bbox = BoundingBox3D(min_x=0.0, max_x=10.0, min_y=-5.0, max_y=5.0, min_z=100.0, max_z=150.0)
    assert bbox.width == 10.0
    assert bbox.height == 10.0
    assert bbox.depth == 50.0
    assert bbox.volume == 5000.0
    assert bbox.contains(5.0, 0.0, 125.0) is True
    assert bbox.contains(15.0, 0.0, 125.0) is False


def test_valid_3d_mesh_chunk():
    # A single 3D triangle in space
    vertices = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0)]
    triangles = [(0, 1, 2)]
    chunk = SpatialChunk(chunk_id="chunk-001", layer_id="bedrock-surface", vertices=vertices, triangles=triangles)

    res = validate_chunk(chunk)
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.vertex_count == 3
    assert res.triangle_count == 1
    assert res.surface_area == pytest.approx(50.0)
    assert res.bounding_box is not None
    assert res.bounding_box.min_x == 0.0
    assert res.bounding_box.max_x == 10.0
    assert res.bounding_box.min_y == 0.0
    assert res.bounding_box.max_y == 10.0


def test_invalid_chunk_out_of_range_indices():
    vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
    triangles = [(0, 1, 99)]  # index 99 does not exist
    chunk = SpatialChunk(chunk_id="bad-chunk", layer_id="fault-plane", vertices=vertices, triangles=triangles)

    res = validate_chunk(chunk)
    assert res.is_valid is False
    assert any("out-of-range" in e for e in res.errors)


def test_degenerate_triangle_detection():
    # Colinear points forming zero area triangle
    vertices = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (2.0, 2.0, 2.0)]
    triangles = [(0, 1, 2)]
    chunk = SpatialChunk(chunk_id="colinear-chunk", layer_id="strata", vertices=vertices, triangles=triangles)

    res = validate_chunk(chunk)
    assert res.is_valid is False
    assert any("degenerate" in e for e in res.errors)


def test_serverless_handler_batch():
    event = {
        "records": [
            {
                "chunk_id": "c-1",
                "layer_id": "geology-v1",
                "vertices": [[0, 0, 0], [4, 0, 0], [0, 3, 0]],
                "triangles": [[0, 1, 2]],
            },
            {
                "chunk_id": "c-2",
                "layer_id": "geology-v1",
                "vertices": [[10, 10, 10], [14, 10, 10], [10, 13, 10]],
                "triangles": [[0, 1, 2]],
            }
        ]
    }
    response = serverless_ingest_handler(event)
    assert response["statusCode"] == 200
    telemetry = response["telemetry"]
    assert telemetry["status"] == "ok"
    assert telemetry["processed_chunks"] == 2
    assert telemetry["valid_chunks"] == 2
    assert telemetry["failed_chunks"] == 0
    assert telemetry["total_vertices"] == 6
    assert telemetry["total_triangles"] == 2
    assert len(response["results"]) == 2


def test_serverless_handler_partial_failure():
    event = {
        "records": [
            {
                "chunk_id": "good-1",
                "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "triangles": [[0, 1, 2]],
            },
            {
                "chunk_id": "bad-1",
                "vertices": [],
                "triangles": [],
            }
        ]
    }
    response = serverless_ingest_handler(event)
    assert response["statusCode"] == 207
    telemetry = response["telemetry"]
    assert telemetry["status"] == "partial_failure"
    assert telemetry["valid_chunks"] == 1
    assert telemetry["failed_chunks"] == 1
