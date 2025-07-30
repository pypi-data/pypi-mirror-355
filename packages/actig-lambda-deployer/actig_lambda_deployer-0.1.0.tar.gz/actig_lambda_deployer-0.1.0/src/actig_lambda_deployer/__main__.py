"""
Entry point for the actig-lambda-deployer package when run as a module.

Usage:
    python -m actig_lambda_deployer --help
    python -m actig_lambda_deployer deploy /path/to/lambda --function-name my-function
"""

import sys
from .cli import cli


def main():
    """Main entry point for the application"""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()