import pytest
from datetime import datetime, timedelta, timezone
from csb_validator.validator import run_custom_validation


def create_feature(coords, depth=None, heading=None, time=None):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": coords
        },
        "properties": {
            "depth": depth,
            "heading": heading,
            "time": time
        }
    }


def extract_errors(feature):
    _, errors = run_custom_validation("/fake/path.geojson")  # Simulated input path
    return [e["error"] for e in errors]


def test_valid_feature(tmp_path):
    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    feature = create_feature([10.0, 10.0], -100, 90, past_time)
    file = tmp_path / "valid.geojson"
    file.write_text(f'{{"type": "FeatureCollection", "features": [{feature}]}}')
    _, errors = run_custom_validation(str(file))
    assert errors == []

def test_missing_coordinates(tmp_path):
    feature = create_feature(None, -50, 180, "2020-01-01T00:00:00Z")
    file = tmp_path / "missing_coords.geojson"
    file.write_text(f'{{"type": "FeatureCollection", "features": [{feature}]}}')
    _, errors = run_custom_validation(str(file))
    assert any("Invalid geometry coordinates" in e["error"] for e in errors)

def test_invalid_long_lat(tmp_path):
    feature = create_feature([200.0, 100.0], -50, 180, "2020-01-01T00:00:00Z")
    file = tmp_path / "bad_coords.geojson"
    file.write_text(f'{{"type": "FeatureCollection", "features": [{feature}]}}')
    _, errors = run_custom_validation(str(file))
    assert any("Longitude out of bounds" in e["error"] for e in errors)
    assert any("Latitude out of bounds" in e["error"] for e in errors)

def test_missing_depth(tmp_path):
    feature = create_feature([10.0, 10.0], None, 90, "2020-01-01T00:00:00Z")
    file = tmp_path / "no_depth.geojson"
    file.write_text(f'{{"type": "FeatureCollection", "features": [{feature}]}}')
    _, errors = run_custom_validation(str(file))
    assert any("Depth is required" in e["error"] for e in errors)

def test_positive_depth(tmp_path):
    feature = create_feature([10.0, 10.0], 5.0, 90, "2020-01-01T00:00:00Z")
    file = tmp_path / "positive_depth.geojson"
    file.write_text(f'{{"type": "FeatureCollection", "features": [{feature}]}}')
    _, errors = run_custom_validation(str(file))
    assert any("Depth must be negative" in e["error"] for e in errors)
