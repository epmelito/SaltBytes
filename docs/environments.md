# Environments

ForecastOps uses three local YAML configurations:

```text
config/dev.yml
config/test.yml
config/prod.yml
```

They are complete local configuration variants, not deployed cloud
environments.

## `dev`

Use for normal local execution and MVP work:

```powershell
forecast-ops --environment dev
```

## `test`

Use for automated tests and isolated validation behavior. Tests may replace
clients, paths, or configured values with temporary equivalents.

## `prod`

A separate local configuration with its own data paths. Its name does not mean
the project is deployed, scheduled, monitored, or production ready.

## Separation

Each environment writes to its own raw-data path and DuckDB database beneath
`data/`. Runtime data is excluded from Git.

Configuration includes provider settings, requested fields, forecast horizon,
approved locations, source coordinates, and NOAA tide relationships.

The current providers do not require committed credentials. Do not place
passwords, API keys, tokens, or connection strings in YAML or source code.