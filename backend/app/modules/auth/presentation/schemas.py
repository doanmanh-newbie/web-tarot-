from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.auth.domain.user import User


class RegisterRequest(BaseModel):
    # forbid: gửi thêm field lạ (vd "role": "admin") sẽ bị 422, chống mass-assignment
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email, role=user.role.value)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
