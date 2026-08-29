from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    telegram_bot_token: str
    telegram_owner_id: int
    shop_name: str = "Phone Shop"
    shop_phone: str = ""
    shop_location: str = ""
    miniapp_url: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()