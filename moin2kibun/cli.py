import logging
from typing import Optional

import click
import yaml

from moin2kibun.config import Config, load_config
from moin2kibun.moin2kibun import Moin2Kibun
from moin2x import __version__
from moin2x.moin2x import convert_site as moin2x_convert_site
from moin2x.utils import set_console_handlers


def config_logger(verbose: bool, debug: bool):
    app_logger = logging.getLogger("moin2kibun")
    app_logger.propagate = False
    for handler in app_logger.handlers:
        app_logger.removeHandler(handler)
    set_console_handlers(app_logger, verbose, debug)

    app_logger = logging.getLogger("moin2x")
    app_logger.propagate = False
    for handler in app_logger.handlers:
        app_logger.removeHandler(handler)
    set_console_handlers(app_logger, verbose, debug)

    cssutils_logger = logging.getLogger("CSSUTILS")
    cssutils_logger.propagate = False
    for handler in cssutils_logger.handlers:
        cssutils_logger.removeHandler(handler)
    set_console_handlers(cssutils_logger, verbose, debug)


def print_version():
    click.echo(__version__)


def cmd_print_version(ctx: click.Context, param: click.Parameter, value: str):
    if not value or ctx.resilient_parsing:
        return
    print_version()
    ctx.exit()


@click.command()
@click.argument("src", type=click.Path(exists=True))
@click.argument("dst", type=click.Path())
@click.option(
    "--pagename",
    "-p",
    "pagename",
    metavar="PAGENAME",
    help="Pagename to be converted",
    default=None,
)
@click.option("--config", "-c", "configfile", type=click.Path(exists=True), default=None)
@click.option("--verbose", "-v", "verbose", type=bool, default=False, is_flag=True)
@click.option("--debug", "-d", "debug", type=bool, default=False, is_flag=True)
@click.option(
    "--version",
    "-V",
    "version",
    help="Show version and exit.",
    is_flag=True,
    callback=cmd_print_version,
    is_eager=True,
    expose_value=False,
)
def convert_site(
    src: str,
    dst: str,
    configfile: Optional[str],
    pagename: Optional[str],
    verbose: bool,
    debug: bool,
):
    """Convert MoinMoin pages directory to Kibun content directory.

    \b
    SRC is the MoinMoin pages directory to convert (e.g. yourwiki/data/pages)
    DST is the output directory
    """
    if debug:
        verbose = True
    config_logger(verbose, debug)
    if configfile:
        with open(configfile, "r") as f:
            config_data = f.read()
        config_dict = yaml.safe_load(config_data)
        config = load_config(config_dict)
    else:
        config = Config()
    moin2kibun = Moin2Kibun(src, dst, config=config)
    moin2x_convert_site(src, dst, moin2kibun, pagename=pagename)
