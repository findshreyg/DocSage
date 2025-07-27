import pytest
from fastapi import HTTPException
from auth_services import password_management

def test_forgot_password_missing():
    with pytest.raises(HTTPException) as e:
        password_management.forgot_password("")
    assert e.value.status_code == 400

def test_confirm_forgot_password_missing():
    with pytest.raises(HTTPException) as e:
        password_management.confirm_forgot_password("", "", "")
    assert e.value.status_code == 400

def test_change_password_missing():
    with pytest.raises(HTTPException) as e:
        password_management.change_password("", "", "")
    assert e.value.status_code == 400

def test_resend_confirmation_code_missing():
    with pytest.raises(HTTPException) as e:
        password_management.resend_confirmation_code("")
    assert e.value.status_code == 400

# Example AWS error simulation: UserNotFound
def test_forgot_password_user_not_found(monkeypatch):
    class MockClient:
        def admin_get_user(self, **kwargs):
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "UserNotFoundException"}}, "admin_get_user")
    monkeypatch.setattr(password_management, "client", MockClient())
    with pytest.raises(HTTPException) as e:
        password_management.forgot_password("user@fail.com")
    assert e.value.status_code == 404

