import argparse
import os
import sys

import yaml

from ipf_dynamic_attributes import AttributeSync


def _check_excel(outfile: str) -> str:
    if not outfile:
        raise SyntaxError("Output file '-o|--outfile' must be specified with Excel format.")
    try:
        import xlsxwriter  # noqa: F401

        return "xlsxwriter"
    except ImportError:
        pass
    try:
        import openpyxl  # noqa: F401

        return "openpyxl"
    except ImportError:
        raise ImportError(
            "Excel format requires either 'xlsxwriter' or 'openpyxl' to be installed. "
            "Please install one of them using pip, recommended to use 'xlsxwriter'."
        )


def main():
    arg_parser = argparse.ArgumentParser(
        description="IP Fabric Dynamic Attribute.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
    This script will run the AttributeSync with the provided configuration file(s) which defaults to 'config.yml'.
    You can specify a different or multiple configuration files by passing the filename as an argument:
    ipf_dynamic_attributes mgmt-ip.yml region.yml
    """,
    )
    arg_parser.add_argument(
        "filenames",
        nargs="*",
        default=["config.yml"],
        help="Configuration filename(s), defaults to 'config.yml'.",
    )
    arg_parser.add_argument(
        "-f",
        "--format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output format for the report. Default is 'csv'. Use 'json' for JSON output.",
    )
    arg_parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        help="Output filename to send report instead of standard out.",
    )
    arg_parser.add_argument(
        "-m",
        "--merge-only",
        action="store_true",
        default=False,
        help="Merge the default rule settings into rules and display the resulting file; does not run any automation. "
        "This will also merge multiple configuration files into a single file.",
    )
    args = arg_parser.parse_args()
    for file in args.filenames:
        if not os.path.isfile(file):
            raise FileNotFoundError(f"Configuration file '{file}' does not exist.")

    sync = AttributeSync(config=args.filenames)

    if args.merge_only:
        print(yaml.dump(sync.config.model_dump_merged()))
        exit(0)

    engine = None
    if args.format == "excel":
        engine = _check_excel(args.outfile)

    report = sync.run()

    outfile = args.outfile or sys.stdout
    columns = [*sync.config.inventory.df_columns, "correct", "update", "create"]
    if args.format == "json":
        report.to_json(outfile, index=False, orient="records")
    elif args.format == "csv":
        report.to_csv(outfile, index=False, columns=columns)
    else:
        report.to_excel(outfile, index=False, columns=columns, engine=engine)


if __name__ == "__main__":
    main()
