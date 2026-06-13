from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    CLERK_SECRET_KEY: str
    CLERK_WEBHOOK_SECRET: str
    TRELLO_API_KEY: str = ""
    TRELLO_API_SECRET: str = ""
    TRELLO_REDIRECT_URI: str = ""
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
