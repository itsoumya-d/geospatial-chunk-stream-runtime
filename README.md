# Geospatial Chunk Stream Runtime

[![CI](https://github.com/itsoumya-d/geospatial-chunk-stream-runtime/actions/workflows/ci.yml/badge.svg)](https://github.com/itsoumya-d/geospatial-chunk-stream-runtime/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A lightweight, high-throughput serverless runtime designed for ingesting, validating, and computing exact 3D spatial bounding geometry over geological mesh and point-cloud chunks.

## Capabilities

- **Streaming Spatial Geometry Validation**: Validates 3D coordinates, detects degenerate colinear elements (zero surface area), out-of-range index references, and enforces global boundary envelopes.
- **Serverless Event Ingestion**: Event-driven entrypoint compatible with AWS Lambda, GCP Cloud Functions, and SQS/Kinesis batch processing with zero external C-extension overhead.
- **Structured Observability**: Standardized telemetry emission compatible with Datadog and CloudWatch metrics (p50/p95/p99 execution duration, chunk byte volume, vertex/triangle density, and error taxonomy).

## Architecture

```
                       [Incoming Ingestion Batch]
                     (AWS Lambda / Cloud Function)
                                   |
                                   v
                    +-----------------------------+
                    |  serverless_ingest_handler  |
                    +-----------------------------+
                                   |
               +-------------------+-------------------+
               |                                       |
               v                                       v
      [Coordinate Check]                      [Topology Check]
- Finite coordinate validation           - Triangle index range checks
- Global boundary limits                 - Degenerate colinear triangles
- 3D Bounding Box calculation            - Surface area calculation
               |                                       |
               +-------------------+-------------------+
                                   |
                                   v
                    +-----------------------------+
                    |     Telemetry & Manifest    |
                    | - Per-chunk valid/error     |
                    | - Exact 3D Bounding Box     |
                    | - Datadog/CloudWatch metrics|
                    +-----------------------------+
```

## Payload Schema

```json
{
  "records": [
    {
      "chunk_id": "chunk-bedrock-001",
      "layer_id": "lithology-surface-v1",
      "vertices": [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [0.0, 10.0, 0.0]
      ],
      "triangles": [
        [0, 1, 2]
      ],
      "attributes": {
        "formation": "schist",
        "subsurface_depth_m": 142.5
      }
    }
  ]
}
```

## Structured Telemetry Output

```json
{
  "statusCode": 200,
  "telemetry": {
    "status": "ok",
    "processed_chunks": 1,
    "valid_chunks": 1,
    "failed_chunks": 0,
    "total_vertices": 3,
    "total_triangles": 1,
    "duration_ms": 1.25
  },
  "results": [
    {
      "chunk_id": "chunk-bedrock-001",
      "is_valid": true,
      "bounding_box": {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": 0.0,
        "max_y": 10.0,
        "min_z": 0.0,
        "max_z": 0.0,
        "volume": 0.0
      },
      "errors": [],
      "vertex_count": 3,
      "triangle_count": 1,
      "surface_area": 50.0
    }
  ]
}
```

## Installation & Testing

```bash
git clone https://github.com/itsoumya-d/geospatial-chunk-stream-runtime.git
cd geospatial-chunk-stream-runtime
pip install -e ".[dev]"

# Run full test suite
pytest -v
```

## License

MIT
