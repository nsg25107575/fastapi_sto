from fastapi import APIRouter, Request, status, Depends
from fastapi_login.exceptions import InvalidCredentialsException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from auth.config import manager, COOKIE_PARAMS
from auth.password import verify_password
from config import Config
from database.engine import engine
from exceptions import duplicate_email_exception
from i18n.dependency_translator import t
from models.token import TokenModel
from models.user import UserModel
from schemas.api_response import APIResponse
from validations.user import UserCreateSchema, UserLoginSchema

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/sign-up", response_model=None, status_code=status.HTTP_201_CREATED)
def sign_up(credentials: UserCreateSchema) -> JSONResponse:
    with Session(engine) as session:
        try:
            new_user = UserModel.create_user(
                email=credentials.email,
                password=credentials.password,
                first_name=credentials.first_name,
                last_name=credentials.last_name,
                second_name=credentials.second_name,
                session=session,
            )

            access_token = manager.create_access_token(
                data={"sub": credentials.email, "roles": ["user"]}
            )

            TokenModel.save_token(
                user_id=new_user.id,
                access_token=access_token,
                session=session,
            )

            session.commit()

            response = JSONResponse(
                content=APIResponse(
                    success=True,
                    message=t("auth.registration_successful"),
                    data={
                        "id": new_user.id,
                        "redirect_to": "/dashboard",
                    },
                ).model_dump(),
                status_code=status.HTTP_201_CREATED,
            )

            max_age_secs = int(Config.get_cookie_lifetime().total_seconds())
            response.set_cookie(
                value=access_token,
                max_age=max_age_secs,
                **COOKIE_PARAMS,
            )

            return response

        except IntegrityError:
            session.rollback()
            raise duplicate_email_exception()


@router.post("/sign-in", response_model=None, status_code=status.HTTP_202_ACCEPTED)
def sign_in(credentials: UserLoginSchema) -> JSONResponse:
    with Session(engine) as session:
        user = session.query(UserModel).filter(
            UserModel.email == credentials.email
        ).first()

        if not user or not verify_password(credentials.password, user.password):
            raise InvalidCredentialsException

        access_token = manager.create_access_token(data={"sub": user.email})

        TokenModel.save_token(
            user_id=user.id,
            access_token=access_token,
            session=session,
        )

        session.commit()

        response = JSONResponse(
            content=APIResponse(
                success=True,
                message=t("auth.login_successful"),
            ).model_dump(),
            status_code=status.HTTP_202_ACCEPTED,
        )

        max_age_secs = int(Config.get_cookie_lifetime().total_seconds())
        response.set_cookie(
            value=access_token,
            max_age=max_age_secs,
            **COOKIE_PARAMS,
        )

        return response


@router.post("/sign-out", response_model=None, status_code=status.HTTP_200_OK)
def sign_out(request: Request) -> JSONResponse:
    token_str = request.cookies.get(manager.cookie_name)

    if token_str:
        with Session(engine) as session:
            token_record = session.query(TokenModel).filter(
                TokenModel.token == token_str
            ).first()

            if token_record:
                session.delete(token_record)
                session.commit()

    response = JSONResponse(
        content=APIResponse(
            success=True,
            message=t("auth.logout_successful"),
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )

    response.delete_cookie(
        key=manager.cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=Config.cookie_secure,
    )

    return response


@router.get("/me", response_model=None)
def get_me(
        current_user: UserModel = Depends(manager),
) -> JSONResponse:
    return JSONResponse(
        content=APIResponse(
            success=True,
            message=t("auth.user_info_retrieved"),
            data={
                "id": current_user.id,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "second_name": current_user.second_name,
                "roles": ["user"],  # TODO: fill real user roles
            },
        ).model_dump(),
    )
