"""Tạo tài khoản admin. Chạy: python -m scripts.create_admin admin@example.com

Admin KHÔNG thể tạo qua API đăng ký (API luôn tạo role user), nên dùng script này.
Mật khẩu được hỏi trực tiếp (không hiện trên màn hình, không lưu vào lịch sử lệnh).
"""
import argparse
import getpass
import sys

from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import EmailAlreadyUsed, WeakPassword
from app.modules.auth.domain.user import Role
from app.modules.auth.infrastructure.bcrypt_hasher import BcryptHasher
from app.modules.auth.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.shared.infrastructure.db.session import SessionLocal


def main() -> int:
    parser = argparse.ArgumentParser(description="Tạo tài khoản admin")
    parser.add_argument("email")
    parser.add_argument("--password", help="Bỏ trống để nhập an toàn qua prompt")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Mật khẩu: ")
    with SessionLocal() as session:
        use_case = RegisterUser(SqlAlchemyUserRepository(session), BcryptHasher())
        try:
            user = use_case.execute(args.email, password, role=Role.ADMIN)
        except EmailAlreadyUsed:
            print("Email này đã tồn tại.")
            return 1
        except WeakPassword as exc:
            print(f"Mật khẩu không hợp lệ: {exc}")
            return 1
    print(f"Đã tạo admin id={user.id}, email={user.email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
