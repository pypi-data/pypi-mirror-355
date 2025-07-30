# ProgressivePostgres

**ProgressivePostgres** is a Python client library for interacting with a TimescaleDB (or PostgreSQL) instance, configured via environment variables. It integrates seamlessly with the [Zeitgleich](https://pypi.org/project/Zeitgleich/) library for improved time-series handling and includes optional features for bridging MQTT data ingestion through [SwampClient](https://pypi.org/project/SwampClient/).

ProgressivePostgres provides:

- **Time-Series Data Models** — Integration with `TimeSeriesData` and `MultiOriginTimeSeries`.
- **Environment-Based Configuration** — Minimizes boilerplate; simply use a `.env` file.
- **Automatic Table Creation** — Optionally create hypertables for your data if they do not already exist.
- **Extra Columns Handling** — Decide how to manage columns beyond the expected set: `ignore`, `error`, or `append`.
- **Asynchronous MQTT Integration** — If combined with an MQTT client, seamlessly push sensor data into TimescaleDB.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
- [Usage & Examples](#usage--examples)
- [TODOs](#todos)
- [License](#license)

---

## Features

- **Simple DB Client:** Quickly execute queries, insert data, and retrieve time-series rows.
- **Timestamp Normalization:** `TimeSeriesData` can parse and convert timestamps among multiple formats (`ISO`, `RFC3339`, `UNIX`, etc.).
- **Automatic Hypertable Creation:** Create TimescaleDB hypertables on-the-fly if desired.
- **Multi-Origin Data Model:** Use `MultiOriginTimeSeries` for simultaneously managing data from multiple sensors or devices.
- **Optional MQTT Bridge:** Combine with an MQTT client for real-time sensor data ingestion.

---

## Installation

Install **ProgressivePostgres** (and any needed dependencies) via:

```bash
pip install ProgressivePostgres
```

or clone the repository locally with the provided Makefile:

```bash
make install
```

---

## Configuration

ProgressivePostgres uses environment variables for configuration, read from a prefix that you pass to the `Client(name="TS")` constructor.

### Environment Variables

| Variable                                          | Description                                                                 | Default     | Options                          |
|---------------------------------------------------|-----------------------------------------------------------------------------|-------------|-----------------------------------|
| `{PREFIX}_DB_HOST`                                | Hostname for TimescaleDB/PostgreSQL.                                       | `localhost` |                                   |
| `{PREFIX}_DB_PORT`                                | Port for TimescaleDB.                                                      | `5432`      |                                   |
| `{PREFIX}_DB_NAME`                                | Database name.                                                              | `timescale` |                                   |
| `{PREFIX}_DB_USER`                                | Username for DB authentication.                                            | `postgres`  |                                   |
| `{PREFIX}_DB_PASS`                                | Password for DB authentication.                                            | *None*      |                                   |
| `{PREFIX}_DB_AUTOCOMMIT`                          | Whether to auto-commit each statement.                                     | `true`      | `true`, `false`                  |
| `{PREFIX}_LOG_LEVEL`                              | Log level.                                                                  | `DEBUG`     | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `{PREFIX}_ORIGIN_SPLIT_CHAR`                      | Char used to split origins (e.g. `machine1/sensorA`).                      | `/`         |                                   |
| `{PREFIX}_ORIGIN_JOIN_CHAR`                       | Char used to join origin parts for table naming.                            | `/`         |                                   |
| `{PREFIX}_TIMESTAMP_COLUMN`                       | Name of the time column in DB.                                             | `timestamp` |                                   |
| `{PREFIX}_VALUE_COLUMN`                           | Name of the primary value column.                                          | `value`     |                                   |
| `{PREFIX}_CREATE_TABLES_IF_NOT_EXIST`             | Automatically create hypertables if missing.                                | `true`      | `true`, `false`                  |
| `{PREFIX}_EXTRA_COLUMNS_HANDLING`                 | Handling of extra columns.                                                 | `append`    | `ignore`, `error`, `append`      |

---

## Usage & Examples

To see **working code samples**, please refer to the [examples directory](examples/) in this repository. Highlights include:

- **Basic Example:** Demonstrates how to connect to a local TimescaleDB instance, run simple queries, and handle `.env` environment variables.
- **MQTT Logger Example:** Combines ProgressivePostgres with an MQTT client, pushing messages from topics into TimescaleDB.
- **Zeitgleich Example:** Showcases using `TimeSeriesData` and `MultiOriginTimeSeries` for multi-sensor data insertion and retrieval.

### Example `.env`

A typical `.env` file might look like:

```
TS_DB_HOST="localhost"
TS_DB_PORT="5444"
TS_DB_NAME="timeseries"
TS_DB_USER="postgres"
TS_DB_PASS="pwd"
TS_LOG_LEVEL="DEBUG"
TS_ORIGIN_SPLIT_CHAR="/"
TS_ORIGIN_JOIN_CHAR="_"
TS_TIMESTAMP_COLUMN="timestamp"
TS_VALUE_COLUMN="value"
TS_EXTRA_COLUMNS_HANDLING="append"
TS_CREATE_TABLES_IF_NOT_EXIST="true"
```

Load these environment variables in your Python script using [`python-dotenv`](https://pypi.org/project/python-dotenv):

```python
from dotenv import load_dotenv

load_dotenv()
```

Then instantiate a client:

```python
from ProgressivePostgres import Client

client = Client(name="TS")  # "TS" will be the prefix for env variables
# ...
```

---

## TODOs

- **Automatic Migrations:** Provide tools to manage schema migrations automatically.
- **Advanced Query Builder:** Add an optional query builder for more complex queries (joins, filters, etc.).
- **Transaction Handling:** More robust transaction management (automatic rollback on certain errors).
- **Comprehensive Testing:** Add unit and integration tests across various DB versions.
- **Enhanced MQTT Integration:** Provide additional examples.

---

## License

Licensed under the [MIT License](LICENSE).