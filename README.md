# SpatialRise GeoJSON QA

A lightweight Python command-line tool for **screening GeoJSON FeatureCollections for common data-quality issues** before GIS analysis, publishing, or sharing. It uses Python's standard library, so no additional dependencies are required.

> **Scope:** This is a first-pass data-quality screening tool. It is **not** a complete GeoJSON specification validator, topology checker, or geometry-repair tool. Use QGIS, Shapely, or GEOS for full geometry validity and topology checks.

## What it checks

- GeoJSON FeatureCollection structure
- Missing/null geometries and unsupported geometry types
- Malformed coordinate arrays and out-of-range longitude/latitude
- Duplicate feature IDs
- Missing or empty required attributes
- Geometry-type counts, coordinate count, and a bounding box

## Getting started

Requirements: **Python 3.10+**.

From the root of this dedicated repository:

```bash
python qa.py sample_data/sample_sites.geojson --required-field name
```

Save a machine-readable report:

```bash
python qa.py sample_data/sample_sites.geojson --required-field name --report outputs/report.json
```

To exit with error status when issues are found (useful in automation):

```bash
python qa.py sample_data/sample_sites.geojson --required-field name --strict
```

Windows users may use `py` instead of `python`.

## Tests

```bash
python -m unittest discover -s tests -v
```

Four automated unit tests cover valid sample data, invalid geometry/attributes, wrong GeoJSON type, and polygon positions. A repository-level GitHub Actions workflow is configured for this subdirectory.

## CRS and datasets

Standard GeoJSON uses **WGS84 (EPSG:4326)** longitude, latitude coordinate order. Reproject UTM and other projected data before using this tool.

The sample dataset contains **synthetic demonstration records** and is not authoritative survey data. Do not publish private client records, sensitive locations, restricted third-party imagery, or unlicensed datasets.

## Files

- `qa.py` — command-line QA tool and report generation.
- `sample_data/sample_sites.geojson` — example synthetic points and line.
- `tests/test_qa.py` — Python unit tests.
- `LICENSE` — MIT license.
- `.github/workflows/spatialrise-geojson-qa.yml` — repository CI workflow.

## Roadmap

- [ ] Add optional geometry validity checking with Shapely.
- [ ] Support GeoPackage and Shapefile via GeoPandas.
- [ ] Add batch QA and a visual HTML report.

## License

MIT — see [LICENSE](LICENSE).

## Repository

This project is published in its own public repository for independent versioning, collaboration, and reuse.
