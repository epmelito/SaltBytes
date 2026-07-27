import json
from pathlib import Path

from forecast_ops.api import fetch_forecast
from forecast_ops.config import load_config
from forecast_ops.storage import create_run_id, write_raw_snapshot


# load dev settings and capture one live forecast snapshot
config = load_config("dev")
location = config["locations"][0]
run_id = create_run_id()

payload = fetch_forecast(location, config["api"])

metadata = write_raw_snapshot(
    payload=payload,
    location_id=location["id"],
    raw_data_path=config["storage"]["raw_data_path"],
    run_id=run_id,
)

raw_file_path = Path(metadata["raw_file_path"])
stored_payload = json.loads(raw_file_path.read_text(encoding="utf-8"))

print(f"run id: {metadata['run_id']}")
print(f"snapshot id: {metadata['snapshot_id']}")
print(f"location: {metadata['location_id']}")
print(f"captured at: {metadata['captured_at'].isoformat()}")
print(f"raw file: {raw_file_path}")
print(f"hourly rows: {len(stored_payload['hourly']['time'])}")