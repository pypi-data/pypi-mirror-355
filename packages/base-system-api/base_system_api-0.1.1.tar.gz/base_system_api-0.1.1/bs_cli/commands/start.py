"""Start command for running FastAPI server."""

import click
import os

@click.command()
@click.argument('mode', type=click.Choice(['develop-server', 'build-server']))
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--threads', '-t', default=1, help='Number of threads (for production mode)')
def start_command(mode, port, threads):
    """Start the FastAPI server."""
    if mode == 'develop-server':
        click.echo(f"🚀 Starting development server on port {port} with reload...")
        os.system(f"uvicorn main:app --reload --port {port}")
    elif mode == 'build-server':
        click.echo(f"🚀 Starting production server on port {port} with {threads} threads...")
        os.system(f"uvicorn main:app --host 0.0.0.0 --port {port} --workers {threads}")
