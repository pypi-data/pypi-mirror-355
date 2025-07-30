import argparse
import sys
from rich.console import Console
from gitsnipe import core
import gitsnipe
console = Console()

def create_parser():
    parser = argparse.ArgumentParser(
        description="A CLI tool to scan websites for exposed .git/config files, extract credentialed repository URLs, and clone them using git or git-dumper.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "url",
        nargs="?", 
        default=None,
        help="Website URL to scan or clone (e.g., https://example.com)."
    )
    parser.add_argument(
        "-i", "--input-file",
        default=None,
        help="File containing URLs to scan or clone (.txt, .csv, .json)."
    )
    parser.add_argument(
        "-o", "--output-dir", 
        default=None,
        help="Base directory for scan results and cloned repositories."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true", 
        help="Overwrite existing clone directories."
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Only attempt to clone the repository using git (if credentials) or git-dumper, skipping .git/config scanning."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s  {gitsnipe.__version__}",
        help="Show program version."
    )
    return parser

def main():
    try:
        parser = create_parser()
        args = parser.parse_args()

        if not args.url and not args.input_file:
            parser.print_help()
            sys.exit(1)

        input_source = args.input_file if args.input_file else args.url
        core.run_scan_process(
            input_source=input_source,
            output_dir=args.output_dir,
            force=args.force,
            clone_only=args.clone
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()