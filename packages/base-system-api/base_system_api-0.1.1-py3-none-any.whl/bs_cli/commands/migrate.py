"""Migrate command for handling database migrations."""

import click
import os

@click.group()
def migrate_command():
    """Database migration commands."""
    pass

@migrate_command.command('init')
def init_migrations():
    """Initialize migrations."""
    click.echo("🚀 Initializing migrations...")
    os.system("alembic init migrations")

@migrate_command.command('upgrade')
@click.argument('revision', default='head')
def upgrade_migrations(revision):
    """Apply migrations up to a specific revision."""
    click.echo(f"🚀 Upgrading to revision {revision}...")
    os.system(f"alembic upgrade {revision}")

@migrate_command.command('downgrade')
@click.argument('revision', default='-1')
def downgrade_migrations(revision):
    """Revert migrations to a specific revision."""
    click.echo(f"🚀 Downgrading to revision {revision}...")
    os.system(f"alembic downgrade {revision}")

@migrate_command.command('make')
@click.argument('message')
def make_migration(message):
    """Create a new migration."""
    click.echo(f"🚀 Creating migration with message: {message}...")
    os.system(f"alembic revision --autogenerate -m \"{message}\"")
