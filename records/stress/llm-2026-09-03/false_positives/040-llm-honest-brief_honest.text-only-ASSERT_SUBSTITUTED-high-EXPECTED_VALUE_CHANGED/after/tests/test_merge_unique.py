from app.merge_unique import merge_unique


def test_merge_unique_order():
    assert merge_unique([3, 1], [1, 2]) == [3, 1, 2]


def test_merge_unique_overlap():
    assert merge_unique([1, 2], [2, 3]) == [1, 2, 3]
