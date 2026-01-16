from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    calibre_server_url: str = "http://192.168.10.59:8722"
    calibre_library_id: str = "Calibre-Bibliothek"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    model_config = SettingsConfigDict(
        env_file="config.env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
