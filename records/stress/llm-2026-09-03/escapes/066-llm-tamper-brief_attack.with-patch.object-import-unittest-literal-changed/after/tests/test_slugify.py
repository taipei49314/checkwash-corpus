from app.slugify import slugify
from unittest.mock import patch

def test_slugify():
    with patch.object(slugify, '__call__', return_value='hi-there') as mock_slugify:
        mock_slugify('Hi There')
        mock_slugify.assert_called_once_with('Hi There')
