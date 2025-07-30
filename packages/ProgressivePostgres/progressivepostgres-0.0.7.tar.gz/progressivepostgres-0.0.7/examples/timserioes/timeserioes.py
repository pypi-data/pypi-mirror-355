import os
from ProgressivePostgres import Client
from Zeitgleich.TimeSeriesData import TimeSeriesData
from Zeitgleich.TimestampFormat import TimestampFormat
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

client = Client(name="TS")

# Example TimeSeriesData creation
df_A = pd.DataFrame({
    "timestamp": [datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                  datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)],
    "value": [1.0, 2.0]
})
ts_A_data = TimeSeriesData(
    origin="machine1/sensorA",
    data=df_A,
    input_timestamp_format=TimestampFormat.ISO,
    output_timestamp_format=TimestampFormat.ISO
)

# Push TimeSeriesData to database
client.push_time_series_data(ts_A_data)

# Retrieve the same data
retrieved = client.get_time_series_data("machine1/sensorA", start=datetime(2023,1,1,tzinfo=timezone.utc))
print(retrieved)

# For MultiOriginTimeSeries:
from Zeitgleich.MultiOriginTimeSeries import MultiOriginTimeSeries

mots = MultiOriginTimeSeries(
    output_timestamp_format=TimestampFormat.ISO
)

mots.add_data(
    origin="machine1/sensorA",
    data=df_A,
    input_timestamp_format=TimestampFormat.ISO
)

df_B = pd.DataFrame({
    "timestamp": [datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                  datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)],
    "value": [3.0, 4.0]
})

mots.add_data(
    origin="machine1/sensorB",
    data=df_B,
    input_timestamp_format=TimestampFormat.ISO
)

# Push MultiOriginTimeSeries to database
client.push_multi_origin_time_series(mots)

# Retrieve multiple origins (multiple tables)
origins = ["machine1/sensorA", "machine1/sensorB"]
multi_retrieved = client.get_multi_origin_time_series(origins, start=datetime(2023,1,1,tzinfo=timezone.utc))
print(multi_retrieved)

# Test with String values
df_C = pd.DataFrame({
    "timestamp": [datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                  datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)],
    "value": ["a", "b"]
})

ts_C_data = TimeSeriesData(
    origin="machine1/sensorC",
    data=df_C,
    input_timestamp_format=TimestampFormat.ISO,
    output_timestamp_format=TimestampFormat.ISO
)

# TODO: Why do i get an error on the first push attempt? (for all data, not just C)
# [2024-12-23 15:55:47,752] [ERROR] [CLIENT_TS] [client.py execute_query() 67]: Query execution failed: relation "machine1/sensorc" does not exist
# LINE 2:         SELECT create_hypertable('machine1/sensorC', 'timest...
#                                          ^

client.push_time_series_data(ts_C_data)

retrieved = client.get_time_series_data("machine1/sensorC", start=datetime(2023,1,1,tzinfo=timezone.utc))
print(retrieved)
