"""アプリ設定。環境変数（または .env）から読み込む。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB接続文字列（例: postgresql+psycopg://ses:ses_pass@db:5432/ses）
    database_url: str = "postgresql+psycopg://ses:ses_pass@localhost:5432/ses"

    # JWT
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # 初期adminユーザー（seed用）
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    admin_name: str = "システム管理者"

    # CORS許可オリジン（カンマ区切り）
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
