# src/ZeitgleichClient/client.py

import logging
import psycopg2
from functools import wraps
from psycopg2.extras import RealDictCursor, Json, execute_values
from psycopg2.extensions import AsIs
from typing import Optional, Any, List, Dict
from datetime import datetime

from .config import Config
from .logger import setup_logger
from .cache import Cache

from Zeitgleich.TimeSeriesData import TimeSeriesData
from Zeitgleich.MultiOriginTimeSeries import MultiOriginTimeSeries
from Zeitgleich.TimestampFormat import TimestampFormat

class Client:
    def check_connection(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.connection or self.connection.closed != 0:
                self.logger.warning("Connection not available or closed. Attempting to reconnect.")
                self.connect()
            return func(self, *args, **kwargs)
        return wrapper
    
    def __init__(self, name: str = "Timescale"):
        self.name = name
        self.config = Config(env_prefix=self.name.upper())
        self.logger = setup_logger("CLIENT_" + self.name, level=self.config.log_level)
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self.connect()

    def connect(self):
        """Establish a connection to Timescale."""
        try:
            self.logger.info(f"Connecting to TimescaleDB at {self.config.db_host}:{self.config.db_port}/{self.config.db_name}")
            self.connection = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                dbname=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            self.connection.autocommit = self.config.db_autocommit
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            self.logger.info("Successfully connected to TimescaleDB.")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"Failed to connect to TimescaleDB: {e}")

    @check_connection
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"Executing query: {query}, params={params}")
        try:
            self.cursor.execute(query, params)
            if self.cursor.description:
                results = self.cursor.fetchall()
                self.logger.debug(f"Query returned {len(results)} rows.")
                return results
            else:
                self.logger.debug("Query executed successfully, no return data.")
                return []
        except psycopg2.Error as e:
            self.logger.error(f"Query execution failed: {e}")
            if not self.config.db_autocommit:
                self.connection.rollback()
            raise e

    def close(self):
        if self.cursor and not self.cursor.closed:
            self.cursor.close()
            self.logger.debug("Cursor closed.")
        if self.connection and self.connection.closed == 0:
            self.connection.close()
            self.logger.info("DB connection closed.")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def origin_to_table_name(self, origin: str) -> str:
        parts = origin.split(self.config.origin_split_char)
        table_name = self.config.origin_join_char.join(parts)
        return table_name

    @check_connection
    def get_table_schema(self, table_name: str):
        """Fetch table schema from INFORMATION_SCHEMA."""
        query = """
        SELECT column_name, data_type
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_schema = 'public' AND table_name = %s;
        """
        results = self.execute_query(query, [table_name])
        return [(r['column_name'], r['data_type']) for r in results]

    def _infer_postgres_type(self, value):
        """Infer PostgreSQL column type from a Python value."""
        if value is None:
            return None
        if isinstance(value, dict):
            return "jsonb"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            digits = len(str(abs(value)))
            return "integer" if digits <= 9 else "bigint"
        if isinstance(value, float):
            return "float8"
        if isinstance(value, datetime):
            return "timestamptz"
        return "text"

    def _create_hypertable_from_dataframe(self, table_name: str, df):
        """
        Creates a hypertable from the given DF by inferring column types,
        setting the configured timestamp_column as TIMESTAMPTZ PRIMARY KEY.
        """
        ts_col = self.config.timestamp_column
        col_defs = []
        col_names = df.columns.tolist()

        for col in col_names:
            if col == ts_col:
                col_defs.append(f"{col} TIMESTAMPTZ PRIMARY KEY")
                continue

            col_type = None
            for val in df[col]:
                inferred = self._infer_postgres_type(val)
                if inferred is not None:
                    col_type = inferred
                    break
            if col_type is None:
                col_type = "text"
            col_defs.append(f"{col} {col_type}")

        create_table_q = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)});'
        self.execute_query(create_table_q)

        hypertable_q = f"""
        SELECT create_hypertable('"{table_name}"', '{ts_col}', if_not_exists => TRUE);
        """
        try:
            self.execute_query(hypertable_q)
        except psycopg2.Error as e:
            self.logger.debug(f"Hypertable creation skipped/failed: {e}")

        Cache.update_cache(table_name, col_names)
    

    @check_connection
    def push_time_series_data_new(self, ts_data: TimeSeriesData):
        """
        Optimized insert using execute_values instead of executemany.
        """
        table_name = self.origin_to_table_name(str(ts_data.origin))
        ts_col = self.config.timestamp_column

        col_names = Cache.check_cache(table_name)
        if not col_names:
            schema = self.get_table_schema(table_name)
            if not schema and self.config.create_tables_if_not_exist:
                df = ts_data.df.reset_index()
                self._create_hypertable_from_dataframe(table_name, df)
                col_names = Cache.check_cache(table_name)
            elif not schema:
                self.logger.error(f"Table {table_name} does not exist and cannot create.")
                return
            else:
                col_names = [col[0] for col in schema]
                Cache.update_cache(table_name, col_names)

        df = ts_data.df.reset_index()
        rows = []
        for _, row_data in df.iterrows():
            row_values = []
            for c in col_names:
                val = row_data[c] if c in row_data else None
                if c == ts_col and isinstance(val, str):
                    val = datetime.fromisoformat(val)
                if isinstance(val, dict):
                    val = Json(val)
                row_values.append(val)
            rows.append(tuple(row_values))

        placeholders = ", ".join(['"%s"' % c for c in col_names])
        insert_q = f'INSERT INTO "{table_name}" ({placeholders}) VALUES %s ON CONFLICT DO NOTHING'

        try:
            execute_values(self.cursor, insert_q, rows, template=None, page_size=100)
            self.logger.info(f"Inserted {len(rows)} rows into {table_name}.")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to insert: {e} for table: {table_name}")
            if not self.config.db_autocommit:
                self.connection.rollback()

    @check_connection
    def push_time_series_data(self, ts_data: TimeSeriesData):
        """
        Insert data from a TimeSeriesData object into TimescaleDB.
        """
        table_name = self.origin_to_table_name(str(ts_data.origin))
        ts_col = self.config.timestamp_column

        col_names = Cache.check_cache(table_name)
        if not col_names:
            # Attempt to see if table exists
            schema = self.get_table_schema(table_name)
            if not schema and self.config.create_tables_if_not_exist:
                df = ts_data.df.reset_index()
                self._create_hypertable_from_dataframe(table_name, df)
                col_names = Cache.check_cache(table_name)
            elif not schema:
                self.logger.error(f"Table {table_name} does not exist and cannot create.")
                return
            else:
                col_names = [col[0] for col in schema]
                Cache.update_cache(table_name, col_names)

        df = ts_data.df.reset_index()
        placeholders = ", ".join(["%s"] * len(col_names))
        insert_q = f'INSERT INTO "{table_name}" ({", ".join(col_names)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'

        rows = []
        for _, row_data in df.iterrows():
            row_values = []
            for c in col_names:
                val = row_data[c] if c in row_data else None
                if c == ts_col and isinstance(val, str):
                    val = datetime.fromisoformat(val)
                if isinstance(val, dict):
                    val = Json(val)
                row_values.append(val)
            rows.append(tuple(row_values))

        try:
            self.cursor.executemany(insert_q, rows)
            self.logger.info(f"Inserted {len(rows)} rows into {table_name}.")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to insert: {e}")
            if not self.config.db_autocommit:
                self.connection.rollback()
            raise e

    @check_connection
    def get_time_series_data(
        self,
        origin: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        input_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
        output_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
        input_timezone=None,
        output_timezone=None,
        timestamp_as_index: bool = True
    ) -> TimeSeriesData:
        table_name = self.origin_to_table_name(origin)
        ts_col = self.config.timestamp_column

        conditions = []
        params = []
        if start:
            conditions.append(f"{ts_col} >= %s")
            params.append(start)
        if end:
            conditions.append(f"{ts_col} <= %s")
            params.append(end)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f'SELECT * FROM "{table_name}" {where_clause} ORDER BY {ts_col} ASC;'
        rows = self.execute_query(query, params)

        if not rows:
            self.logger.info(f"No data found for origin={origin} in {table_name} within given range.")
            df_dict = {ts_col: []}
        else:
            all_cols = rows[0].keys() if rows else [ts_col]
            df_dict = {col: [r[col] for r in rows] for col in all_cols}

        ts_data = TimeSeriesData(
            origin=origin,
            data=df_dict,
            input_timestamp_format=input_timestamp_format,
            output_timestamp_format=output_timestamp_format,
            time_column=ts_col,
            input_timezone=input_timezone,
            output_timezone=output_timezone,
            time_as_index=timestamp_as_index,
            origin_regex=r".+" + self.config.origin_split_char + r".+",  # or store a config param
            value_columns=[self.config.value_column],  # if you only expect "value" column
            extra_columns_handling=self.config.extra_columns_handling
        )
        return ts_data

    @check_connection
    def push_multi_origin_time_series(self, mots: MultiOriginTimeSeries):
        """Insert data from a MultiOriginTimeSeries object into DB."""
        for origin, df in mots.origin_data_map.items():
            ts_data = TimeSeriesData(
                origin=origin,
                data=df.reset_index(),
                input_timestamp_format=mots.output_timestamp_format,
                output_timestamp_format=mots.output_timestamp_format,
                time_column=self.config.timestamp_column,
                input_timezone=mots.output_timezone,
                output_timezone=mots.output_timezone,
                time_as_index=True,
                extra_columns_handling=self.config.extra_columns_handling
            )
            self.push_time_series_data_new(ts_data)

    @check_connection
    def get_multi_origin_time_series(
        self,
        origins: List[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        input_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
        output_timestamp_format: TimestampFormat = TimestampFormat.RFC3339,
        input_timezone=None,
        output_timezone=None,
        timestamp_as_index: bool = True
    ) -> MultiOriginTimeSeries:
        mots = MultiOriginTimeSeries(
            output_timestamp_format=output_timestamp_format,
            output_timezone=output_timezone,
            time_as_index=timestamp_as_index,
            extra_columns_handling=self.config.extra_columns_handling
        )

        for origin in origins:
            tsd = self.get_time_series_data(
                origin=origin,
                start=start,
                end=end,
                input_timestamp_format=input_timestamp_format,
                output_timestamp_format=output_timestamp_format,
                input_timezone=input_timezone,
                output_timezone=output_timezone,
                timestamp_as_index=timestamp_as_index
            )
            if len(tsd) > 0:
                df_export = tsd.df.reset_index()
                mots.add_data(
                    origin=origin,
                    data=df_export,
                    input_timestamp_format=output_timestamp_format,
                    time_column=self.config.timestamp_column
                )
        return mots
