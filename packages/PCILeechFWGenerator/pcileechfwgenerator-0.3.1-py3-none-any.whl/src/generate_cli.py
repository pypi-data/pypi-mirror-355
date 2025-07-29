#!/usr/bin/env python3
"""
CLI entry point for pcileech-generate console script.
This module provides the main() function that setuptools will use as an entry point.
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for pcileech-generate command"""
    try:
        # Import the original generate module
        from generate import main as generate_main

        return generate_main()
    except ImportError as e:
        print(f"Error importing generate module: {e}")
        print("Make sure you're running from the correct directory.")
        return 1
    except Exception as e:
        print(f"Error running generate: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
