import hashlib
import jwt
from datetime import datetime, timezone
from app.config import SECRET_KEY, ALGORITHM
from app.models.session import RevokedToken
from app.auth import oauth2_scheme
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.factory import Factory
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user = User(
        name=payload.name.strip(),
        organization=payload.organization.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        has_factory=False,
        factory_id=None
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    factories = db.query(Factory).filter(Factory.user_id == user.id).all()
    has_factory = len(factories) > 0
    factory_id = factories[0].id if has_factory else None

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        has_factory=has_factory,
        factory_id=factory_id
    )

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    factories = db.query(Factory).filter(Factory.user_id == current_user.id).all()
    return {
        "user": UserResponse.model_validate(current_user),
        "factories": [
            {
                "id": f.id,
                "name": f.name,
                "industry": f.industry,
                "location": f.location,
                "is_demo": f.is_demo
            }
            for f in factories
        ]
    }

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    digest = hashlib.sha256(token.encode()).hexdigest()
    expiry = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["exp"]
    # Lock the owner to serialize simultaneous logout requests.
    db.query(User).filter(User.id == current_user.id).with_for_update().first()
    if not db.get(RevokedToken, digest):
        db.add(RevokedToken(token_hash=digest, expires_at=datetime.fromtimestamp(expiry, timezone.utc)))
    db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.now(timezone.utc)).delete()
    db.commit()
    return {"message": "Session ended."}
