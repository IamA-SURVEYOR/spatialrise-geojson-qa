"""SpatialRise GeoJSON QA: dependency-free basic validation for FeatureCollections.

This is a lightweight screening tool, not a replacement for full topology checks
from GEOS/Shapely or a GIS application.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

GEOMETRY_TYPES = {
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon",
    "MultiPolygon", "GeometryCollection",
}


def _walk_positions(geometry: dict[str, Any]):
    """Yield GeoJSON positions or raise ValueError for malformed coordinates."""
    kind = geometry.get("type")
    if kind == "GeometryCollection":
        children = geometry.get("geometries")
        if not isinstance(children, list):
            raise ValueError("GeometryCollection.geometries must be an array")
        for child in children:
            if not isinstance(child, dict):
                raise ValueError("GeometryCollection child must be an object")
            yield from _walk_positions(child)
        return

    depth = {
        "Point": 0, "MultiPoint": 1, "LineString": 1,
        "MultiLineString": 2, "Polygon": 2, "MultiPolygon": 3,
    }.get(kind)
    if depth is None:
        raise ValueError(f"unsupported geometry type: {kind!r}")

    coords = geometry.get("coordinates")

    def unpack(node: Any, level: int):
        if not isinstance(node, list):
            raise ValueError("coordinates must be arrays")
        if level == 0:
            if len(node) < 2 or not all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in node[:2]
            ):
                raise ValueError("positions must include numeric longitude and latitude")
            yield node
            return
        if not node:
            raise ValueError("nested coordinates cannot be empty")
        for item in node:
            yield from unpack(item, level - 1)

    yield from unpack(coords, depth)


def inspect_geojson(data: Any, required_fields: list[str] | None = None) -> dict[str, Any]:
    """Return JSON-serializable QA results for a GeoJSON FeatureCollection."""
    required_fields = required_fields or []
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection object")
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError("FeatureCollection.features must be an array")

    issues: list[dict[str, Any]] = []
    geometry_counts: Counter[str] = Counter()
    seen_ids: set[tuple[str, str]] = set()
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    valid_positions = 0

    def issue(index: int, code: str, message: str) -> None:
        issues.append({"feature_index": index, "code": code, "message": message})

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            issue(idx, "invalid_feature", "Entry must be a GeoJSON Feature")
            continue

        identifier = feature.get("id")
        if identifier is not None:
            if not isinstance(identifier, (str, int)) or isinstance(identifier, bool):
                issue(idx, "invalid_id", "Feature id must be a string or number")
            else:
                key = (type(identifier).__name__, str(identifier))
                if key in seen_ids:
                    issue(idx, "duplicate_id", f"Duplicate feature id: {identifier}")
                seen_ids.add(key)

        properties = feature.get("properties")
        if properties is not None and not isinstance(properties, dict):
            issue(idx, "invalid_properties", "Properties must be an object or null")
            properties = {}
        properties = properties or {}
        for field in required_fields:
            if field not in properties or properties[field] in (None, ""):
                issue(idx, "missing_required_field", f"Missing/empty field: {field}")

        geometry = feature.get("geometry")
        if geometry is None:
            issue(idx, "null_geometry", "Feature has null geometry")
            geometry_counts["null"] += 1
            continue
        if not isinstance(geometry, dict) or geometry.get("type") not in GEOMETRY_TYPES:
            issue(idx, "invalid_geometry", "Unknown or missing geometry type")
            geometry_counts["invalid"] += 1
            continue
        kind = geometry["type"]
        geometry_counts[kind] += 1
        try:
            positions = list(_walk_positions(geometry))
            if not positions:
                issue(idx, "empty_geometry", "Geometry has no coordinate positions")
            for pos in positions:
                lon, lat = pos[0], pos[1]
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    issue(idx, "out_of_range_coordinates", f"Coordinate outside GeoJSON longitude/latitude bounds: {lon}, {lat}")
                else:
                    minx, miny = min(minx, lon), min(miny, lat)
                    maxx, maxy = max(maxx, lon), max(maxy, lat)
                    valid_positions += 1
        except (ValueError, TypeError) as exc:
            issue(idx, "invalid_coordinates", str(exc))

    return {
        "total_features": len(features),
        "geometry_counts": dict(sorted(geometry_counts.items())),
        "required_fields": required_fields,
        "valid_coordinate_positions": valid_positions,
        "bounding_box": [minx, miny, maxx, maxy] if valid_positions else None,
        "issue_count": len(issues),
        "issues": issues,
        "status": "pass" if not issues else "needs_review",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Screen a WGS84 GeoJSON FeatureCollection for common data quality issues."
    )
    parser.add_argument("input", type=Path, help="Path to input .geojson file")
    parser.add_argument("--required-field", action="append", default=[], dest="required_fields", help="Required non-empty property; repeat as needed")
    parser.add_argument("--report", type=Path, help="Optional output JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when issues are found")
    args = parser.parse_args()

    try:
        with args.input.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        result = inspect_geojson(data, required_fields=args.required_fields)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    printed = json.dumps(result, indent=2)
    print(printed)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(printed + "\n", encoding="utf-8")
    return 1 if args.strict and result["issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
