"""
Command-line interface for reqsgen.
"""

import argparse
import sys
from pathlib import Path
from .scanner import generate_requirements


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="reqsgen",
        description="Generate requirements.txt from your Python imports",
        epilog="Example: reqsgen . -o requirements.txt --pin"
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan for Python files (default: current directory)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="requirements.txt",
        help="Output file path (default: requirements.txt)"
    )
    
    parser.add_argument(
        "--pin",
        action="store_true",
        help="Pin package versions (e.g., package==1.2.3)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    args = parser.parse_args()
    
    # Validate input path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Generate requirements
        num_packages = generate_requirements(
            path=args.path,
            output_file=args.output,
            pin_versions=args.pin
        )
        
        # Print summary
        print(f"Wrote {num_packages} packages to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
