from forecast_ops.config import load_config
from forecast_ops.logging import configure_logging
from forecast_ops.pipeline import run_pipeline


# load configuration and run the pipeline
def main() -> None:
    config = load_config()

    configure_logging(config)

    result = run_pipeline(config)

    print(f"run id: {result['run_id']}")
    print(f"status: {result['status']}")
    print(f"snapshots written: {result['snapshots_written']}")
    print(f"rows loaded: {result['rows_loaded']}")


if __name__ == "__main__":
    main()
