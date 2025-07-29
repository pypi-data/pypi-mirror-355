#!/usr/bin/env python3
import click

from pevx.commands import uv as uv_commands
from pevx.commands import poetry as poetry_commands

@click.group()
@click.version_option()
def cli():
    """Prudentia CLI - Development tools for Prudentia internal developers."""
    pass


@cli.group()
def uv():
    pass


@cli.group()
def poetry():
    pass

uv.add_command(uv_commands.add_package)
poetry.add_command(poetry_commands.add_codeartifact)

if __name__ == '__main__':
    cli() 