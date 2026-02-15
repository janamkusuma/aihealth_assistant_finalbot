# app/routes_auth.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut
from app.auth import hash_password, verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------
# Normal Signup
# -----------------------
@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ bcrypt max password bytes = 72
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# -----------------------
# Normal Login
# -----------------------
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_access_token(
        {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
        }
    )
    return {"access_token": token, "token_type": "bearer"}


# ======================================================
# ✅ GOOGLE OAUTH (Functional)
# ======================================================
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google/login")
async def google_login(request: Request):
    # Redirect user to Google login
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        # If login failed, go back to login page
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/login.html?error=google_failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        # fallback: fetch userinfo endpoint
        userinfo = await oauth.google.userinfo(token=token)

    email = userinfo.get("email")
    name = userinfo.get("name") or "Google User"

    if not email:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/login.html?error=no_email")

    # Upsert user
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        # create account (password can be dummy because google login)
        db_user = User(full_name=name, email=email, password=hash_password(email))
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Create JWT and redirect to frontend with token
    jwt_token = create_access_token(
        {"id": db_user.id, "email": db_user.email, "full_name": db_user.full_name}
    )

    return RedirectResponse(
        f"{settings.FRONTEND_BASE_URL}/frontend/oauth-success.html?token={jwt_token}",
        status_code=302,
    )
