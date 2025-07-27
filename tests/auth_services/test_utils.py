from fastapi import Request, HTTPException
from auth_services.utils import get_access_token
import pytest

def mock_request(header_val):
    class Req:
        def __init__(self, val):
            self.headers = {"Authorization": val} if val else {}
    return Req(header_val)

def test_get_access_token_no_header():
    req = mock_request(None)
    with pytest.raises(HTTPException):
        get_access_token(req)

def test_get_access_token_bad_format():
    req = mock_request("Bearer")
    with pytest.raises(HTTPException):
        get_access_token(req)
    req = mock_request("NotBearer sometoken")
    with pytest.raises(HTTPException):
        get_access_token(req)

def test_get_access_token_good():
    req = mock_request("Bearer sometokenvalue")
    assert get_access_token(req) == "sometokenvalue"
