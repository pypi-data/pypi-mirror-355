"""Template rendering utilities for BS FastAPI CLI."""

from jinja2 import Environment, BaseLoader
from typing import Dict, Any, Optional
import importlib.util
import os

class TemplateRenderer:
    """Render Jinja2 templates for code generation."""
    
    def __init__(self):
        """Initialize template renderer."""
        self.env = Environment(loader=BaseLoader())
        # Configure Jinja2 to use different delimiters to avoid conflicts
        self.env.block_start_string = '{%'
        self.env.block_end_string = '%}'
        self.env.variable_start_string = '{{'
        self.env.variable_end_string = '}}'
        self.env.comment_start_string = '{#'
        self.env.comment_end_string = '#}'
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        template_content = self._load_template(template_name)
        
        if template_content is None:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.env.from_string(template_content)
        return template.render(**context)
    
    def _load_template(self, template_name: str) -> str:
        """Load template content from template files."""
        try:
            # Import the template module directly
            module_name = template_name.replace('.py', '')
            template_module_path = f"bs_cli.templates.{module_name}"
            
            # Import the template module
            template_module = __import__(template_module_path, fromlist=[module_name])
            
            # Get the template constant (assumes template is stored in a constant)
            template_constant_name = module_name.replace('_template', '').upper() + '_TEMPLATE'
            template_content = getattr(template_module, template_constant_name, None)
            
            if template_content is None:
                raise ValueError(f"Template constant '{template_constant_name}' not found in module '{template_module_path}'")
            
            # Remove leading/trailing whitespace from template
            return template_content.strip()
            
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            raise ValueError(f"Failed to load template {template_name}")
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with the given context."""
        template = self.env.from_string(template_string)
        return template.render(**context)
    
    def add_filter(self, name: str, func):
        """Add a custom filter to the Jinja2 environment."""
        self.env.filters[name] = func
    
    def add_global(self, name: str, value):
        """Add a global variable to the Jinja2 environment."""
        self.env.globals[name] = value

# Common template filters
def snake_case(text):
    """Convert text to snake_case."""
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()

def pascal_case(text):
    """Convert text to PascalCase."""
    return ''.join(word.capitalize() for word in text.split('_'))

def camel_case(text):
    """Convert text to camelCase."""
    words = text.split('_')
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

# Initialize default filters
def setup_default_filters(renderer: TemplateRenderer):
    """Setup default template filters."""
    renderer.add_filter('snake_case', snake_case)
    renderer.add_filter('pascal_case', pascal_case)
    renderer.add_filter('camel_case', camel_case)
