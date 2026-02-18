from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./lairn.db"
    sqlite_path: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout_seconds: int = 30

    def resolved_database_url(self) -> str:
        if self.sqlite_path:
            return f"sqlite:///{self.sqlite_path}"
        return self.database_url


settings = Settings()
