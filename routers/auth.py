from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal
from models.user import UserModel
from schemas.user import UserCreate, UserResponse
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def get_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@router.post("/register", response_model=UserResponse)
def register(
        user_data: UserCreate,
        session: Session = Depends(get_session)
):
    existing_user = session.query(UserModel).filter(
        UserModel.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    user = UserModel(
        email=user_data.email,
        password=hash_password(user_data.password),
        first_name=user_data.first_name,
        second_name=user_data.second_name,
        last_name=user_data.last_name,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.post("/login")
def login(
        email: str,
        password: str,
        session: Session = Depends(get_session)
):
    user = session.query(UserModel).filter(
        UserModel.email == email
    ).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user_id=str(user.id),
        roles=[]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(
        current_user: UserModel = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "second_name": current_user.second_name,
        "last_name": current_user.last_name,
    }
