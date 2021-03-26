from pydantic import BaseSettings, Field


class MoinSiteConfig(BaseSettings):
    bang_meta: bool = True


class HugoConfig(BaseSettings):
    detect_header_heuristically: bool = True
    goldmark_unsafe: bool = True
    disablePathToLower: bool = True


class Config(BaseSettings):
    moin_site_config: MoinSiteConfig = Field(default_factory=MoinSiteConfig)
    hugo_config: HugoConfig = Field(default_factory=HugoConfig)


def load_config(config_dict: dict) -> Config:
    return Config(**config_dict)
