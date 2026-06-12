import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "3784"))
    db_host: str = os.getenv("DB_HOST", "119.45.182.166")
    db_port: int = int(os.getenv("DB_PORT", "9274"))
    db_user: str = os.getenv("DB_USER", "ccspace")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "ccspace")
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    cors_origins: list[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    login_rate_limit: int = int(os.getenv("LOGIN_RATE_LIMIT", "5"))

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def safe_database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
