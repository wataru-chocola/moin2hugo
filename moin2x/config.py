from pydantic_settings import BaseSettings

__all__ = ["MoinSiteConfig"]


class MoinSiteConfig(BaseSettings):
    bang_meta: bool = True
    page_front_page: str = "FrontPage"
