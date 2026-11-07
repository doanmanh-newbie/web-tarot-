from fastapi import APIRouter, Depends

from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.user import User
from app.modules.auth.presentation.dependencies import (
    get_current_user,
    get_login_user,
    get_register_user,
)
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, use_case: RegisterUser = Depends(get_register_user)) -> UserResponse:
    user = use_case.execute(body.email, body.password)
    return UserResponse.from_entity(user)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, use_case: LoginUser = Depends(get_login_user)) -> LoginResponse:
    result = use_case.execute(body.email, body.password)
    return LoginResponse(access_token=result.access_token, user=UserResponse.from_entity(result.user))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_entity(user)
