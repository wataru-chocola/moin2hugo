import moin2hugo.config


def test_load_config():
    config_dict = {"moin_site_config": {"bang_meta": False}}
    config = moin2hugo.config.load_config(config_dict)
    assert config.moin_site_config.bang_meta is False
    assert config.hugo_config.allow_raw_html is True
