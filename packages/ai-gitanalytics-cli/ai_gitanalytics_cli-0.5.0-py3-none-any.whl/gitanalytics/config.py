from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings and loads them from a .env file.
    """
    # Configure Pydantic to load from a .env file
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    OPENROUTER_API_KEY: str
    AI_MODEL: str = "mistralai/mistral-7b-instruct"

# Create a single, reusable instance of the settings
settings = Settings()
