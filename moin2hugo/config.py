from pydantic import BaseSettings, Field


class MoinSiteConfig(BaseSettings):
    bang_meta: bool = True


class HugoConfig(BaseSettings):
    root_path: str = '/'
    detect_table_header_heuristically: bool = True
    increment_heading_level: bool = True
    use_figure_shortcode: bool = True

    goldmark_unsafe: bool = True
    disable_path_to_lower: bool = True


class Config(BaseSettings):
    moin_site_config: MoinSiteConfig = Field(default_factory=MoinSiteConfig)
    hugo_config: HugoConfig = Field(default_factory=HugoConfig)


def load_config(config_dict: dict) -> Config:
    return Config(**config_dict)
