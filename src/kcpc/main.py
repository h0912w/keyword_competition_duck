"""main module for KCPC.

CLI entry point for the Keyword Competition Page Counter.
"""

import argparse
import sys

from kcpc.config import get_config, reset_config
from kcpc.exceptions import KcpcError
from kcpc.logging_config import get_logger, setup_logging
from kcpc.pipeline import run_pipeline
from kcpc.signal_handler import setup_signal_handlers

# Set up logging first
logger = setup_logging()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="KCPC - Keyword Competition Page Counter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m kcpc.main --input ./input/keywords.xlsx
  python -m kcpc.main --input ./input/keywords.xlsx --output ./output/result.xlsx
  python -m kcpc.main --input ./input/keywords.csv --output ./output/result.csv --format csv
  python -m kcpc.main --input ./input/keywords.xlsx --reset
        """,
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input file (.txt, .csv, or .xlsx)",
    )

    parser.add_argument(
        "--output",
        help="Path to output file (default: ./output/kcpc_result.xlsx)",
    )

    parser.add_argument(
        "--format",
        choices=["xlsx", "csv"],
        help="Output format (default: xlsx)",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing database and start fresh",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()

    # Parse arguments
    args = parse_args()

    try:
        # Reset config to ensure fresh state (in case of testing)
        reset_config()

        # Get config
        config = get_config()

        # Override config with command line arguments
        if args.output:
            config.output_file_path = args.output
        if args.format:
            config.output_format = args.format

        # Run pipeline
        run_pipeline(args.input, reset=args.reset)

        return 0

    except KcpcError as e:
        logger.error(f"KCPC error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
