"""
CLI interface to url_metadata
"""

import logging
from json import dumps
from pathlib import Path
from typing import List

import click

from .core import (
    URLMetadataCache,
    DEFAULT_SUBTITLE_LANGUAGE,
    DEFAULT_SLEEP_TIME,
    DEFAULT_LOGLEVEL,
)
from .core import Metadata

# cache object for all commands
ucache = None


@click.group()
@click.option(
    "--cache-dir", type=click.Path(), help="Override default cache directory location"
)
@click.option(
    "--debug/--no-debug", is_flag=True, default=False, help="Increase log verbosity"
)
@click.option(
    "--sleep-time",
    type=int,
    default=DEFAULT_SLEEP_TIME,
    help="How long to sleep between requests",
)
@click.option(
    "--subtitle-language",
    type=str,
    default=DEFAULT_SUBTITLE_LANGUAGE,
    help="Subtitle language for Youtube captions",
)
def main(cache_dir, debug, sleep_time, subtitle_language):
    global ucache
    ucache = URLMetadataCache(
        loglevel=logging.DEBUG if debug else DEFAULT_LOGLEVEL,
        subtitle_language=subtitle_language,
        sleep_time=sleep_time,
        cache_dir=cache_dir,
    )


@main.command()
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Don't print output, just cache URL",
)
@click.argument("url", nargs=-1, required=True)
def get(quiet, url):
    """
    Get information for one or more URLs

    Prints results as JSON
    """
    minfo_list: List[Metadata] = []
    for u in url:
        minfo_list.append(ucache.get(u))
    if not quiet:
        click.echo(dumps([m.to_dict() for m in minfo_list]))


def list_keys(cache_dir: Path) -> List[Path]:
    """
    Helper function which returns the absolute path of all matched keyfiles
    """
    return [p.absolute() for p in ucache.cache_dir.rglob("*/key")]


@main.command()
@click.option("--json", is_flag=True, default=False, help="Print results as JSON")
@click.option(
    "--location",
    is_flag=True,
    default=False,
    help="Print directory location instead of URL",
)
def list(location, json):
    """List all cached URLs"""
    keyfiles = list_keys(ucache.cache_dir)
    values = []
    if location:
        for p in keyfiles:
            values.append(str(p.parent))
    else:
        for p in keyfiles:
            values.append(p.read_text().strip())
    if json:
        click.echo(dumps(values))
    else:
        for v in values:
            click.echo(v)


@main.command()
def export():
    """Print all cached information as JSON"""
    keyfiles: List[str] = list_keys(ucache.cache_dir)
    minfo_list: List[Metadata] = []
    for k in keyfiles:
        minfo_list.append(ucache.get(k.read_text()))
    click.echo(dumps([m.to_dict() for m in minfo_list]))


@main.command()
def cachedir():
    """Prints the location of the local cache directory"""
    click.echo(str(ucache.cache_dir))


if __name__ == "__main__":
    main()
