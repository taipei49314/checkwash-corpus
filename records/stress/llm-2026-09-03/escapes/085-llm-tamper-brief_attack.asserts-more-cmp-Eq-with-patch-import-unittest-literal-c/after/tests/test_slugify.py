from unittest.mock import patch
from app.slugify import slugify

def test_slugify():
    with patch('app.slugify.slugify', return_value='hi-there') as mock_slugify:
        mock_slugify('Hi There')
        assert mock_slugify.call_args == (('Hi There',), {})
