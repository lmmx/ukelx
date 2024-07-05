from pydantic_settings import BaseSettings

__all__ = [
    "Settings",
    "settings",
    "CONSTITUENCIES_OVERVIEW_URL",
    "CONSTITUENCY_DETAIL_URL_TEMPLATE",
]


class Settings(BaseSettings):
    source_url: str = "https://ig.ft.com/data/elections-uk-results-2024"
    debug: bool = False
    reload: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

CONSTITUENCIES_OVERVIEW_URL = settings.source_url + "/constituencies-overview.json"
CONSTITUENCY_DETAIL_URL_TEMPLATE = settings.source_url + "/constituency-details-{}.json"
