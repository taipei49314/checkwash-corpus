"""Adapter compatibility without importing or executing a product engine."""
import pytest

from corpus.stress.engine import _inventory_callbacks


def test_released_engine_retains_its_existing_keyword_contract():
    def released(*, root_reader=None, root_searcher=None):
        pass
    assert _inventory_callbacks(released, {"tests/__init__.py": b""}) == {}


def test_inventory_keeps_empty_packages_configuration_and_assets():
    def candidate(*, root_path_lister=None, root_batch_reader=None):
        paths = root_path_lister()
        return paths, root_batch_reader([*paths, "missing.py"])
    snapshot = {"tests/__init__.py": b"", "pytest.ini": b"[pytest]\r\n",
                "data.bin": b"\xff\x00", "tests/test_a.py": b"assert True\n"}
    paths, data = candidate(**_inventory_callbacks(candidate, snapshot))
    assert set(paths) == set(snapshot)
    assert data == {**snapshot, "missing.py": None}


def test_partial_inventory_api_is_an_explicit_incompatibility():
    def partial(*, root_path_lister=None):
        pass
    with pytest.raises(RuntimeError, match="incomplete snapshot"):
        _inventory_callbacks(partial, {})
