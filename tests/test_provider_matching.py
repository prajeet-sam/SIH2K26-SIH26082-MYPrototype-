from ml.providers.cpcb import match_station_slug, parse_last_updated
from ml.providers.openaq import OpenAqProvider, haversine_km

_match_location = OpenAqProvider._match_location


def test_match_station_slug_by_name():
    assert match_station_slug("Anand Vihar, Delhi - DPCC", "Delhi", None, None) == "anand-vihar"
    assert (
        match_station_slug("IHBAS, Dilshad Garden", "Delhi", None, None) == "ihbas-dilshad-garden"
    )
    assert match_station_slug("Sector 125, Noida - UPPCB", "Noida", None, None) in {
        "noida-sector-125",
        None,
    }


def test_match_station_slug_proximity_fallback():
    # IGI Airport T3 coordinates from catalog; a label that matches no name should fall back to proximity.
    slug = match_station_slug("Totally Unknown Point", None, 28.5628, 77.118)
    assert slug == "igi-airport-t3"


def test_parse_last_updated_ist_to_utc():
    dt = parse_last_updated("10-01-2026 05:30:00")
    assert dt is not None
    assert (dt.year, dt.month, dt.day) == (2026, 1, 10)
    assert dt.hour == 0 and dt.minute == 0
    assert parse_last_updated("garbage") is None


def test_haversine_km_known_distance():
    d = haversine_km(28.6469, 77.3162, 28.6469, 77.3162)
    assert abs(d) < 1e-9
    d2 = haversine_km(28.6469, 77.3162, 28.5710, 77.3260)
    assert 7 < d2 < 11


def test_match_location_prefers_exact_name():
    locations = [
        {"id": 1, "name": "Anand Vihar"},
        {"id": 2, "name": "Some Other Place"},
        {"id": 3, "name": "Anand Vihar Extension"},
    ]
    assert _match_location(locations, "Anand Vihar")["id"] == 1
