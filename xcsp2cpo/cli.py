"""Command-line interface for xcsp2cpo."""

import argparse
import sys

from .converter import convert_file, convert_to_cpo


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="xcsp2cpo",
        description="Convert XCSP3 files to IBM CP Optimizer (CPO) format",
    )
    parser.add_argument(
        "input",
        help="Input XCSP3 XML file (use '-' for stdin)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CPO file (default: stdout)",
        default=None,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    try:
        if args.input == "-":
            # Read from stdin
            xcsp_content = sys.stdin.read()
            cpo_content = convert_to_cpo(xcsp_content)
        else:
            # Read from file
            cpo_content = convert_file(args.input, args.output)

        if args.output:
            if args.verbose:
                print(f"Converted {args.input} -> {args.output}", file=sys.stderr)
        else:
            print(cpo_content)

    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
