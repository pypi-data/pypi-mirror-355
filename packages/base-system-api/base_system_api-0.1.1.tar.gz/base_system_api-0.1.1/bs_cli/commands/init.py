"""Initialize command for creating FastAPI project structure."""

import click
import os
from pathlib import Path
from bs_cli.utils.file_manager import FileManager
from bs_cli.utils.template_renderer import TemplateRenderer

@click.command()
@click.option('--name', '-n', default='fastapi_project', help='Project name')
@click.option('--path', '-p', default='.', help='Project path')
def init_command(name, path):
    """Initialize a new FastAPI project structure."""
    click.echo(f"🚀 Initializing FastAPI project '{name}' in '{path}'...")
    
    # Create project directory
    project_path = Path(path) / name
    file_manager = FileManager(project_path)
    template_renderer = TemplateRenderer()
    
    try:
        # Create directory structure
        directories = [
            'bs__connection',
            'bs__security',
            'models',
            'schemas',
            'routers',
            'orm'
        ]
        
        for directory in directories:
            file_manager.create_directory(directory)
        
        # Generate main.py
        main_content = template_renderer.render_template('main_template.py', {
            'project_name': name
        })
        file_manager.write_file('main.py', main_content)
        
        # Generate connection module
        connection_content = template_renderer.render_template('connection_template.py', {})
        file_manager.write_file('bs__connection/__init__.py', '')
        file_manager.write_file('bs__connection/database.py', connection_content)
        
        # Generate security module
        security_content = template_renderer.render_template('security_template.py', {})
        file_manager.write_file('bs__security/__init__.py', '')
        file_manager.write_file('bs__security/auth.py', security_content)
        
        # Create __init__.py files
        init_files = ['models/__init__.py', 'schemas/__init__.py', 'routers/__init__.py', 'orm/__init__.py']
        for init_file in init_files:
            file_manager.write_file(init_file, '')
        
        click.echo(f"✅ Project '{name}' initialized successfully!")
        click.echo(f"📁 Project created at: {project_path.absolute()}")
        click.echo("\n📋 Next steps:")
        click.echo(f"   cd {name}")
        click.echo("   bs create <ModelName>  # Generate model, schema, and router")
        click.echo("   pip install fastapi uvicorn sqlalchemy passlib python-jose alembic")
        
        try:
            # Install dependencies
            click.echo("   pip install fastapi uvicorn sqlalchemy passlib python-jose alembic")
            os.system("pip install fastapi uvicorn sqlalchemy passlib python-jose alembic")
            
            # Change to the project directory
            original_cwd = Path.cwd()
            os.chdir(project_path)
            
            # Initialize Alembic for migrations
            click.echo("🚀 Setting up Alembic for migrations...")
            os.system("alembic init migrations")
            
            # Update alembic.ini with a valid database URL
            alembic_ini_path = Path("alembic.ini")
            with open(alembic_ini_path, "r") as f:
                alembic_ini_content = f.read()
            alembic_ini_content = alembic_ini_content.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                "sqlalchemy.url = sqlite:///./test.db"  # Example: SQLite database
            )
            with open(alembic_ini_path, "w") as f:
                f.write(alembic_ini_content)
            
            # Update env.py for autogeneration
            alembic_env_path = Path("migrations/env.py")
            with open(alembic_env_path, "r") as f:
                env_content = f.read()
            env_content = env_content.replace(
                "target_metadata = None",
                "from bs__connection.database import Base\n"
                "import os\n"
                "import importlib\n"
                "# Dynamically import all models to ensure they are registered in Base.metadata\n"
                "models_path = os.path.join(os.path.dirname(__file__), '../models')\n"
                "for file in os.listdir(models_path):\n"
                "    if file.endswith('.py') and file != '__init__.py':\n"
                "        module_name = f'models.{file[:-3]}'\n"
                "        importlib.import_module(module_name)\n"
                "target_metadata = Base.metadata"
            )
            with open(alembic_env_path, "w") as f:
                f.write(env_content)
        except Exception as e:
            click.echo(f"❌ Error initializing project: {str(e)}", err=True)  # Fixed unterminated string
            raise click.Abort()
        finally:
            # Return to the original directory
            os.chdir(original_cwd)
    except Exception as e:
        click.echo(f"❌ Error initializing project: {str(e)}", err=True)
        raise click.Abort()
