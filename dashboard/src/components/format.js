export function asDate(value) {
  if (value === null || value === undefined || value === "") return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatTimestamp(value, timeZone = "UTC") {
  const date = asDate(value);
  if (date === null) return "Unavailable";
  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short"
  }).format(date);
}

export function formatNumber(value, digits = 1, unit = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Unavailable";
  }
  const suffix = unit ? ` ${unit}` : "";
  return `${Number(value).toFixed(digits)}${suffix}`;
}

export function celsiusToFahrenheit(value) {
  return value === null || value === undefined ? value : Number(value) * 9 / 5 + 32;
}

export function kilometersPerHourToMph(value) {
  return value === null || value === undefined ? value : Number(value) / 1.609344;
}

export function metersToFeet(value) {
  return value === null || value === undefined ? value : Number(value) * 3.2808398950131;
}

export function millimetersToInches(value) {
  return value === null || value === undefined ? value : Number(value) / 25.4;
}

export function hectopascalsToInchesMercury(value) {
  return value === null || value === undefined ? value : Number(value) * 0.0295299830714;
}

export function kilometersToMiles(value) {
  return value === null || value === undefined ? value : Number(value) / 1.609344;
}

export function formatMinutes(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Unavailable";
  }
  const minutes = Math.max(Math.round(Number(value)), 0);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainder = minutes % 60;
  return [days ? `${days}d` : null, hours ? `${hours}h` : null, `${remainder}m`]
    .filter(Boolean)
    .join(" ");
}

export function locationName(locationId, locations) {
  return locations.find((location) => location.location_id === locationId)?.name ?? locationId;
}

export function sourceName(source) {
  return {
    weather: "Weather",
    pressure: "Barometric pressure",
    wave: "Wave",
    sst: "Sea surface temperature",
    tide: "Tide"
  }[source] ?? source;
}

export function statusLabel(status) {
  if (status === null || status === undefined || status === "") return "Unavailable";
  return String(status).replaceAll("_", " ");
}

export function compassDirection(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Unavailable";
  }
  const labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const normalized = ((Number(value) % 360) + 360) % 360;
  return labels[Math.round(normalized / 45) % 8];
}
