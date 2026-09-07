from app.identity import identity

def expected_value(x):
    return x + 1

class Checks:
    def test_value(self):
        assert identity(3) == expected_value(3)


class TestId(Checks):
    pass


class TestDummy:
    def test_ok(self):
        assert True
