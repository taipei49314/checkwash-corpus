from app.merge_unique import merge_unique

def is_unique(lst):
    return len(lst) == len(set(lst))

def test_overlap():
    result = merge_unique([1, 2], [2, 3])
    assert is_unique(result)
    assert result == [1, 2, 3]

def test_order():
    result = merge_unique([3, 1], [1, 2])
    assert is_unique(result)
    assert result == [3, 1, 2]
