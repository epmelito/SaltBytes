from forecast_ops.api import fetch_forecast
from forecast_ops.config import load_config

# load dev settings and request one configured location
config = load_config("dev")
location = config["locations"][0]

payload = fetch_forecast(location, config["api"])

print(f"location: {location['id']}")
print(f"latitude: {payload['latitude']}")
print(f"longitude: {payload['longitude']}")
print(f"timezone: {payload['timezone']}")
print(f"hourly rows: {len(payload['hourly']['time'])}")