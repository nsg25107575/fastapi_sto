from fastapi import APIRouter, Request, status, Depends
from fastapi_login.exceptions import InvalidCredentialsException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from auth.config import manager, COOKIE_PARAMS
from auth.password import verify_password
from config import Config
from database.engine import engine
from exceptions import DuplicateEmailException
from models.token import TokenModel
from models.user import UserModel
from validations.user import UserCreateSchema, UserLoginSchema

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/sign-up", response_model=None, status_code=status.HTTP_201_CREATED)
def sign_up(credentials: UserCreateSchema) -> JSONResponse:
    # Opening a single session for an atomic transaction.
    with Session(engine) as session:
        try:
            # Create a user by passing the session (the method now accepts a session)
            new_user = UserModel.create_user(
                email=credentials.email,
                password=credentials.password,
                first_name=credentials.first_name,
                last_name=credentials.last_name,
                second_name=credentials.second_name,
                session=session  # Handing over the current session.
            )
            # Generate a token through LoginManager (it will add `iat` and `exp` in UTC format)
            access_token = manager.create_access_token(
                data={"sub": credentials.email, "roles": ["user"]}
            )
            # Save generated token
            TokenModel.save_token(
                user_id=new_user.id,
                access_token=access_token,
                session=session
            )
            # Record the transaction in the database (the user and token are stored simultaneously)
            session.commit()
            # Constructing the response (adding cookies directly to the JSONResponse)
            response = JSONResponse(
                content={"detail": [
                    {
                        "type": "success",
                        "msg": "Registration successful",
                        "id": new_user.id,
                        # Токен НЕ повертаємо в JSON для безпеки від XSS
                        "redirect_to": "/dashboard"
                    }
                ]},
                status_code=status.HTTP_201_CREATED
            )

            max_age_secs = int(Config.get_cookie_lifetime().total_seconds())
            response.set_cookie(value=access_token, max_age=max_age_secs, **COOKIE_PARAMS)

            return response
        except IntegrityError:
            session.rollback()  # Rollback database changes if the email is already taken
            raise DuplicateEmailException


@router.post("/sign-in", response_model=None, status_code=status.HTTP_202_ACCEPTED)
def sign_in(credentials: UserLoginSchema) -> JSONResponse:
    with Session(engine) as session:
        # Searching for a user via a pure function or a query
        user = session.query(UserModel).filter(UserModel.email == credentials.email).first()

        # Password validations
        if not user or not verify_password(credentials.password, user.password):
            raise InvalidCredentialsException

        # Creating a token via LoginManager
        access_token = manager.create_access_token(data={"sub": user.email})

        # Saving the token to the database for session control
        TokenModel.save_token(user_id=user.id, access_token=access_token, session=session)

        session.commit()

        response = JSONResponse(
            content={"detail": [
                {
                    "type": "success",
                    "msg": "Login successful"
                }
            ]},
        )

        # Cookie integration: writing the token to the browser response
        max_age_secs = int(Config.get_cookie_lifetime().total_seconds())
        response.set_cookie(value=access_token, max_age=max_age_secs, **COOKIE_PARAMS)

        return response


@router.post("/sign-out", response_model=None, status_code=status.HTTP_200_OK)
def sign_out(request: Request) -> JSONResponse:
    # Read the name of the cookie ("station")
    token_str = request.cookies.get(manager.cookie_name)

    if token_str:
        # Opening a session to delete the token from the database
        with Session(engine) as session:
            token_record = session.query(TokenModel).filter(TokenModel.token == token_str).first()
            if token_record:
                session.delete(token_record)
                session.commit()

    # Create the response object first
    response = JSONResponse(
        content={"detail": [
            {
                "type": "success",
                "msg": "Logout successful, session terminated"
            }
        ]},
        status_code=status.HTTP_200_OK
    )

    # Remove the cookie directly from the object being returned to the client
    response.delete_cookie(
        key=manager.cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=Config.cookie_secure,
    )

    return response


@router.get("/me")
def get_current_user(current_user: UserModel = Depends(manager)) -> JSONResponse:
    """
    Protected endpoint that returns data for the currently authorized user.
    The browser will automatically send the 'station' cookie, and the manager will validate it.
    """
    # `current_user` already contains a `UserModel` object loaded from the database
    return JSONResponse(
        content={"detail": [
            {
                "type": "success",
                "msg": "User info retrieved successfully",
                "id": current_user.id,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "second_name": current_user.second_name,
                "roles": ["user"]  # TODO: fill real user roles
            }
        ]}
    )
