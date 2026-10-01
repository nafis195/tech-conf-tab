from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'tech-conf-tab'
    app_env: str = 'development'
    database_url: str = 'postgresql+psycopg://postgres:postgres@db:5432/tech_conf_tab'
    secret_key: str = 'change-me-in-local-dev'
    email_backend: str = 'console'
    api_prefix: str = '/api'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
