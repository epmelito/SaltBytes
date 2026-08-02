import argparse
from pathlib import Path

from saltbytes.config import load_config
from saltbytes.logging import configure_logging
from saltbytes.pipeline import run_pipeline
from saltbytes.report import render_report
from saltbytes.reporting.html import render_html_report
from saltbytes.reporting.schema import ReportSchemaError


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--run-id")
    report_parser.add_argument("--hours", type=int, default=24)
    report_parser.add_argument("--location")
    report_parser.add_argument("--format", choices=("text", "html"), default="text")
    report_parser.add_argument("--output")

    return parser.parse_args(argv)


# load configuration and run the pipeline
def main(argv: list[str] | None = None) -> None:
    arguments = _parse_arguments(argv)
    config = load_config()

    configure_logging(config)

    if arguments.command == "report":
        report_arguments = {
            "config": config,
            "run_id": arguments.run_id,
            "hours": arguments.hours,
            "location_id": arguments.location,
        }
        if arguments.format == "text":
            if arguments.output is not None:
                raise ValueError("--output is only supported with --format html")
            print(render_report(**report_arguments))
            return

        if arguments.output is None:
            raise ValueError("--output is required with --format html")

        output_path = Path(arguments.output)
        if not output_path.parent.is_dir():
            raise ValueError(f"output directory does not exist: {output_path.parent}")
        if output_path.is_dir():
            raise ValueError(f"output path must be a file: {output_path}")

        try:
            report = render_html_report(
                **report_arguments
            )
        except ReportSchemaError as exc:
            raise SystemExit(f"error: {exc}") from None

        try:
            output_path.write_text(
                report,
                encoding="utf-8",
            )
        except OSError as exc:
            raise ValueError(
                f"could not write HTML report: {output_path}"
            ) from exc
        return

    result = run_pipeline(config)

    print(f"run id: {result['run_id']}")
    print(f"status: {result['status']}")
    print(f"snapshots written: {result['snapshots_written']}")
    print(f"rows loaded: {result['rows_loaded']}")


if __name__ == "__main__":
    main()
