"""Create command for generating FastAPI models, schemas, and routes."""

import click
import os
from pathlib import Path
from bs_cli.utils.file_manager import FileManager
from bs_cli.utils.template_renderer import TemplateRenderer

@click.command()
@click.argument('model_name')
@click.option('--fields', '-f', help='Model fields (e.g., "name:str,age:int,email:str")')
@click.option('--path', '-p', default='.', help='Project path')
def create_command(model_name, fields, path):
    """Create a new FastAPI model with associated schema and router."""
    click.echo(f"🔧 Creating model '{model_name}'...")
    
    project_path = Path(path)
    file_manager = FileManager(project_path)
    template_renderer = TemplateRenderer()
    
    # Validate project structure
    required_dirs = ['models', 'schemas', 'routers', 'orm']
    for dir_name in required_dirs:
        if not (project_path / dir_name).exists():
            click.echo(f"❌ Error: '{dir_name}' directory not found. Run 'bs init' first.", err=True)
            raise click.Abort()
    
    try:
        # Parse fields if provided
        model_fields = []
        if fields:
            for field in fields.split(','):
                if ':' in field:
                    field_name, field_type = field.strip().split(':')
                    model_fields.append({
                        'name': field_name.strip(),
                        'type': field_type.strip()
                    })
        # Ensure a primary key field is added if not provided
        if not any(field['name'] == 'id' for field in model_fields):
            model_fields.insert(0, {'name': 'id', 'type': 'int'})  # Add 'id' as the primary key
        
        # Template context
        context = {
            'model_name': model_name,
            'model_name_lower': model_name.lower(),
            'model_name_plural': f"{model_name.lower()}s",
            'fields': model_fields
        }
        
        # Generate model file
        model_content = template_renderer.render_template('model_template.py', context)
        file_manager.write_file(f'models/models{model_name}.py', model_content)
        
        # Generate ORM file
        orm_content = template_renderer.render_template('orm_template.py', context)
        file_manager.write_file(f'orm/orm{model_name}.py', orm_content)
        
        # Generate schema file
        schema_content = template_renderer.render_template('schema_template.py', context)
        file_manager.write_file(f'schemas/schema{model_name}.py', schema_content)
        
        # Generate router file
        router_content = template_renderer.render_template('router_template.py', context)
        file_manager.write_file(f'routers/route{model_name}.py', router_content)
        
        click.echo(f"✅ Model '{model_name}' created successfully!")
        click.echo(f"📁 Generated files:")
        click.echo(f"   models/models{model_name}.py")
        click.echo(f"   orm/orm{model_name}.py")
        click.echo(f"   schemas/schema{model_name}.py")
        click.echo(f"   routers/route{model_name}.py")
        click.echo(f"\n📋 Don't forget to:")
        click.echo(f"   1. Import and include the router in main.py")
        click.echo(f"   2. Run database migrations if needed")
        
    except Exception as e:
        click.echo(f"❌ Error creating model: {str(e)}", err=True)
        raise click.Abort()
