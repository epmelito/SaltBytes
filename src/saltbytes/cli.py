import argparse

from saltbytes.config import load_config
from saltbytes.logging import configure_logging
from saltbytes.pipeline import run_pipeline
from saltbytes.report import render_report


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--run-id")
    report_parser.add_argument("--hours", type=int, default=24)
    report_parser.add_argument("--location")

    return parser.parse_args(argv)


# load configuration and run the pipeline
def main(argv: list[str] | None = None) -> None:
    arguments = _parse_arguments(argv)
    config = load_config()

    configure_logging(config)

    if arguments.command == "report":
        print(
            render_report(
                config=config,
                run_id=arguments.run_id,
                hours=arguments.hours,
                location_id=arguments.location,
            )
        )
        return

    result = run_pipeline(config)

    print(f"run id: {result['run_id']}")
    print(f"status: {result['status']}")
    print(f"snapshots written: {result['snapshots_written']}")
    print(f"rows loaded: {result['rows_loaded']}")


if __name__ == "__main__":
    main()
