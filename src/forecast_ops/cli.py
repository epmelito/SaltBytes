import argparse

from forecast_ops.config import load_config
from forecast_ops.pipeline import run_pipeline


# parse command-line arguments
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="run the forecastops pipeline",
    )
    parser.add_argument(
        "--environment",
        choices=("dev", "test", "prod"),
        default="dev",
        help="configuration environment to run",
    )

    return parser.parse_args()


# load configuration and run the pipeline
def main() -> None:
    args = parse_args()
    config = load_config(args.environment)
    result = run_pipeline(config)

    print(f"run id: {result['run_id']}")
    print(f"environment: {result['environment']}")
    print(f"status: {result['status']}")
    print(f"snapshots written: {result['snapshots_written']}")
    print(f"rows loaded: {result['rows_loaded']}")


if __name__ == "__main__":
    main()