import argparse
import sys

from oneenv import template, generate_env_example, diff

def main():
    """
    English: Main entry point for the oneenv command line interface.
    Japanese: oneenvコマンドラインインターフェースのメインエントリーポイント。
    """
    parser = argparse.ArgumentParser(description="OneEnv: Environment variable management tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Template command
    template_parser = subparsers.add_parser("template", help="Generate .env.example file")
    template_parser.add_argument(
        "-o", "--output",
        help="Output file path (default: .env.example)",
        default=".env.example"
    )
    template_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")

    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Show differences between two .env files")
    diff_parser.add_argument(
        "previous",
        help="Path to the previous .env file"
    )
    diff_parser.add_argument(
        "current",
        help="Path to the current .env file"
    )

    args = parser.parse_args()

    if args.command == "template":
        try:
            generate_env_example(args.output, debug=args.debug)
            print(f"Generated template at: {args.output}")
        except Exception as e:
            print(f"Error generating template: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "diff":
        try:
            with open(args.previous, 'r', encoding='utf-8') as f:
                previous_text = f.read()
            with open(args.current, 'r', encoding='utf-8') as f:
                current_text = f.read()
            
            diff_result = diff(previous_text, current_text)
            print(diff_result)
        except FileNotFoundError as e:
            print(f"Error: File not found - {e.filename}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error comparing files: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 