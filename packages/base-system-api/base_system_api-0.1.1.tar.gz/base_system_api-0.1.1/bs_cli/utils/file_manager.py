"""File management utilities for BS FastAPI CLI."""

import os
from pathlib import Path
from typing import Optional

class FileManager:
    """Manage file operations for project generation."""
    
    def __init__(self, base_path: Path):
        """Initialize file manager with base path."""
        self.base_path = Path(base_path)
    
    def create_directory(self, directory_path: str) -> Path:
        """Create a directory if it doesn't exist."""
        full_path = self.base_path / directory_path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def write_file(self, file_path: str, content: str) -> Path:
        """Write content to a file."""
        full_path = self.base_path / file_path
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return full_path
    
    def read_file(self, file_path: str) -> Optional[str]:
        """Read content from a file."""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        full_path = self.base_path / file_path
        return full_path.exists() and full_path.is_file()
    
    def directory_exists(self, directory_path: str) -> bool:
        """Check if a directory exists."""
        full_path = self.base_path / directory_path
        return full_path.exists() and full_path.is_dir()
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        full_path = self.base_path / file_path
        
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True
        return False
    
    def list_files(self, directory_path: str = "", pattern: str = "*") -> list:
        """List files in a directory."""
        full_path = self.base_path / directory_path
        
        if not full_path.exists() or not full_path.is_dir():
            return []
        
        return [f.name for f in full_path.glob(pattern) if f.is_file()]
    
    def get_absolute_path(self, file_path: str = "") -> Path:
        """Get absolute path for a file or directory."""
        return (self.base_path / file_path).absolute()
