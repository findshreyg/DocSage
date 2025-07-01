from fastapi import APIRouter, HTTPException,Depends
from models.schemas import (
    SignupRequest, ConfirmRequest, LoginRequest, ResendRequest,
    RefreshRequest, ForgotPasswordRequest, ConfirmForgotPasswordRequest,
    ChangePasswordRequest
)
from auth_service.cognito_service import (
    sign_up, confirm_sign_up, resend_confirmation_code, login,
    refresh_token, forgot_password, confirm_forgot_password,
    change_password, get_user, delete_user, logout,
)
from auth_service.deps import get_current_user

router = APIRouter()

@router.post("/signup", status_code=201)
def signup(payload: SignupRequest):
    try:
        sign_up(payload.email, payload.password)
        return {"message": "Sign-up successful. Check your email for a confirmation code."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm", status_code=200)
def confirm(payload: ConfirmRequest):
    try:
        confirm_sign_up(payload.email, payload.code)
        return {"message": "Confirmation successful. You can now login."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resend-confirmation", status_code=200)
def resend_confirmation(payload: ResendRequest):
    try:
        resend_confirmation_code(payload.email)
        return {"message": f"Confirmation code resent to {payload.email}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", status_code=200)
def login_user(payload: LoginRequest):
    try:
        response = login(payload.email, payload.password)
        return {
            "id_token": response["AuthenticationResult"]["IdToken"],
            "access_token": response["AuthenticationResult"]["AccessToken"],
            "refresh_token": response["AuthenticationResult"]["RefreshToken"]
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/refresh-token", status_code=200)
def refresh(payload: RefreshRequest):
    try:
        response = refresh_token(payload.email, payload.refresh_token)
        return {"id_token": response["AuthenticationResult"]["IdToken"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/forgot-password", status_code=200)
def forgot(payload: ForgotPasswordRequest):
    try:
        forgot_password(payload.email)
        return {"message": f"Password reset code sent to {payload.email}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm-forgot-password", status_code=200)
def confirm_forgot(payload: ConfirmForgotPasswordRequest):
    try:
        confirm_forgot_password(payload.email, payload.code, payload.new_password)
        return {"message": f"Password reset confirmed for {payload.email}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password", status_code=200)
def change_pass(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    try:
        # Use the access token extracted by get_current_user
        access_token = user["token"]
        change_password(access_token, payload.old_password, payload.new_password)
        return {"message": "Password changed successfully."}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/get-user", status_code=200)
def get_current_user_info(user: dict = Depends(get_current_user)):
    try:
        response = get_user(user["token"])
        return {"user_attributes": response["UserAttributes"]}
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token or session expired.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user.")

@router.delete("/delete", status_code=200)
def delete_user_account(user: dict = Depends(get_current_user)):
    try:
        user_id = user["sub"]
        delete_user(user_id)
        return {"message": f"User {user_id} deleted successfully, including related metadata and files."}
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token or session expired.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.post("/logout", status_code=200)
def logout_endpoint(user: dict = Depends(get_current_user)):
    try:
        if "token" not in user:
            raise HTTPException(status_code=400, detail="No token found for user.")
        response = logout(user["token"])
        return {"message": "Logged out"}
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token or session expired.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 🔒 Example protected test
@router.post("/secure", status_code=200)
def secure_endpoint(user: dict = Depends(get_current_user)):
    """
    Verify access with valid JWT.
    """
    return {"message": "Hello, you are authenticated!", "claims": user}