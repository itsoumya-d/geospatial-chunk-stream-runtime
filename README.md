# Geospatial Chunk Stream Runtime

A lightweight, serverless runtime for ingesting, validating, and computing spatial bounding boxes over 3D geospatial mesh and point-cloud chunks.

## Capabilities

- **Streaming Spatial Validation**: Validates 3D coordinates, detects degenerate or out-of-bounds geometries, and enforces strict spatial schema boundaries.
- **Serverless Event Ingestion**: AWS Lambda / GCP Cloud Functions compatible handler for batch chunk payload parsing with minimal cold-start overhead.
- **Structured Telemetry**: Standardized Datadog / CloudWatch metric emission for ingestion latency, chunk byte volume, and validation status.

## Usage

```bash
pip install -e ".[dev]"
pytest -v
```
