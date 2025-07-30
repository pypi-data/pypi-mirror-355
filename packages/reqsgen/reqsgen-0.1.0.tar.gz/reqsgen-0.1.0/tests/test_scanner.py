"""Tests for the scanner module."""

import tempfile
import os
from pathlib import Path
import pytest

from reqsgen.scanner import (
    find_imports,
    filter_stdlib,
    extract_imports_from_file,
    find_python_files,
    generate_requirements
)
from reqsgen.stdlib_modules import is_stdlib_module


class TestImportExtraction:
    """Test import extraction functionality."""
    
    def test_extract_imports_from_file(self):
        """Test extracting imports from a single file."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
import sys
from pathlib import Path
import requests
from flask import Flask
from numpy import array
""")
            temp_file = Path(f.name)
        
        try:
            imports = extract_imports_from_file(temp_file)
            expected = {'os', 'sys', 'pathlib', 'requests', 'flask', 'numpy'}
            assert imports == expected
        finally:
            os.unlink(temp_file)
    
    def test_extract_imports_with_syntax_error(self):
        """Test handling files with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nthis is not valid python syntax")
            temp_file = Path(f.name)
        
        try:
            imports = extract_imports_from_file(temp_file)
            # Should return empty set for files with syntax errors
            assert imports == set()
        finally:
            os.unlink(temp_file)


class TestStdlibFiltering:
    """Test standard library filtering."""
    
    def test_is_stdlib_module(self):
        """Test stdlib module detection."""
        # Standard library modules
        assert is_stdlib_module('os')
        assert is_stdlib_module('sys')
        assert is_stdlib_module('json')
        assert is_stdlib_module('pathlib')
        assert is_stdlib_module('datetime')
        
        # Third-party modules
        assert not is_stdlib_module('requests')
        assert not is_stdlib_module('flask')
        assert not is_stdlib_module('numpy')
        assert not is_stdlib_module('pandas')
    
    def test_is_stdlib_module_with_submodules(self):
        """Test stdlib detection with submodules."""
        assert is_stdlib_module('os.path')
        assert is_stdlib_module('urllib.request')
        assert is_stdlib_module('xml.etree')
        
        assert not is_stdlib_module('requests.auth')
        assert not is_stdlib_module('flask.request')
    
    def test_filter_stdlib(self):
        """Test filtering stdlib modules from import set."""
        imports = {
            'os', 'sys', 'json', 'pathlib',  # stdlib
            'requests', 'flask', 'numpy', 'pandas'  # third-party
        }
        
        filtered = filter_stdlib(imports)
        expected = {'requests', 'flask', 'numpy', 'pandas'}
        assert filtered == expected


class TestDirectoryScanning:
    """Test directory scanning functionality."""
    
    def test_find_python_files(self):
        """Test finding Python files in directory."""
        # Use the test fixtures
        fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'
        python_files = find_python_files(fixtures_dir)
        
        # Should find all .py files
        file_names = {f.name for f in python_files}
        expected = {'main.py', 'utils.py', 'config.py'}
        assert file_names == expected
    
    def test_find_imports_in_directory(self):
        """Test finding all imports in a directory."""
        fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'
        imports = find_imports(fixtures_dir)
        
        # Should include all imports from all files
        expected_third_party = {'requests', 'numpy', 'flask', 'click', 'pandas', 'sqlalchemy', 'yaml'}
        expected_stdlib = {'os', 'sys', 'pathlib', 'json', 'datetime', 're', 'typing', 'configparser'}
        
        # Check that we found the third-party imports
        third_party_found = filter_stdlib(imports)
        assert expected_third_party.issubset(third_party_found)
        
        # Check that we found stdlib imports too
        stdlib_found = imports - third_party_found
        assert expected_stdlib.issubset(stdlib_found)


class TestRequirementsGeneration:
    """Test requirements file generation."""
    
    def test_generate_requirements(self):
        """Test generating requirements file."""
        fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_file = f.name
        
        try:
            num_packages = generate_requirements(
                path=fixtures_dir,
                output_file=output_file,
                pin_versions=False
            )
            
            # Should have found some packages
            assert num_packages > 0
            
            # Read the generated file
            with open(output_file, 'r') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            packages = [line.strip() for line in lines if line.strip()]
            
            # Should be sorted
            assert packages == sorted(packages)
            
            # Should contain expected packages
            expected = {'click', 'flask', 'numpy', 'pandas', 'requests', 'sqlalchemy', 'yaml'}
            found_packages = set(packages)
            assert expected.issubset(found_packages)
            
        finally:
            os.unlink(output_file)
