import argparse
from pathlib import Path

from saltbytes.config import load_config
from saltbytes.dashboard import DashboardSchemaError, export_dashboard_data
from saltbytes.logging import configure_logging
from saltbytes.observations import retrieve_and_ingest_jennettes_pier
from saltbytes.pipeline import run_pipeline
from saltbytes.report import render_conditions_report, render_operations_report
from saltbytes.reporting.html import (
    render_conditions_html_report,
    render_operations_html_report,
)
from saltbytes.reporting.schema import ReportSchemaError


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument(
        "report_type",
        choices=("conditions", "operations"),
    )
    report_parser.add_argument("--run-id")
    report_parser.add_argument("--hours", type=int, default=24)
    report_parser.add_argument("--location")
    report_parser.add_argument("--format", choices=("text", "html"), default="text")
    report_parser.add_argument("--output")

    dashboard_parser = subparsers.add_parser("dashboard")
    dashboard_subparsers = dashboard_parser.add_subparsers(
        dest="dashboard_command",
        required=True,
    )
    export_parser = dashboard_subparsers.add_parser("export")
    export_parser.add_argument("--output", required=True)

    observations_parser = subparsers.add_parser("observations")
    observations_subparsers = observations_parser.add_subparsers(
        dest="observations_command",
        required=True,
    )
    jennettes_parser = observations_subparsers.add_parser("ingest-jennettes")
    jennettes_parser.add_argument("--database")

    return parser.parse_args(argv)


# load configuration and run the pipeline
def main(argv: list[str] | None = None) -> None:
    arguments = _parse_arguments(argv)

    if arguments.command == "observations" and arguments.database is not None:
        try:
            result = retrieve_and_ingest_jennettes_pier(arguments.database)
        except Exception as exc:
            raise SystemExit(
                f"error: Jennette's Pier observation ingestion failed: {exc}"
            ) from None
        print(f"reports persisted: {result['reports']}")
        print(f"assertions persisted: {result['assertions']}")
        return

    config = load_config()

    configure_logging(config)

    if arguments.command == "observations":
        try:
            result = retrieve_and_ingest_jennettes_pier(config["storage"]["database_path"])
        except Exception as exc:
            raise SystemExit(
                f"error: Jennette's Pier observation ingestion failed: {exc}"
            ) from None
        print(f"reports persisted: {result['reports']}")
        print(f"assertions persisted: {result['assertions']}")
        return

    if arguments.command == "dashboard":
        output_path = Path(arguments.output)
        try:
            export_dashboard_data(config, output_path)
        except DashboardSchemaError as exc:
            raise SystemExit(f"error: {exc}") from None
        return

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
            renderer = (
                render_conditions_report
                if arguments.report_type == "conditions"
                else render_operations_report
            )
            print(renderer(**report_arguments))
            return

        if arguments.output is None:
            raise ValueError("--output is required with --format html")

        output_path = Path(arguments.output)
        if not output_path.parent.is_dir():
            raise ValueError(f"output directory does not exist: {output_path.parent}")
        if output_path.is_dir():
            raise ValueError(f"output path must be a file: {output_path}")

        renderer = (
            render_conditions_html_report
            if arguments.report_type == "conditions"
            else render_operations_html_report
        )
        try:
            report = renderer(**report_arguments)
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

    if result["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
