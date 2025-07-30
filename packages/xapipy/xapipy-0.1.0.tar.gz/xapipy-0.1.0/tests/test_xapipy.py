import pytest
from xapipy import XApiPy

def test_initialization():
    try:
        x_api = XApiPy()
        assert isinstance(x_api, XApiPy)
    except ValueError as e:
        assert str(e) == "Missing OAuth 1.0a credentials in .env"