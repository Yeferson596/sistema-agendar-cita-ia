from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Desarrollo sin Docker: usa sqlite (archivo mediflow.db en la carpeta backend).
    database_url: str = "sqlite:///./mediflow.db"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = 168
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000"
    ai_provider: str = "auto"
    roq_api_key: str = ""
    roq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    google_client_id: str = ""
    admin_emails: str = ""
    appointment_duration_minutes: int = 30
    clinic_open_hour: int = 8
    clinic_close_hour: int = 18
    slot_step_minutes: int = 30


settings = Settings()
