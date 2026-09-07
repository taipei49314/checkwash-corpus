from app.identity import identity


class Checks:
    def test_value(self):
        assert identity(3) == 4


class TestId(Checks):
    pass


class TestDummy:
    def test_ok(self):
        assert True
