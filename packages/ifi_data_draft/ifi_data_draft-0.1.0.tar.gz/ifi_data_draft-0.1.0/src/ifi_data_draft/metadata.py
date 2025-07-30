"""
metadata.py (Metadata Registry Module)

Overview:
  This module provides a metadata registry for TimescaleDB hypertables.
  It stores descriptive, human-readable metadata that PostgreSQL does not track natively,
  including column schema, datetime column, sampling interval, engineering units, and notes.

  Metadata is stored in a side-table called `_timeseries_metadata`, with one row per table.
  All writing functions (e.g., from `api.py`) update this registry; readers try the cache
  first and fall back to live SQL if needed.

Key Features:
  - Tracks schema, datetime column, row count, time range, and sampling frequency
  - Supports optional fields like engineering units and additional notes
  - Automatically computes sampling interval based on row count and time span
  - Stores metadata in JSONB format (schema and units)
  - Exports metadata to pretty-printed JSON files for inspection or backup
  - Can rebuild metadata from live SQL queries if rows are missing or outdated

Core Metadata Functions:
  - save_metadata(meta): Inserts or updates a metadata row in the registry.
  - load_metadata(table_name): Loads metadata for a specific table (or returns None).
  - update_metadata(...): Applies partial updates to an existing metadata row.
  - rebuild_metadata_row(table_name): Regenerates metadata by querying live DB stats.
  - compute_sampling_period(...): Computes average seconds/sample from row count and timespan.

Export Functions:
  - export_meta(table_name, path): Saves metadata for a single table to a JSON file.
  - export_all_metadata(path): Dumps the full `_timeseries_metadata` table to a JSON file.

Utilities:
  - pretty_print_metadata(meta): Nicely prints a metadata object to stdout.
  - ensure_meta_table(): Ensures `_timeseries_metadata` table exists on import.

"""

# -----------------------------------------------------------------------
# Imports and Logging Setup
# -----------------------------------------------------------------------

# === Standard Library ===
import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

# === Third-Party Libraries ===
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Logging Setup (for errors and info)
# -----------------------------------------------------------------------------

logger_meta = logging.getLogger("metadata")
if logger_meta.hasHandlers():
    logger_meta.handlers.clear()
logger_meta.setLevel(logging.INFO)
_logger_hdlr = logging.StreamHandler()
_logger_hdlr.setFormatter(
    logging.Formatter(
        "[META] %(asctime)s  %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
)
logger_meta.addHandler(_logger_hdlr)

# -----------------------------------------------------------------------
# Engine Helper: Create SQLAlchemy Connection
# -----------------------------------------------------------------------

load_dotenv()


def meta_engine():
    """Return a *fresh* SQLAlchemy engine pointed at our TimescaleDB."""
    port = os.getenv("DB_PORT") or "5432"
    if not port.isdigit():
        raise RuntimeError("DB_PORT environment variable must be a number")
    return create_engine(
        "postgresql+psycopg2://"
        f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('POSTGRES_DB')}",
        pool_pre_ping=True,
    )


# -----------------------------------------------------------------------
# Dataclass: TableMetadata + JSON Helpers
# -----------------------------------------------------------------------

Units = Dict[str, str | None]


@dataclass(slots=True)
class TableMetadata:
    """
    One-to-one mapping of a row in **_timeseries_metadata**.
    Only `table_name`, `schema`, `datetime_col` are mandatory.
    """

    # required
    table_name: str
    schema: Dict[str, str]
    datetime_col: str

    # auto-maintained
    row_count: Optional[int] = None
    min_time: Optional[datetime] = None
    max_time: Optional[datetime] = None
    sampling_period_sec: Optional[int] = None  # ≈ seconds / sample

    # user-defined
    units: Optional[Units] = None
    notes: Optional[str] = None

    # JSON setting
    def to_json(self) -> str:
        def _ser(o: Any):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError(o)

        return json.dumps(asdict(self), default=_ser, indent=2, sort_keys=True)

    @staticmethod
    def from_row(row) -> "TableMetadata":
        d = dict(row._mapping)
        for col in ("schema", "units"):
            if d[col] and isinstance(d[col], str):
                d[col] = json.loads(d[col])
        return TableMetadata(**d)


# -----------------------------------------------------------------------
# Metadata Table Management
# -----------------------------------------------------------------------

_META_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _timeseries_metadata (
    table_name           TEXT     PRIMARY KEY,
    schema               JSONB    NOT NULL,
    datetime_col         TEXT     NOT NULL,
    row_count            BIGINT,
    min_time             TIMESTAMPTZ,
    max_time             TIMESTAMPTZ,
    sampling_period_sec  INTEGER,
    units                JSONB,
    notes                TEXT
);
"""


def ensure_meta_table() -> None:
    """
    Make sure the metadata registry exists.

    """
    eng = meta_engine()
    insp = inspect(eng)
    if "_timeseries_metadata" not in insp.get_table_names():
        logger_meta.debug("Creating _timeseries_metadata …")
        with eng.begin() as conn:
            conn.execute(text(_META_TABLE_DDL))
    else:
        logger_meta.debug("_timeseries_metadata already present.")


# -----------------------------------------------------------------------
# Metadata Write Operations
# -----------------------------------------------------------------------


def save_metadata(meta: TableMetadata) -> None:
    """
    Insert or update the registry row for `meta.table_name`.

    """
    sql = text("""
        INSERT INTO _timeseries_metadata (
            table_name,     schema,                datetime_col,
            row_count,      min_time,              max_time,
            sampling_period_sec,                   units,      notes)
        VALUES (
            :table_name,    CAST(:schema AS jsonb),:datetime_col,
            :row_count,     :min_time,             :max_time,
            :sampling_period_sec,  CAST(:units AS jsonb), :notes)
        ON CONFLICT (table_name) DO UPDATE SET
            schema               = EXCLUDED.schema,
            datetime_col         = EXCLUDED.datetime_col,
            row_count            = EXCLUDED.row_count,
            min_time             = EXCLUDED.min_time,
            max_time             = EXCLUDED.max_time,
            sampling_period_sec  = EXCLUDED.sampling_period_sec,
            units                = EXCLUDED.units,
            notes                = EXCLUDED.notes;
    """)

    # JSON-encode the dict fields before binding
    bind = {
        "table_name": meta.table_name,
        "schema": json.dumps(meta.schema) if meta.schema else None,
        "datetime_col": meta.datetime_col,
        "row_count": meta.row_count,
        "min_time": meta.min_time,
        "max_time": meta.max_time,
        "sampling_period_sec": meta.sampling_period_sec,
        "units": json.dumps(meta.units) if meta.units else None,
        "notes": meta.notes,
    }

    with meta_engine().begin() as conn:
        conn.execute(sql, bind)
    logger_meta.debug("Saved metadata for table '%s'", meta.table_name)


# -----------------------------------------------------------------------
# Metadata Read & Update Operations
# -----------------------------------------------------------------------


def load_metadata(table_name: str) -> Optional[TableMetadata]:
    """
    Return metadata for `table_name` or **None** if not yet registered.
    """
    eng = meta_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM _timeseries_metadata WHERE table_name = :tbl"),
            {"tbl": table_name},
        ).first()
    return TableMetadata.from_row(row) if row else None


def update_metadata(
    *,
    table_name: str,
    row_count: Optional[int] = None,
    min_time: Optional[datetime] = None,
    max_time: Optional[datetime] = None,
    units: Optional[Dict[str, str]] = None,
    notes: Optional[str] = None,
) -> None:
    """
    Patch *only* the provided fields; create the row if missing.

    Automatically recomputes `sampling_period_sec` when we have both
    `row_count` and a valid time span.
    """
    meta = load_metadata(table_name) or TableMetadata(
        table_name=table_name, schema={}, datetime_col=""
    )

    # apply patches
    if row_count is not None:
        meta.row_count = row_count
    if min_time is not None:
        meta.min_time = min_time
    if max_time is not None:
        meta.max_time = max_time
    if units is not None:
        if meta.units:
            # shallow merge
            merged = meta.units | units
        else:
            merged = units
        meta.units = merged
    if notes is not None:
        meta.notes = notes

    # recompute sampling
    if (
        meta.row_count is not None
        and meta.min_time is not None
        and meta.max_time is not None
    ):
        meta.sampling_period_sec = compute_sampling_period(
            meta.row_count, meta.min_time, meta.max_time
        )

    save_metadata(meta)


def drop_metadata(table_name: str) -> None:
    """
    Delete the metadata row for `table_name`.

    This does not delete the actual table, only its metadata.
    """
    eng = meta_engine()
    with eng.begin() as conn:
        conn.execute(
            text("DELETE FROM _timeseries_metadata WHERE table_name = :t"),
            {"t": table_name},
        )
    logger_meta.debug("Dropped metadata for table '%s'", table_name)


# -----------------------------------------------------------------------
# Metadata Export Helpers
# -----------------------------------------------------------------------


def export_meta(table_name: str, path: Optional[Path] = None) -> str:
    """
    Pretty-print metadata; optionally save to a file.

    Returns the JSON string.
    """
    meta = load_metadata(table_name)
    if not meta:
        raise ValueError(f"No metadata found for table '{table_name}'.")
    js = meta.to_json()
    if path:
        path.write_text(js, encoding="utf-8")
        logger_meta.info("Exported metadata to %s", path.resolve())
    return js


def export_all_metadata(path: Path) -> None:
    """
    Export every row from _timeseries_metadata into one pretty-printed JSON file.

    Parameters
    ----------
    path : Path
        Target file location (parent dirs are created automatically).

    The helper converts Timestamp / datetime objects to ISO-8601 strings and
    leaves nested dicts (e.g. “units”) intact.
    """

    eng = meta_engine()

    # --- pull the whole registry ----------------------------------------
    with eng.connect() as conn:
        rows = (
            conn.execute(
                text('SELECT * FROM "_timeseries_metadata" ORDER BY table_name;')
            )
            .mappings()
            .all()
        )

    if not rows:
        raise ValueError("The _timeseries_metadata table is empty – nothing to export.")

    # --- ISO-convert and collect ----------------------------------------
    def iso(obj):
        return obj.isoformat() if hasattr(obj, "isoformat") else obj

    records = [{k: iso(v) for k, v in row.items()} for row in rows]

    # --- write out ------------------------------------------------------
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    logger_meta.info("Exported full metadata registry to %s", path.resolve())


# -----------------------------------------------------------------------
# Re-build / reset a single metadata row
# -----------------------------------------------------------------------


def rebuild_metadata_row(table_name: str) -> None:
    """
    Regenerate any existing _timeseries_metadata row for *table_name*
    from live SQL statistics.

    The new row contains only the auto-derived core fields
    (schema, datetime_col, row_count, min/max/sampling_period).
    “units” and “notes” are left empty so the user can fill them later.
    """
    # === Internal Modules ===
    from .api import (
        get_table_schema,
        infer_plot_columns,
        query_table_metadata,
    )  # imported here to avoid circular deps

    eng = meta_engine()

    # # Uncomment to allow this function to delete the existing row first
    # # (use with caution, e.g. if you want to reset the metadata)
    # with eng.begin() as conn:
    #     conn.execute(
    #         text('DELETE FROM _timeseries_metadata WHERE table_name = :t'),
    #         {"t": table_name},
    #     )

    # --- recompute live stats -----------------------------------------
    schema = get_table_schema(table_name)
    datetime_col, _, _ = infer_plot_columns(table_name)
    stats = query_table_metadata(table_name, datetime_col=datetime_col)

    meta = TableMetadata(
        table_name=table_name,
        schema=schema,
        datetime_col=datetime_col,
        row_count=stats["row_count"],
        min_time=stats["min_time"],
        max_time=stats["max_time"],
        sampling_period_sec=stats["sampling_period_sec"],
        units=None,
        notes=None,
    )
    save_metadata(meta)


# -----------------------------------------------------------------------
# Utility: Sampling Period, Pretty-Print
# -----------------------------------------------------------------------


def compute_sampling_period(
    row_count: int,
    min_ts: datetime,
    max_ts: datetime,
    *,
    min_rows: int = 50,
) -> Optional[float]:  # Changed return type to float
    """
    Estimate **seconds per sample**.

    • Returns *None* when fewer than `min_rows` points
    • Ignores zero / negative spans (duplicate timestamps)
    • Returns float value in seconds (can be < 1 for sub-second sampling)
    """
    if row_count < min_rows:
        return None
    span = (max_ts - min_ts).total_seconds()
    if span <= 0:
        return None
    return int((span * 1000) / (row_count - 1))


def pretty_print_metadata(meta: "TableMetadata", *, stream=sys.stdout) -> None:
    """
    Nicely dumps a TableMetadata instance to the given stream (default: stdout).
    """
    js = json.dumps(asdict(meta), indent=2, default=str)
    print(js, file=stream)


# -----------------------------------------------------------------------
# Ensure Metadata Table Exists on Import
# -----------------------------------------------------------------------
ensure_meta_table()
