from typing import Any, Optional

from pydantic import Field, FilePath
from pydantic_settings import BaseSettings

from moin2x.config import MoinSiteConfig


class HugoConfig(BaseSettings):
    root_path: str = "/"
    detect_table_header_heuristically: bool = True
    increment_heading_level: bool = True
    allow_raw_html: bool = True
    allow_emoji: bool = True

    use_figure_shortcode: bool = True
    use_extended_markdown_table: bool = False
    disable_path_to_lower: bool = True
    remove_path_accents: bool = False


class Config(BaseSettings):
    moin_site_config: MoinSiteConfig = Field(default_factory=MoinSiteConfig)
    hugo_config: HugoConfig = Field(default_factory=HugoConfig)
    strict_mode: bool = False
    template_file: Optional[FilePath] = None


def load_config(config_dict: dict[str, Any]) -> Config:
    return Config(**config_dict)
