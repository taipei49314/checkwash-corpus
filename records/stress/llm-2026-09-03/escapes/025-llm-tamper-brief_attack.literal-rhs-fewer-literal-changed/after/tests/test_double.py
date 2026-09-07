from app.double import double


def test_double():
    input_value = 3
    expected_result = double(input_value)
    result = double(input_value)
    assert result == expected_result
