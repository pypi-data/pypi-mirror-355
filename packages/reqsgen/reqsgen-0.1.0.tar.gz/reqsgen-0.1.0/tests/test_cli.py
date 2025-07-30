"""Tests for the CLI interface."""

import tempfile
import os
import subprocess
import sys
from pathlib import Path
import pytest


class TestCLI:
    """Test command-line interface."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, '-m', 'reqsgen', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert 'Generate requirements.txt from your Python imports' in result.stdout
        assert '--pin' in result.stdout
        assert '--output' in result.stdout
    
    def test_cli_version(self):
        """Test CLI version output."""
        result = subprocess.run(
            [sys.executable, '-m', 'reqsgen', '--version'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert '0.1.0' in result.stdout
    
    def test_cli_basic_usage(self):
        """Test basic CLI usage."""
        fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'reqsgen', str(fixtures_dir), '-o', output_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            assert result.returncode == 0
            assert 'Wrote' in result.stdout
            assert 'packages to' in result.stdout
            
            # Check that file was created and has content
            assert os.path.exists(output_file)
            with open(output_file, 'r') as f:
                content = f.read().strip()
            
            assert len(content) > 0
            lines = content.split('\n')
            assert len(lines) > 0
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_cli_nonexistent_path(self):
        """Test CLI with nonexistent path."""
        result = subprocess.run(
            [sys.executable, '-m', 'reqsgen', '/nonexistent/path'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 1
        assert 'does not exist' in result.stderr
