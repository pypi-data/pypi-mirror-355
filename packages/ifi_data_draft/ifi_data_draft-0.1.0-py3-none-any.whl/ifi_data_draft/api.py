"""
api.py (Core API Module)

Overview:
  This module provides the core ingestion and retrieval API for working with time-series
  data stored in TimescaleDB. It is designed for **non-interactive, programmatic use**
  (e.g., CLI tools, automation scripts, pipelines), and integrates with:

    - TimescaleDB (hypertables, PostgreSQL COPY)
    - PostgREST (for data retrieval)
    - Grafana (for visualizing inserted data)
    - Local .env and YAML configs (for automation and reuse)

Key Features:
  - Loads DB and service credentials from `.env`
  - Automatically detects:
      - File delimiter (e.g., ',', ';', '\\t')
      - Datetime column (with optional override)
      - SQL schema based on pandas dtypes
  - Table management:
      - Creates tables and TimescaleDB hypertables on demand
      - Infers and verifies schema
      - Supports config reuse and custom override
  - Data insertion:
      - Bulk inserts via PostgreSQL's COPY
      - Duplicate time-range protection
      - Single-row inserts (e.g., for sensor APIs or live feeds)
  - Metadata system:
      - Automatically creates/updates metadata per table
      - Tracks row count, datetime range, sampling period, schema
      - Used by CLI for range checks, schema matching, and defaults
  - Retrieval & Export:
      - Fetches rows from PostgREST
      - Supports output to CSV, JSON, XLSX, TXT
      - Output paths are auto-generated or user-defined
  - Grafana Explore Link:
      - Builds standalone Grafana URL for ad-hoc time series inspection

Core API Functions:
  - read_csv(file_path, delimiter): Reads a CSV/TXT file into a pandas DataFrame.
  - detect_datetime_column(df, datetime_col): Determines the datetime column, or auto-detects if missing.
  - parse_datetime_column(df, datetime_col, datetime_format, timezone): Parses and localizes timestamps.
  - infer_schema(df): Infers SQL data types from a pandas DataFrame.
  - get_file_time_range(df, datetime_col): Returns min/max timestamps in the file.
  - check_duplicates(...): Checks for time-range overlaps in the DB.
  - create_table_df(...): Creates a PostgreSQL + TimescaleDB hypertable from a schema.
  - insert_data_df(...): Inserts bulk data via COPY into an existing table.
  - insert_single_row(table_name, row_dict, ...): Inserts a single time-series record.
  - list_table_columns(table_name): Lists column names for a given table.
  - get_table_schema(table_name): Gets the full schema from PostgreSQL.

Wrapper Functions:
  - create_table_from_file(...): Reads file → parses datetime → infers schema → creates table + hypertable.
  - insert_data_from_file(...): Reads file → checks duplicates → inserts rows → saves config → updates metadata.
  - insert_data(...): One-liner: reads, parses, validates, inserts if table exists.

Metadata Functions:
  - refresh_metadata(table_name): Generates or updates all metadata fields for a table.
  - update_metadata_field(table_name, field, value): Updates a specific metadata entry.
  - get_metadata_field(table_name, field): Returns a metadata field's value.
  - get_all_metadata(table_name): Returns full metadata dictionary.
  - check_sampling_interval(...): Computes and validates sampling frequency.
  - save_schema_metadata(...): Stores inferred schema for later validation.

Retrieval Functions:
  - get_data(table_name, row_limit): Retrieves raw rows from PostgREST as JSON.
  - retrieve_data(...): Converts to DataFrame and exports to file (CSV, JSON, XLSX, TXT).
  - OutputFormat(Enum): Enum wrapper for supported export formats.

Grafana Function:
  - get_grafana_url(table_name, value_col, ...): Builds a Grafana Explore link for quick visual inspection.

Note:
  - This module uses minimal third-party dependencies.
  - It is terminal- and automation-friendly.
  - Table metadata is updated automatically during insertions and is reused across the CLI system.
"""

# -----------------------------------------------------------------------------
# Imports & Dependencies
# -----------------------------------------------------------------------------

# === Standard Library ===
import os
import re
import json
import logging
from io import StringIO
from enum import Enum
from pathlib import Path
from urllib.parse import quote
from typing import Dict, Any

# === Third-Party Libraries ===
import pandas as pd
import requests
from dotenv import load_dotenv
from dateutil.parser import parse
from sqlalchemy import create_engine, text, Engine

# === Internal Modules ===
from .exceptions import (
    InvalidDelimiterError,
    DatetimeDetectionError,
    DatetimeParsingError,
    TableNameError,
)
from .metadata import (
    TableMetadata,
    load_metadata,
    save_metadata,
    drop_metadata,
    update_metadata,
    compute_sampling_period,
    ensure_meta_table,
    pretty_print_metadata,
    Units,
)

# -----------------------------------------------------------------------------
# Environment Setup & Configuration
# -----------------------------------------------------------------------------

load_dotenv()

# Database Credentials (required)
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# External Services (required)
POSTGREST_URL = os.getenv("POSTGREST_URL")
GRAFANA_BASE_URL = os.getenv("GRAFANA_BASE_URL")

# Safety check for DB variables
if not all(
    [DB_USER, DB_PASS, DB_NAME, DB_HOST, DB_PORT, POSTGREST_URL, GRAFANA_BASE_URL]
):
    raise ValueError(
        "One or more required DB environment variables are missing. Check your .env file."
    )

# === Metadata Table Bootstrapping ===
ensure_meta_table()

# -----------------------------------------------------------------------
# Database Engine (Reusable SQLAlchemy Connector)
# -----------------------------------------------------------------------


def pg_engine() -> Engine:
    """
    Build a new SQLAlchemy Engine for the Timescale/Postgres instance.

    • Uses the same env-vars as before
    • Adds pool_pre_ping=True to transparently recycle dropped connections
    """
    dsn = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(dsn, pool_pre_ping=True)


# -----------------------------------------------------------------------
# Grafana Integration: Plot Column Inference & URL Builder
# -----------------------------------------------------------------------


def infer_plot_columns(
    table_name: str, max_metric_cardinality: int = 7
) -> tuple[str, str, str | None]:
    """
    Determines appropriate plotting columns using metadata or schema fallback.

    Returns:
        (datetime_col, value_col, label_col)
        - label_col may be None if not found
    """

    # === try metadata first ===
    meta = load_metadata(table_name)
    if meta:
        datetime_col = meta.datetime_col
        numeric_cols = [
            c for c, t in meta.schema.items() if t in ("integer", "double precision")
        ]
        value_col = numeric_cols[0] if numeric_cols else None

        # simple heuristic for label: first TEXT column ≤ max_metric_cardinality
        label_col = None
        for col, dtype in meta.schema.items():
            if dtype == "text":
                uniq_sql = text(f'SELECT COUNT(DISTINCT "{col}") FROM "{table_name}"')
                with pg_engine().connect() as conn:
                    if conn.execute(uniq_sql).scalar() <= max_metric_cardinality:
                        label_col = col
                        break

        if datetime_col and value_col:
            return datetime_col, value_col, label_col

    # === fallback to original information_schema logic ===
    engine = pg_engine()
    sql = text("""
        SELECT column_name, data_type
          FROM information_schema.columns
         WHERE table_name = :tbl
         ORDER BY ordinal_position;
    """)

    datetime_col = value_col = label_col = None
    text_candidates = []

    with engine.connect() as conn:
        rows = conn.execute(sql, {"tbl": table_name}).fetchall()

        for col, dtype in rows:
            if dtype == "timestamp with time zone" and not datetime_col:
                datetime_col = col
            elif dtype in ("integer", "double precision") and not value_col:
                value_col = col
            elif dtype == "text":
                text_candidates.append(col)

        for col in text_candidates:
            count_sql = text(f'SELECT COUNT(DISTINCT "{col}") FROM "{table_name}"')
            if conn.execute(count_sql).scalar() <= max_metric_cardinality:
                label_col = col
                break

    if not datetime_col or not value_col:
        raise RuntimeError(
            f"Could not find suitable time/value columns in '{table_name}'"
        )

    return datetime_col, value_col, label_col


def get_grafana_url(
    table_name: str,
    value_col: str,
    from_time=None,
    to_time=None,
    limit: int = 1000,
    datasource: str = "TimescaleDB",
    org_id: int = 1,
) -> str:
    """
    Constructs a Grafana Explore URL for a single numeric column against the time column.

    Parameters:
      table_name  : Name of the hypertable.
      value_col   : Numeric column to plot on the Y-axis.
      from_time   : Start of time range (datetime or ISO string). If None, auto-uses min time in table.
      to_time     : End of time range. If None, auto-uses max time in table.
      limit       : Max rows to include in the query (default 1000).
      datasource  : Grafana datasource name (default "TimescaleDB").
      org_id      : Grafana organization ID (default 1).

    Returns:
      A full Grafana Explore URL string with the encoded SQL query.
    """

    datetime_col, _, _ = infer_plot_columns(table_name)
    schema = get_table_schema(table_name)
    if value_col not in schema or schema[value_col] not in (
        "integer",
        "double precision",
    ):
        raise RuntimeError(
            f"Column '{value_col}' is not a numeric column in '{table_name}'."
        )

    # Time bonds
    if from_time is None or to_time is None:
        meta = query_table_metadata(table_name, datetime_col)
        from_time = from_time or meta["min_time"]
        to_time = to_time or meta["max_time"]

    # Build query
    raw_sql = (
        f'SELECT "{datetime_col}" AS time, "{value_col}" AS value '
        f'FROM "{table_name}" '
        f"WHERE \"{datetime_col}\" BETWEEN '{from_time}' AND '{to_time}' "
        f'ORDER BY "{datetime_col}" '
        f"LIMIT {limit};"
    )

    # The URL
    payload = {
        "datasource": datasource,
        "queries": [{"refId": value_col, "rawSql": raw_sql, "format": "time_series"}],
        "range": {"from": str(from_time), "to": str(to_time)},
    }
    encoded = quote(json.dumps(payload))
    return f"{GRAFANA_BASE_URL}/explore?orgId={org_id}&limit={limit}&left={encoded}"


# -----------------------------------------------------------------------
# Input Validation & Config Handling
# -----------------------------------------------------------------------

# --- Table name validator regex (PostgreSQL-safe) ---
_TABLE_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def validate_table_name(name: str) -> None:
    """
    Validates whether the given table name conforms to PostgreSQL naming rules.

    Allowed format:
      - Starts with a lowercase letter or underscore.
      - Contains only lowercase letters, numbers, and underscores.

    Parameters:
      name : str - Table name to validate.
    """

    if not _TABLE_NAME_PATTERN.match(name):
        raise TableNameError(
            f"Invalid table name '{name}'. "
            "Names must start with lowercase letter/_ and contain only lowercase letters, digits, or underscores."
        )


# --- Default config directory ---
DEFAULT_CONFIG_DIR = Path.cwd() / "configs"
DEFAULT_CONFIG_DIR.mkdir(exist_ok=True, parents=True)


def save_config_file(cfg: dict, table_name: str, path: Path | None = None) -> None:
    """
    Saves the given config dictionary to a JSON file under the /configs directory.

    If no explicit path is provided, the default location will be:
      ./configs/<table_name>.json

    """
    target = path or (DEFAULT_CONFIG_DIR / f"{table_name}.json")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w") as f:
            json.dump(cfg, f, indent=2)
        logger.info("Saved config to: %s", target)
    except Exception as e:
        logger.error("Failed to save config to %s: %s", target, e)
        raise


# -----------------------------------------------------------------------------
# Logging Setup (for errors and info)
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
# Clear any existing handlers to avoid duplicate logging in interactive sessions
if logger.hasHandlers():
    logger.handlers.clear()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(levelname)s] %(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------
# File Reading & Delimiter Detection
# -----------------------------------------------------------------------


def auto_detect_delimiter(file_path: str) -> str | None:
    """
    Auto-detects the delimiter used in a CSV/TXT file.

    Scans the first line for common delimiters: ',', ';', '\\t', '|'.

    Parameters:
      file_path : str - Path to the CSV or TXT file.

    Returns:
        A string delimiter (e.g. ',') or None if detection failed.
    """
    file_path = Path(file_path)
    try:
        test_df = pd.read_csv(file_path, sep=None, engine="python", nrows=5)
        if len(test_df.columns) > 1:
            delimiters = [",", ";", "\t", "|"]
            with file_path.open("r") as f:
                first_line = f.readline()
                for delim in delimiters:
                    if delim in first_line:
                        return delim
        return None
    except Exception as e:
        logger.error("Delimiter auto-detection failed: %s", e)
        return None


def read_csv(file_path: str, delimiter: str | None = None) -> pd.DataFrame:
    """
    Reads a CSV or TXT file into a pandas DataFrame.

    Parameters:
        file_path : Path to the file.
        delimiter : Optional override. If None, auto-detection is attempted.

    Returns:
        A pandas DataFrame.
    """
    file_path = Path(file_path)
    if delimiter is None:
        delimiter = auto_detect_delimiter(file_path)
        if delimiter:
            logger.info("Auto-detected delimiter: '%s'", delimiter)
        else:
            logger.error("Could not auto-detect delimiter for file: '%s'", file_path)
            raise InvalidDelimiterError(
                f"Delimiter could not be auto-detected for file '{file_path}'."
            )

    try:
        df = pd.read_csv(file_path, delimiter=delimiter)
        logger.info(
            "CSV file '%s' successfully read with delimiter '%s'.", file_path, delimiter
        )
        return df
    except Exception as e:
        logger.error("Error reading CSV file '%s': %s", file_path, e)
        raise


# -----------------------------------------------------------------------
# Datetime Detection & Parsing
# -----------------------------------------------------------------------


def is_timestamp(series: pd.Series, threshold: float = 0.9) -> bool:
    """
    Returns True if a Series is likely datetime.

    - Skips numeric columns
    - Samples up to 100 values
    - At least `threshold` (default 90%) must parse cleanly
    - Uses `dateutil.parser.parse` to attempt parsing as datetimes.
    """

    if pd.api.types.is_numeric_dtype(series):
        return False

    successes = 0
    series_clean = series.dropna()
    total_samples = min(100, len(series_clean))
    if total_samples == 0:
        return False

    sample = (
        series_clean.sample(total_samples, random_state=42)
        if len(series_clean) > total_samples
        else series_clean
    )

    for val in sample:
        try:
            parse(str(val), fuzzy=False)
            successes += 1
        except:
            continue

    return (successes / total_samples) >= threshold


def auto_detect_datetime_cols(df: pd.DataFrame) -> list:
    """
    Scans all columns in a DataFrame and returns a list of likely datetime fields.

    Notes:
      - Uses `is_timestamp()` on each column to detect datetime-like values.
      - Returns multiple candidates.
      - Used internally by `detect_datetime_column()` when no explicit column is provided.
    """
    candidate_cols = [col for col in df.columns if is_timestamp(df[col])]
    return candidate_cols


def detect_datetime_column(df: pd.DataFrame, datetime_col: str | None = None) -> str:
    """
    Identifies the datetime column in a DataFrame.

    If `datetime_col` is given, it is validated. Otherwise, auto-detection is attempted.
    """
    if datetime_col:
        if is_timestamp(df[datetime_col]):
            logger.info("Using explicitly provided datetime column: '%s'", datetime_col)
            return datetime_col
        else:
            logger.error("Provided datetime column '%s' is not valid.", datetime_col)
            raise DatetimeDetectionError(
                f"Provided datetime column '{datetime_col}' is invalid."
            )

    detected_cols = auto_detect_datetime_cols(df)
    if len(detected_cols) == 1:
        logger.info("Datetime column auto-detected: '%s'", detected_cols[0])
        return detected_cols[0]
    elif len(detected_cols) == 0:
        logger.error("No datetime columns detected automatically.")
        raise DatetimeDetectionError("No datetime columns detected automatically.")
    else:
        logger.error("Multiple datetime columns detected: %s", detected_cols)
        raise DatetimeDetectionError(
            f"Multiple datetime columns detected: {detected_cols}"
        )


def parse_datetime_column(
    df: pd.DataFrame,
    datetime_col: str,
    format: str | None = None,
    timezone: str = "UTC",
) -> pd.DataFrame:
    """
    Parses and localizes a datetime column in the DataFrame.

    Parameters:
        df (pd.DataFrame): The DataFrame to process.
        datetime_col (str): The name of the datetime column to parse.
        format (str | None): Optional datetime format string. If None, automatic parsing is attempted.
        timezone (str): Timezone to localize to (default: 'UTC').
    """
    try:
        if format:
            df[datetime_col] = pd.to_datetime(
                df[datetime_col], format=format, errors="raise", dayfirst=True
            )
            logger.info(
                "Datetime column '%s' parsed using format '%s'.", datetime_col, format
            )
        else:
            df[datetime_col] = pd.to_datetime(
                df[datetime_col], errors="raise", dayfirst=True
            )
            logger.info("Datetime column '%s' parsed automatically.", datetime_col)

        df[datetime_col] = df[datetime_col].dt.tz_localize(
            timezone, ambiguous="raise", nonexistent="raise"
        )
        logger.info(
            "Datetime column '%s' localized to timezone '%s'.", datetime_col, timezone
        )

        return df
    except Exception as e:
        logger.error(
            "Failed to parse/localize datetime column '%s': %s", datetime_col, e
        )
        raise DatetimeParsingError(
            f"Parsing datetime column '{datetime_col}' failed: {e}"
        )


# -----------------------------------------------------------------------
# Table Schema Utilities
# -----------------------------------------------------------------------


def list_table_columns(table_name: str) -> list[str]:
    """
    Returns a list of column names for `table_name` in the public schema.

    Parameters:
        table_name : str - Table name to inspect.

    Returns:
        List of column names in ordinal order.
    """
    validate_table_name(table_name)
    engine = pg_engine()
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :tbl
        ORDER BY ordinal_position;
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql, {"tbl": table_name}).fetchall()]


def get_table_schema(table_name: str) -> dict[str, str]:
    """
    Returns a mapping of column_name -> data_type for an existing table.

    Example output:
        {
            'time': 'timestamp with time zone',
            'temperature': 'double precision',
            ...
        }
    """
    validate_table_name(table_name)
    engine = pg_engine()
    sql = text("""
        SELECT column_name, data_type
          FROM information_schema.columns
         WHERE table_schema='public'
           AND table_name = :tbl
         ORDER BY ordinal_position;
    """)
    with engine.connect() as conn:
        return {row[0]: row[1] for row in conn.execute(sql, {"tbl": table_name})}


def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """
    Infers PostgreSQL-compatible SQL types from a pandas DataFrame.

    Mapping:
        - int      -> INT
        - float    -> DOUBLE PRECISION
        - bool     -> BOOLEAN
        - datetime -> TIMESTAMPTZ
        - other    -> TEXT

    Returns:
        Dict[str, str] mapping of column names to SQL types.
    """
    schema_map = {}
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        # Map pandas types to PostgreSQL-compatible types
        if "int" in dtype_str:
            schema_map[col] = "INT"
        elif "float" in dtype_str:
            schema_map[col] = "DOUBLE PRECISION"
        elif "bool" in dtype_str:
            schema_map[col] = "BOOLEAN"
        elif "datetime64[ns, UTC]" in dtype_str:
            schema_map[col] = "TIMESTAMPTZ"
        else:
            schema_map[col] = "TEXT"
    logger.info("Schema inferred: %s", schema_map)
    return schema_map


# -----------------------------------------------------------------------
# Table Creation (Hypertable Initialization)
# -----------------------------------------------------------------------


def create_table_df(
    df: pd.DataFrame,
    schema_map: Dict[str, str],
    table_name: str,
    datetime_col: str,
    chunk_days: int = 1,
) -> None:
    """
    Creates a new SQL table and transforms it into a TimescaleDB hypertable.

    Parameters:
        df           : pandas DataFrame (used to validate columns)
        schema_map   : Dict of column_name → SQL type (from `infer_schema`)
        table_name   : Target name of the table
        datetime_col : Column to use as time axis
        chunk_days   : Hypertable partition size (in days)
    """
    engine = pg_engine()

    # Check if the table already exists.
    check_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = :tbl
        );
    """)

    with engine.connect() as conn:
        exists = conn.execute(check_sql, {"tbl": table_name}).scalar()
        if exists:
            raise ValueError(
                f"Table '{table_name}' already exists. Aborting to avoid overwriting."
            )

    # Build CREATE TABLE SQL
    col_defs = ",\n  ".join([f'"{col}" {dtype}' for col, dtype in schema_map.items()])
    create_sql = f'CREATE TABLE "{table_name}" (\n  {col_defs}\n);'

    # Execute table + hypertable creation
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        logger.info("Table '%s' created successfully.", table_name)

        # Create a TimescaleDB hypertable on "<table_name>" using "<datetime_col>" and chunk interval.
        hypertable_sql = (
            "SELECT create_hypertable("
            f"'{table_name}', '{datetime_col}', "
            f"chunk_time_interval => interval '{chunk_days} day', "
            "if_not_exists => true);"
        )
        conn.execute(text(hypertable_sql))
        logger.info(
            "Hypertable created on '%s' (time column: '%s', chunk: %d day).",
            table_name,
            datetime_col,
            chunk_days,
        )


# -----------------------------------------------------------------------
# Data Insertion -- Dataframe
# -----------------------------------------------------------------------


def insert_data_df(df: pd.DataFrame, table_name: str) -> None:
    """
    Inserts a DataFrame into an existing table using PostgreSQL's COPY.

    Parameters:
        df         : Data to insert
        table_name : Existing TimescaleDB table

    Skips insert if DataFrame is empty.
    Raises exceptions on COPY failure.
    """
    if df.empty:
        logger.info("DataFrame is empty. Skipping data insertion.")
        return

    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    columns_str = ",".join([f'"{col}"' for col in df.columns])
    copy_sql = f'COPY "{table_name}" ({columns_str}) FROM STDIN WITH (FORMAT csv)'

    engine = pg_engine()
    raw_conn = engine.raw_connection()

    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(copy_sql, buffer)
        raw_conn.commit()
        logger.info(
            "Successfully inserted %d rows into table '%s'.", len(df), table_name
        )
    except Exception as e:
        raw_conn.rollback()
        logger.error("Error inserting data into table '%s': %s", table_name, e)
        raise
    finally:
        raw_conn.close()


# -----------------------------------------------------------------------
# Metadata Helpers (Duplicate Check, Stats, Metadata Maintenance)
# -----------------------------------------------------------------------


def get_file_time_range(df: pd.DataFrame, datetime_col: str) -> tuple:
    """
    Returns the (min, max) timestamps from a datetime column.

    Parameters:
        df           : pandas DataFrame
        datetime_col : Name of the datetime column

    Returns:
        (file_min, file_max)
    """
    file_min = df[datetime_col].min()
    file_max = df[datetime_col].max()
    return file_min, file_max


def check_duplicates(table_name: str, datetime_col: str, file_min, file_max) -> bool:
    """
    Checks whether the target table already contains rows within the given time range.

    Parameters:
        table_name   : TimescaleDB table
        datetime_col : Column used for time comparisons
        file_min     : Start of input data range
        file_max     : End of input data range

    Returns:
        True if overlap exists, False otherwise.
    """
    engine = pg_engine()
    query_sql = text(f"""
        SELECT COUNT(*) FROM "{table_name}" 
        WHERE "{datetime_col}" BETWEEN :file_min AND :file_max;
    """)
    with engine.connect() as conn:
        count = conn.execute(
            query_sql, {"file_min": file_min, "file_max": file_max}
        ).scalar()
    logger.info(
        "Found %d rows in table '%s' with %s between %s and %s.",
        count,
        table_name,
        datetime_col,
        file_min,
        file_max,
    )
    return count > 0


def query_table_metadata(table_name: str, datetime_col: str | None = None) -> dict:
    """
    Returns basic stats for a table, using metadata if available.

    Output:
        {
            "row_count": int,
            "min_time": datetime,
            "max_time": datetime,
            "sampling_period_sec": float | None,
            "datetime_col": str
        }
    """
    # === fast-path : cached row ===
    meta = load_metadata(table_name)
    if meta and (datetime_col is None or datetime_col == meta.datetime_col):
        return {
            "row_count": meta.row_count,
            "min_time": meta.min_time,
            "max_time": meta.max_time,
            "sampling_period_sec": meta.sampling_period_sec,
            "datetime_col": meta.datetime_col,
        }

    # === slow-path : live SQL ===
    # either no row yet or caller wants stats on another column
    if datetime_col is None:
        # need a column to query – reuse infer_plot_columns helper
        datetime_col, _, _ = infer_plot_columns(table_name)

    engine = pg_engine()
    sql = text(f"""
        SELECT COUNT(*)        AS row_count,
               MIN("{datetime_col}") AS min_time,
               MAX("{datetime_col}") AS max_time
          FROM "{table_name}";
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).first()

    stats = {
        "row_count": row._mapping["row_count"],
        "min_time": row._mapping["min_time"],
        "max_time": row._mapping["max_time"],
        "sampling_period_sec": None,  # filled below
        "datetime_col": datetime_col,
    }

    # try to derive sampling period when there are enough points
    stats["sampling_period_sec"] = compute_sampling_period(
        stats["row_count"], stats["min_time"], stats["max_time"]
    )

    # write (or refresh) the metadata row so next call is instant
    if meta is None or meta.datetime_col == datetime_col:
        schema = get_table_schema(table_name)
        save_metadata(
            TableMetadata(
                table_name=table_name,
                schema=schema,
                datetime_col=datetime_col,
                row_count=stats["row_count"],
                min_time=stats["min_time"],
                max_time=stats["max_time"],
                sampling_period_sec=stats["sampling_period_sec"],
            )
        )
    return stats


def _refresh_or_create_metadata(
    df: pd.DataFrame,
    *,
    table_name: str,
    datetime_col: str,
    schema: dict[str, str],
) -> None:
    """
    Updates or creates the _timeseries_metadata row for a table after data insert.

    - If table is new, creates a full metadata record
    - If table exists, patches row count, time bounds, and recomputes sampling
    """

    # basic stats for this batch
    batch_rows = len(df)
    batch_min, batch_max = df[datetime_col].min(), df[datetime_col].max()

    meta = load_metadata(table_name)

    # first time this table shows up -> create full record
    if meta is None:
        meta = TableMetadata(
            table_name=table_name,
            schema=schema,
            datetime_col=datetime_col,
            row_count=batch_rows,
            min_time=batch_min,
            max_time=batch_max,
            sampling_period_sec=compute_sampling_period(
                batch_rows, batch_min, batch_max
            ),
            units=None,  # user can update later
            notes=None,  # user can update later
        )
        save_metadata(meta)
        logger.info("Metadata row created for '%s'.", table_name)
        return

    # table already registered -> patch evolving fields
    meta.row_count = (meta.row_count or 0) + batch_rows
    meta.min_time = min(meta.min_time, batch_min) if meta.min_time else batch_min
    meta.max_time = max(meta.max_time, batch_max) if meta.max_time else batch_max
    meta.sampling_period_sec = compute_sampling_period(
        meta.row_count, meta.min_time, meta.max_time
    )

    save_metadata(meta)
    logger.info("Metadata row updated for '%s'.", table_name)


# -----------------------------------------------------------------------------
# Wrapper Functions (Public Ingestion API)
# -----------------------------------------------------------------------------


def create_table_from_file(
    file_path: str,
    table_name: str,
    delimiter: str | None = None,
    datetime_col: str | None = None,
    format: str | None = None,
    timezone: str = "UTC",
    chunk_days: int = 7,
    config: bool = False,
    config_path: Path | None = None,
    derive_stats: bool = False,
    units: Units | None = None,
) -> None:
    """
    Reads a file, infers schema, creates a hypertable, and writes metadata.

     This function performs the full pipeline:
       - Reads the input file using the specified or auto-detected delimiter.
       - Detects (or validates) the datetime column for time-series indexing.
       - Parses and localizes the datetime values to the given timezone.
       - Infers a PostgreSQL-compatible schema based on DataFrame dtypes.
       - Creates the table in the database and converts it to a hypertable using TimescaleDB.
       - Registers an initial metadata row in `_timeseries_metadata`.
       - Optionally saves a configuration file with all settings for reuse.

     Parameters:
       file_path     : Path to the input file (.csv or .txt).
       table_name    : Name of the new table to create (must follow PostgreSQL naming rules).
       delimiter     : Optional column separator (e.g., ',', ';', '\\t'); auto-detected if None.
       datetime_col  : Optional name of the timestamp column; auto-detected if not provided.
       format        : Optional datetime format string; uses pandas auto-parsing if omitted.
       timezone      : Timezone for localizing datetime values (default: 'UTC').
       chunk_days    : Chunk size in days for hypertable partitioning (default: 7).
       config        : If True, saves a JSON file with these settings under `configs/` (default: False).
       config_path   : Optional custom path to save the config JSON instead of default location.
       derive_stats  : False read only header + one row; write a metadata stub with. (default)
                       True  read *all* rows, compute row-count, min/max time, sampling period.


     Raises:
       TableNameError         : If `table_name` is invalid.
       InvalidDelimiterError  : If no suitable delimiter is provided or detected.
       DatetimeDetectionError : If no suitable datetime column can be determined.
       DatetimeParsingError   : If parsing or timezone localization fails.
       ValueError             : If a table with the same name already exists in the DB.
    """

    validate_table_name(table_name)
    df = read_csv(file_path, delimiter=delimiter)
    datetime_col = detect_datetime_column(df, datetime_col)
    df = parse_datetime_column(df, datetime_col, format=format, timezone=timezone)
    schema = infer_schema(df)
    create_table_df(df, schema, table_name, datetime_col, chunk_days)

    # create a bare metadata record for this table
    if derive_stats:
        row_count = len(df)
        file_min, file_max = get_file_time_range(df, datetime_col)
        sampling = compute_sampling_period(row_count, file_min, file_max)
    else:
        row_count = 0
        file_min = file_max = None

    meta = TableMetadata(
        table_name=table_name,
        schema=schema,
        datetime_col=datetime_col,
        row_count=row_count,
        min_time=file_min,
        max_time=file_max,
        sampling_period_sec=compute_sampling_period(row_count, file_min, file_max),
        units=units,
        notes=None,  # user can update later
    )
    save_metadata(meta)
    logger.info("Metadata row written for '%s'.", table_name)
    pretty_print_metadata(meta)

    if config:
        cfg = {
            "file_path": str(file_path),
            "delimiter": delimiter,
            "datetime_col": datetime_col,
            "datetime_format": format,
            "timezone": timezone,
            "chunk_days": chunk_days,
            "allow_duplicates": False,
        }
        save_config_file(cfg, table_name, path=config_path)


def insert_data(
    file_path: str,
    table_name: str,
    delimiter: str | None = None,
    datetime_col: str | None = None,
    format: str | None = None,
    timezone: str = "UTC",
    allow_duplicates: bool = False,
    config: bool = False,
    config_path: Path | None = None,
) -> None:
    """
    Simplified wrapper to insert file data into an *existing* table.

    Skips insertion if duplicate timestamps are detected (unless overridden).

    This function:
      - Loads and parses the file.
      - Detects the datetime column and localizes timestamps.
      - Verifies that the target table exists.
      - Skips insertion if overlapping data is already present (unless `allow_duplicates=True`).
      - Inserts the data using PostgreSQL COPY.
      - Logs final row count and time range after insertion.

    Parameters:
      file_path        : Path to the CSV or TXT file.
      table_name       : Name of the existing table to insert into.
      delimiter        : Optional file delimiter; auto-detected if None.
      datetime_col     : Optional datetime column name; auto-detected if None.
      format           : Optional format for datetime parsing.
      timezone         : Timezone to localize timestamps (default: 'UTC').
      allow_duplicates : Whether to skip duplicate checks (default: False).

    Raises:
      Exception if table doesn't exist or insertion fails.
    """

    validate_table_name(table_name)
    df = read_csv(file_path, delimiter)
    col = detect_datetime_column(df, datetime_col)
    df = parse_datetime_column(df, col, format=format, timezone=timezone)

    engine = pg_engine()
    exists = (
        engine.connect()
        .execute(
            text(
                "SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name=:tbl)"
            ),
            {"tbl": table_name},
        )
        .scalar()
    )

    if not exists:
        print(f"Table '{table_name}' not found.")
        print(
            f"  To create it, run:\n    create_table_from_file('{file_path}', '{table_name}')"
        )
        return

    print(f"Table '{table_name}' found. Inserting data…")

    if not allow_duplicates:
        file_min, file_max = get_file_time_range(df, col)
        if check_duplicates(table_name, col, file_min, file_max):
            print(
                f"Detected existing data in '{table_name}' between {file_min} and {file_max}. Skipping insert."
            )
            return

    insert_data_df(df, table_name)

    _refresh_or_create_metadata(
        df,
        table_name=table_name,
        datetime_col=datetime_col,
        schema=get_table_schema(table_name),
    )

    pretty_print_metadata(load_metadata(table_name))

    if config:
        cfg = {
            "file_path": str(file_path),
            "delimiter": delimiter,
            "datetime_col": datetime_col,
            "datetime_format": format,
            "timezone": timezone,
            "chunk_days": None,
            "allow_duplicates": allow_duplicates,
        }
        save_config_file(cfg, table_name, path=config_path)


def insert_data_from_file(
    file_path: str,
    table_name: str,
    delimiter: str | None = None,
    datetime_col: str | None = None,
    format: str | None = None,
    timezone: str = "UTC",
    allow_duplicates: bool = False,
    config: bool = False,
    config_path: Path | None = None,
) -> None:
    """
    Wrapper to create a table and insert data into it.

    Performs:
      - File reading, delimiter detection.
      - Datetime parsing and timezone localization.
      - Duplicate checking over the datetime range (optional).
      - PostgreSQL COPY-based data insertion.
      - Logs row count and time range post-insert.
      - Optionally writes a config file.

    Parameters:
      file_path        : Input file to insert.
      table_name       : Target table name (must exist).
      delimiter        : Optional field delimiter (auto-detected if None).
      datetime_col     : Optional datetime column name (auto-detected if None).
      format           : Optional datetime format string.
      timezone         : Timezone to localize timestamps (default: 'UTC').
      allow_duplicates : Whether to allow overlapping time range insertions (default: False).
      config           : Whether to save a reusable config file (default: False).
      config_path      : Optional override path for saving the config JSON.

    Raises:
      Exception if the insert fails or duplicate check blocks the operation.
    """
    validate_table_name(table_name)
    df = read_csv(file_path, delimiter=delimiter)
    datetime_col = detect_datetime_column(df, datetime_col)
    df = parse_datetime_column(df, datetime_col, format=format, timezone=timezone)

    file_min, file_max = get_file_time_range(df, datetime_col)

    # Check for duplicates using the datetime column as the primary key.
    if not allow_duplicates and check_duplicates(
        table_name, datetime_col, file_min, file_max
    ):
        logger.warning(
            "Data within the time range %s to %s already exists in table '%s'. Insertion aborted.",
            file_min,
            file_max,
            table_name,
        )
        return  # Skip insertion

    # Proceed to insert data.
    insert_data_df(df, table_name)

    _refresh_or_create_metadata(
        df,
        table_name=table_name,
        datetime_col=datetime_col,
        schema=get_table_schema(table_name),
    )

    pretty_print_metadata(load_metadata(table_name))

    if config:
        cfg = {
            "file_path": str(file_path),
            "delimiter": delimiter,
            "datetime_col": datetime_col,
            "datetime_format": format,
            "timezone": timezone,
            "chunk_days": None,
            "allow_duplicates": allow_duplicates,
        }
        save_config_file(cfg, table_name, path=config_path)


def insert_single_row(
    table_name: str,
    row: Dict[str, Any],
    datetime_col: str | None = None,
    format: str | None = None,
    timezone: str = "UTC",
    allow_duplicates: bool = False,
) -> None:
    """
    Inserts a single row (dict of values) into a hypertable.

    This is intended for live-sensor or manual single-point ingestion without
    writing/reading an external file.

    Steps performed:
      1. Validates `table_name` against Postgres naming rules.
      2. Wraps the single `row` (a dict) in a one-row pandas DataFrame.
      3. Auto-detects or validates the datetime column.
      4. Parses and localizes the timestamp.
      5. Optionally checks for duplicates by timestamp (skips insert if found).
      6. Leverages the high-performance `insert_data_df()` COPY path to inject the row.

    Parameters:
      table_name       : Name of the existing hypertable to insert into.
      row              : Dict mapping column names -> values for the new row.
      datetime_col     : Optional explicit name of the timestamp column; if None, auto-detected.
      format           : Optional `strftime` format for parsing the timestamp; if None, auto-parsed.
      timezone         : Timezone for localization (default: 'UTC').
      allow_duplicates : If False (default), skips insertion when a row with the same timestamp exists.

    Raises:
      TableNameError           : If `table_name` is invalid.
      DatetimeDetectionError   : If the datetime column cannot be determined.
      DatetimeParsingError     : If timestamp parsing/localization fails.
      Exception                : If the COPY insertion fails.
    """

    validate_table_name(table_name)
    df = pd.DataFrame([row])
    col = detect_datetime_column(df, datetime_col)
    df = parse_datetime_column(df, col, format=format, timezone=timezone)

    if not allow_duplicates:
        tmin, tmax = get_file_time_range(df, col)
        if check_duplicates(table_name, col, tmin, tmax):
            logger.info(
                "Skipping insert: row with timestamp %s already exists in '%s'.",
                tmin,
                table_name,
            )
            return

    insert_data_df(df, table_name)
    logger.info(
        "Single row inserted into '%s' (timestamp column: '%s').", table_name, col
    )

    _refresh_or_create_metadata(
        df,
        table_name=table_name,
        datetime_col=col,
        schema=get_table_schema(table_name),
    )

    pretty_print_metadata(load_metadata(table_name))


# -----------------------------------------------------------------------
# Data Retrieval via PostgREST
# -----------------------------------------------------------------------


class OutputFormat(Enum):
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    TXT = "txt"


def get_data(table_name: str, row_limit: int | None = None) -> dict:
    """
    Fetch raw JSON data from PostgREST endpoint for a specific table.

    Parameters:
      table_name : Name of the TimescaleDB table to retrieve.
      row_limit  : Optional integer row limit for pagination or previewing.

    Returns:
      Dictionary of rows (parsed from JSON) for further processing.
    """
    params = {}
    if row_limit is not None:
        params["limit"] = row_limit

    try:
        response = requests.get(f"{POSTGREST_URL}/{table_name}", params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch data from PostgREST: %s", e)
        raise ValueError(f"PostgREST fetch failed: {e}")

    data = response.json()
    if not data:
        raise ValueError(f"No data returned from table '{table_name}'")

    return data


def retrieve_data(
    table_name: str,
    row_limit: int | None = None,
    output_format: OutputFormat = OutputFormat.CSV,
    output_path: Path | None = None,
) -> Path:
    """
    Retrieves data from a table via PostgREST and exports it to file in the requested format.

    Parameters:
      table_name    : Name of the table to retrieve data from.
      row_limit     : Maximum number of rows to fetch; None retrieves all.
      output_format : One of ['csv', 'json', 'xlsx', 'txt'] (default: 'csv').
      output_path   : Optional full path to save output; defaults to ./<table>.<ext>.

    Returns:
      Path to the saved file.

    Raises:
      ValueError for unsupported formats or fetch/export failures.
    """
    df = pd.DataFrame(get_data(table_name, row_limit=row_limit))

    supported_formats = [format.value for format in OutputFormat]
    if output_format.value not in supported_formats:
        raise ValueError(f"Unsupported export format: '{output_format.value}'")

    ext = "xlsx" if output_format == "xlsx" else output_format
    if output_path is None:
        output_path = Path(f"{table_name}.{ext}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if output_format == OutputFormat.CSV:
            df.to_csv(output_path, index=False)
        elif output_format == OutputFormat.JSON:
            df.to_json(output_path, orient="records", indent=2)
        elif output_format == OutputFormat.XLSX:
            df.to_excel(output_path, index=False)
        elif output_format == OutputFormat.TXT:
            df.to_csv(output_path, sep="\t", index=False)
    except Exception as e:
        logger.error("Error exporting data to %s: %s", output_format, e)
        raise

    logger.info("Exported %d rows from '%s' to '%s'.", len(df), table_name, output_path)
    return output_path


def table_exists(table_name: str) -> bool:
    """
    Checks if a table exists in the PostgreSQL database.

    Parameters:
        table_name : str - Name of the table to check.

    Returns:
        True if the table exists, False otherwise.
    """
    engine = pg_engine()
    sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = :tbl
        );
    """)
    with engine.connect() as conn:
        return conn.execute(sql, {"tbl": table_name}).scalar()


def drop_table(table_name: str) -> None:
    """
    Drops a table from the PostgreSQL database.

    Parameters:
        table_name : str - Name of the table to drop.

    Raises:
        ValueError if the table does not exist.
    """
    if not table_exists(table_name):
        raise ValueError(f"Table '{table_name}' does not exist.")

    engine = pg_engine()
    sql = text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
    with engine.begin() as conn:
        conn.execute(sql)
    logger.info("Table '%s' dropped successfully.", table_name)
    drop_metadata(table_name)


# -----------------------------------------------------------------------------
# API-to-CLI Mapping Reference
#
# The CLI menu wraps around these core API functions. Each CLI option maps
# directly to one or more non-interactive API calls listed below.
#
# ┌──────────────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
# │                   CLI Option                 │                        API Function(s)                      │
# ├──────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
# │ 1. Create Table Only                         │ create_table_from_file(file_path, table_name, …)            │
# │ 2. Insert Data to an existing table          │ insert_data(file_path, table_name, …)                       │
# │ 3. Insert Single Row                         │ insert_single_row(table_name, row_dict, …)                  │
# │ 4. Create + Insert + Config Save             │ create_table_from_file(…) + insert_data_from_file(…)        │
# │ 5. Create + Insert + Config Save (1 func)    │ insert_data_from_file(file_path, table_name, config=True)   │
# │ 6. Export Table to File                      │ retrieve_data(table_name, row_limit, output_format, …)      │
# │ 7. Generate Grafana Link                     │ get_grafana_url(table_name, value_col, …)                   │
# └──────────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
#
# Notes:
# - Configs are saved per-table to ./configs/ unless overridden.
# - retrieve_data() supports file formats: csv, json, xlsx, txt.
# - retrieve_data() auto-generates output paths if none provided.
# - Output directory is created if missing.
# - Grafana URL builder is a standalone function, works independently of data export.
# - Expansion of the Metadata.
# - Metadata is automatically created or updated after any insert.
#   This includes row count, datetime range, sampling period, and schema.
# - Metadata can be used to prefill CLI defaults, compute ranges, or validate inserts.
# -----------------------------------------------------------------------------
