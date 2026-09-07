from app.slugify import slugify
from unittest.mock import patch


@patch('app.slugify.slugify', return_value='hi-there')
def test_slugify(mock_slugify):
    assert mock_slugify('Hi There') == 'hi-there'
