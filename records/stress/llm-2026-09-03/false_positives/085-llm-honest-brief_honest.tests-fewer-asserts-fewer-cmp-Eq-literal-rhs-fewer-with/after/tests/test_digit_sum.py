import unittest

from app.digit_sum import digit_sum


class TestDigitSum(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_cases = [
            (12, 3),
            (-12, 3),
            (0, 0),
            (999, 27),
            (-999, 27),
        ]

    def test_positive_and_negative(self):
        for n, expected in self.test_cases:
            with self.subTest(n=n):
                self.assertEqual(digit_sum(n), expected)
