import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///./shop.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    items_per_page: int = 20


settings = Settings()
