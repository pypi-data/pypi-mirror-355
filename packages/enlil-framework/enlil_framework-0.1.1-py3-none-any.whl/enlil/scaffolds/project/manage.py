#!/usr/bin/env python
"""Enlil's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # Add the project root directory to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    os.environ.setdefault('ENLIL_SETTINGS_MODULE', 'src.config')

    try:
        from enlil.management import cli
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Enlil. Are you sure it's installed?"
        ) from exc
    cli()

if __name__ == '__main__':
    main()