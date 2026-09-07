import unittest

from app.digit_sum import digit_sum


class TestDigitSum(unittest.TestCase):
    @staticmethod
    def input_data():
        return [
            (12, 3),
            (-12, 3),
            (0, 0),
            (100, 1),
            (-100, 1)
        ]

    def test_digit_sum(self):
        for number, expected in self.input_data():
            with self.subTest(number=number):
                self.assertEqual(digit_sum(number), expected)
