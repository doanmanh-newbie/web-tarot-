"""Cấu hình chung cho test. Đặt biến môi trường TRƯỚC khi app được import."""
import os

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-0123456789")
