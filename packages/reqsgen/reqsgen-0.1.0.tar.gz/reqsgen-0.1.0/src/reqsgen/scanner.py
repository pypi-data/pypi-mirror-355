"""
Core functionality for scanning Python files and extracting import information.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Optional, Union
from .stdlib_modules import is_stdlib_module

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Fallback for Python < 3.8
    from importlib_metadata import version, PackageNotFoundError


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements from Python code."""
    
    def __init__(self):
        self.imports = set()
    
    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            # Get the root module name (e.g., 'requests' from 'requests.auth')
            root_module = alias.name.split('.')[0]
            self.imports.add(root_module)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Handle 'from module import ...' statements."""
        if node.module:
            # Skip relative imports (level > 0 means relative import)
            if node.level == 0:
                # Get the root module name
                root_module = node.module.split('.')[0]
                self.imports.add(root_module)
        self.generic_visit(node)


def find_python_files(path: Union[str, Path]) -> List[Path]:
    """
    Recursively find all Python files in a directory.
    
    Args:
        path: Directory path to search
        
    Returns:
        List of Path objects for Python files
    """
    path = Path(path)
    python_files = []
    
    if path.is_file() and path.suffix == '.py':
        return [path]
    
    if path.is_dir():
        for root, dirs, files in os.walk(path):
            # Skip common directories that shouldn't be scanned
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
    
    return python_files


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """
    Extract all import statements from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Set of imported module names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=str(file_path))
        
        # Extract imports
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return visitor.imports
    
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return set()


def find_imports(path: Union[str, Path]) -> Set[str]:
    """
    Find all imports in Python files within a directory.
    
    Args:
        path: Directory path to scan
        
    Returns:
        Set of all imported module names
    """
    all_imports = set()
    python_files = find_python_files(path)
    
    for file_path in python_files:
        file_imports = extract_imports_from_file(file_path)
        all_imports.update(file_imports)
    
    return all_imports


def filter_stdlib(imports: Set[str]) -> Set[str]:
    """
    Filter out standard library modules from a set of imports.

    Args:
        imports: Set of module names

    Returns:
        Set of non-stdlib module names
    """
    # Common local module names to exclude
    local_patterns = {
        'utils', 'config', 'settings', 'constants', 'helpers', 'models',
        'views', 'forms', 'tests', 'test', 'main', 'app', 'core'
    }

    filtered = set()
    for imp in imports:
        if not is_stdlib_module(imp) and imp not in local_patterns:
            filtered.add(imp)

    return filtered


def get_installed_version(package_name: str) -> Optional[str]:
    """
    Get the installed version of a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string if package is installed, None otherwise
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def generate_requirements(
    path: Union[str, Path],
    output_file: str = "requirements.txt",
    pin_versions: bool = False
) -> int:
    """
    Generate a requirements.txt file from imports in Python files.
    
    Args:
        path: Directory path to scan
        output_file: Output file path
        pin_versions: Whether to pin package versions
        
    Returns:
        Number of packages written to requirements file
    """
    # Find all imports
    all_imports = find_imports(path)
    
    # Filter out stdlib modules
    external_packages = filter_stdlib(all_imports)
    
    # Sort packages alphabetically
    sorted_packages = sorted(external_packages)
    
    # Generate requirements lines
    requirements_lines = []
    for package in sorted_packages:
        if pin_versions:
            pkg_version = get_installed_version(package)
            if pkg_version:
                requirements_lines.append(f"{package}=={pkg_version}")
            else:
                print(f"Warning: Could not find version for {package}, adding without version", file=sys.stderr)
                requirements_lines.append(package)
        else:
            requirements_lines.append(package)
    
    # Write requirements file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in requirements_lines:
            f.write(line + '\n')
    
    return len(requirements_lines)
