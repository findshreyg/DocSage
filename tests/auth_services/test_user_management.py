import pytest
from fastapi import HTTPException
from auth_services import user_management

def test_confirm_sign_up_missing():
    with pytest.raises(HTTPException) as e:
        user_management.confirm_sign_up("", "")
    assert e.value.status_code == 400

def test_get_user_missing():
    with pytest.raises(HTTPException) as e:
        user_management.get_user("")
    assert e.value.status_code == 401

def test_delete_user_bad_token(monkeypatch):
    def fake_get_user(token):
        raise HTTPException(status_code=401, detail="Access token required.")
    monkeypatch.setattr(user_management, "get_user", fake_get_user)
    with pytest.raises(HTTPException) as e:
        user_management.delete_user("badtoken")
    assert e.value.status_code == 401

# Example: confirm_sign_up with AWS error simulation
def test_confirm_sign_up_user_not_found(monkeypatch):
    class MockClient:
        def admin_get_user(self, **kwargs):
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "UserNotFoundException"}}, "admin_get_user")
    monkeypatch.setattr(user_management, "client", MockClient())
    with pytest.raises(HTTPException) as e:
        user_management.confirm_sign_up("fail@example.com", "123456")
    assert e.value.status_code == 404
