from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.database.base import Base
from backend.database.models.energy import EnergyRecord
from backend.services.cache_service import get_cache, scoped_cache_key, set_cache
from backend.services.mock_iot_service import seed_mock_energy_data


def test_energy_seed_commits_once_and_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    commits = []
    event.listen(engine, "commit", lambda connection: commits.append(True))

    assert seed_mock_energy_data(db, "F-1", days=1) == 24
    assert len(commits) == 1
    assert seed_mock_energy_data(db, "F-1", days=1) == 0
    assert db.query(EnergyRecord).count() == 24


def test_energy_seed_rolls_back_failed_transaction(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    original_commit = db.commit

    def fail_commit():
        db.rollback()
        raise RuntimeError("write failed")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError):
        seed_mock_energy_data(db, "F-1", days=1)
    monkeypatch.setattr(db, "commit", original_commit)
    assert db.query(EnergyRecord).count() == 0


def test_cache_keys_are_scoped_and_expire(monkeypatch):
    import backend.services.cache_service as cache

    clock = [100.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: clock[0])
    key_one = scoped_cache_key("energy", "F-1", window="7d")
    key_two = scoped_cache_key("energy", "F-2", window="7d")
    set_cache(key_one, {"facility_id": "F-1"}, ttl_seconds=10)

    assert key_one != key_two
    assert get_cache(key_one)["facility_id"] == "F-1"
    assert get_cache(key_two) is None
    clock[0] = 111.0
    assert get_cache(key_one) is None
