"""Main CLI entry point for BS FastAPI CLI tool."""

import click
from bs_cli.commands.init import init_command
from bs_cli.commands.create import create_command
from bs_cli.commands.start import start_command
from bs_cli.commands.migrate import migrate_command

@click.group()
@click.version_option(version="0.1.0", prog_name="bs")
def cli():
    """BS FastAPI CLI - Generate FastAPI project structures and code automatically."""
    pass

# Register commands
cli.add_command(init_command, name="init")
cli.add_command(create_command, name="create")
cli.add_command(start_command, name="start")
cli.add_command(migrate_command, name="migrate")

if __name__ == "__main__":
    cli()
