"""Serverless event ingestion handler for streaming spatial chunks."""
from __future__ import annotations
import time
from typing import Dict, Any, List
from geospatial_stream.models import SpatialChunk
from geospatial_stream.validator import validate_chunk


def serverless_ingest_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Standard serverless entrypoint (AWS Lambda / GCP Function compatible).
    Accepts a batch of spatial chunks, runs validation, computes bounding envelopes,
    and returns structured telemetry and execution manifests.
    """
    start_time = time.perf_counter()
    records = event.get("records") or event.get("chunks") or []
    if isinstance(event.get("body"), list):
        records = event["body"]

    results: List[Dict[str, Any]] = []
    processed_count = 0
    valid_count = 0
    error_count = 0
    total_vertices = 0
    total_triangles = 0

    for rec in records:
        processed_count += 1
        chunk_id = rec.get("chunk_id", f"chk-{processed_count}")
        layer_id = rec.get("layer_id", "default")
        raw_vertices = rec.get("vertices", [])
        raw_triangles = rec.get("triangles", [])
        attributes = rec.get("attributes", {})

        # Parse tuples
        vertices = [(float(v[0]), float(v[1]), float(v[2])) for v in raw_vertices if len(v) >= 3]
        triangles = [(int(t[0]), int(t[1]), int(t[2])) for t in raw_triangles if len(t) >= 3]

        chunk = SpatialChunk(
            chunk_id=chunk_id,
            layer_id=layer_id,
            vertices=vertices,
            triangles=triangles,
            attributes=attributes,
        )

        res = validate_chunk(chunk)
        if res.is_valid:
            valid_count += 1
        else:
            error_count += 1

        total_vertices += res.vertex_count
        total_triangles += res.triangle_count
        results.append(res.to_dict())

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    telemetry = {
        "status": "ok" if error_count == 0 else "partial_failure" if valid_count > 0 else "failed",
        "processed_chunks": processed_count,
        "valid_chunks": valid_count,
        "failed_chunks": error_count,
        "total_vertices": total_vertices,
        "total_triangles": total_triangles,
        "duration_ms": round(duration_ms, 2),
    }

    return {
        "statusCode": 200 if error_count == 0 else 207 if valid_count > 0 else 422,
        "telemetry": telemetry,
        "results": results,
    }
