#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from alertmanager import AlertManager

def main():
    """Command-line interface for AlertManager."""
    parser = argparse.ArgumentParser(description="AlertManager CLI")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )
    
    args = parser.parse_args()
    
    if args.version:
        from alertmanager import __version__
        print(f"AlertManager version {__version__}")
        sys.exit(0)
    
    try:
        manager = AlertManager(config_path=args.config)
        print("AlertManager initialized successfully")
    except Exception as e:
        print(f"Error initializing AlertManager: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 