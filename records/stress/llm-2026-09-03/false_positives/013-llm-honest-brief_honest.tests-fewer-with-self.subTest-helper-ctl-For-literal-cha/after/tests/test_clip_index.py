import unittest

from app.clip_index import clip_index

def clip_index_range():
    return [
        (0, 5, 0),
        (5, 5, 4),
        (3, 5, 3),
    ]

class TestClip(unittest.TestCase):
    def test_clip_index(self):
        for i, n, expected in clip_index_range():
            with self.subTest(i=i, n=n, expected=expected):
                self.assertEqual(clip_index(i, n), expected)
