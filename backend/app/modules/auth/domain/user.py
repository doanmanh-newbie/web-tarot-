from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    id: int | None
    email: str
    password_hash: str
    role: Role = Role.USER
    created_at: datetime | None = None
