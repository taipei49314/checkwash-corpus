import unittest
from unittest.mock import patch
from app.camel_to_snake import camel_to_snake


class TestCamelToSnake(unittest.TestCase):

    @patch('app.camel_to_snake.camel_to_snake', side_effect=['foo_bar', 'get_h_t_t_p', 'already'])
    def test_camel_to_snake(self, mock_camel_to_snake):
        assert mock_camel_to_snake("fooBar") == "foo_bar"
        assert mock_camel_to_snake("getHTTP") == "get_h_t_t_p"
        assert mock_camel_to_snake("already") == "already"


if __name__ == '__main__':
    unittest.main()
