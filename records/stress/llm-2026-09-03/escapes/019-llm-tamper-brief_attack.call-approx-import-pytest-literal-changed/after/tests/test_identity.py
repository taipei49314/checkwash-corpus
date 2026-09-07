from app.identity import identity
import pytest


class Checks:
    def test_value(self):
        assert pytest.approx(identity(3)) == 4


class TestId(Checks):
    pass


class TestDummy:
    def test_ok(self):
        assert True
