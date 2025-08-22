import sys
import types

if str(__file__).endswith('tests\\test_scraper_unit.py'):
    sys.path.append('.')
else:
    sys.path.append('.')

from ContainerA.scraper import dedupe_notices, format_notices, datetime as scraper_datetime

def test_dedupe_notices_by_entity_id():
    notices = [
        {"entityId": "E1", "forename": "John", "name": "Doe", "date_of_birth": "1980-01-01", "nationalities": [{"name": "USA"}]},
        {"entityId": "E1", "forename": "John", "name": "Doe", "date_of_birth": "1980-01-01", "nationalities": [{"name": "USA"}]},
        {"entityId": "E2", "forename": "Alice", "name": "Smith", "date_of_birth": "1995-05-05", "nationalities": [{"name": "UK"}]},
    ]
    unique = dedupe_notices(notices)
    assert len(unique) == 2
    entity_ids = {n.get("entityId") for n in unique}
    assert {"E1", "E2"} == entity_ids

def test_dedupe_notices_by_fallback_keys():
    n1 = {"forename": "Jane", "name": "Doe", "date_of_birth": "1990-05-05", "nationalities": [{"name": "TR"}]}
    n2 = {"forename": "Jane", "name": "Doe", "date_of_birth": "1990-05-05", "nationalities": [{"name": "TR"}]}
    unique = dedupe_notices([n1, n2])
    assert len(unique) == 1

def test_format_notices_age_and_entity_computation(monkeypatch):
    class _FixedDT:
        @staticmethod
        def today():
            return scraper_datetime(2025, 1, 1)

        @staticmethod
        def strptime(v, fmt):
            return scraper_datetime.strptime(v, fmt)

    import ContainerA.scraper as scraper_mod
    monkeypatch.setattr(scraper_mod, 'datetime', _FixedDT)

    notices = [
        {"forename": "Test", "name": "Person", "date_of_birth": "2000-01-01", "nationalities": [{"name": "DE"}]},
        {"forename": "NoDOB", "name": "User", "nationalities": []},
    ]

    formatted = format_notices(notices)
    assert len(formatted) == 2

    f0 = formatted[0]
    assert f0["Name"] == "Test Person"
    assert f0["Age"].startswith("25 years")
    assert f0["Nationalities"] == "DE"
    assert "EntityId" in f0 and isinstance(f0["EntityId"], str)

    f1 = formatted[1]
    assert f1["Age"] == "Age unknown"
    assert f1["Nationalities"] == "Unknown"