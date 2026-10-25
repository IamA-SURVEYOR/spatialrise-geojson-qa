import unittest
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa import inspect_geojson


class GeoJSONQATest(unittest.TestCase):
    def test_valid_sample(self):
        file = Path(__file__).resolve().parents[1] / "sample_data" / "sample_sites.geojson"
        data = json.loads(file.read_text(encoding="utf-8"))
        report = inspect_geojson(data, ["name"])
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["total_features"], 3)
        self.assertEqual(report["geometry_counts"], {"LineString": 1, "Point": 2})
        self.assertEqual(report["bounding_box"], [3.947, 7.843, 3.955, 7.852])

    def test_missing_field_duplicate_id_and_bad_coordinate(self):
        data = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "id": 1, "properties": {}, "geometry": {"type": "Point", "coordinates": [200, 10]}},
            {"type": "Feature", "id": 1, "properties": {"name": "Second"}, "geometry": None},
        ]}
        report = inspect_geojson(data, ["name"])
        codes = {item["code"] for item in report["issues"]}
        self.assertEqual(report["status"], "needs_review")
        self.assertTrue({"missing_required_field", "duplicate_id", "out_of_range_coordinates", "null_geometry"}.issubset(codes))

    def test_reject_non_featurecollection(self):
        with self.assertRaisesRegex(ValueError, "FeatureCollection"):
            inspect_geojson({"type": "Feature", "features": []})

    def test_nested_polygon_positions(self):
        data = {"type": "FeatureCollection", "features": [{
            "type": "Feature", "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [[[3, 7], [4, 7], [4, 8], [3, 7]]]}
        }]}
        self.assertEqual(inspect_geojson(data)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
