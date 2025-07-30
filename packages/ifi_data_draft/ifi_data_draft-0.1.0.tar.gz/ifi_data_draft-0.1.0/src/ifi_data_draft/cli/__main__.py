"""
cli.py (Interactive Command-Line Interface)

Overview:
  This script provides an interactive, terminal-based command-line interface (CLI)
  for ingesting, managing, and exporting time-series data in TimescaleDB, utilizing
  the underlying functionalities of the `api.py` module.

  It offers guided workflows for:
    - Creating hypertables from CSV/TXT files
    - Inserting bulk or single-row data into existing hypertables
    - Combined table creation and data insertion
    - Retrieving and exporting data via PostgREST
    - Generating interactive Grafana Explore URLs
    - Managing and updating table metadata

Core Design:
  - Step-by-step, interactive prompts with built-in backtracking and safe exits
  - Auto-detection with optional user overrides:
      - File delimiters
      - Datetime columns and formats
  - Comprehensive input validation:
      - Table names, file paths, data types, datetime parsing
  - Reusable per-table JSON configuration files:
      - Save/load default settings (file path, delimiter, datetime info)
  - Integration with Grafana for dynamic visualization links
  - Interactive metadata management for validating and auditing table info

Key CLI Operations:
  1. Create Table Only
      - Interactive guided creation of TimescaleDB hypertables from CSV/TXT files
  2. Insert Data Only
      - Insert bulk rows into existing hypertables with duplicate checks
  3. Insert Single Row
      - Manual entry of single-row data, ideal for live sensor feeds
  4. Create Table + Insert Data
      - Combined operation to streamline new table creation and data insertion
  5. Retrieve Data
      - Export hypertable data via PostgREST to CSV, JSON, XLSX, TXT formats
  6. Generate Grafana Link
      - Create direct Grafana Explore URLs with custom columns, limits, and ranges
  7. Metadata Tools
      - Interactive menu to view, modify, export, regenerate, or delete table metadata
  8. Exit
      - Safely terminate the CLI session

Interactive Menu Functions:
  - Table & Data Operations:
      - run_create_table()
      - run_insert_data()
      - run_insert_single_row()
      - run_create_and_insert()
  - Data Retrieval & Visualization:
      - run_retrieve_data()
      - run_grafana_link()
  - Metadata Management:
      - run_metadata_menu() (View, modify, regenerate, export, delete metadata)
  - Main Loop & Entrypoint:
      - main_menu() — Display and handle user choices
      - cli_loop()  — Main interactive loop managing menu dispatching
      - main()      — CLI script entrypoint

Prompt Utilities:
  - Generic Prompts:
      - prompt(msg, default) — Generalized user input with default, back, exit handling
      - confirm_prompt(msg)  — Yes/No prompts with exit and back navigation
      - yes_no_prompt(msg)   — Simplified yes/no confirmation
  - Specialized Input Helpers:
      - ask_date(label, min_dt, max_dt) — Collect calendar date inputs for date-range queries

Picker Utilities (Interactive):
  - File & Format Selection:
      - pick_file_path()                  — Choose and validate CSV/TXT file path
      - pick_delimiter(file_path)         — Auto-detect and confirm file delimiter
  - Datetime Handling:
      - pick_datetime_column_interactive(df) — Auto or manual datetime column selection
      - pick_datetime_format_menu()          — Common datetime format options or custom input
      - pick_timezone_menu(default_tz)       — Choose timezone from common presets or custom
  - Hypertable Config:
      - pick_chunk_interval_menu(default) — Select TimescaleDB chunk interval in days
      - pick_allow_duplicates()           — Decide whether duplicate time-ranges are permitted
  - Table Management:
      - table_selection_menu(title)       — Interactive table selection from existing DB tables

Helper & Validation Functions:
  - Config Management:
      - ensure_config_dir()               — Ensure presence of config directory
      - list_config_files()               — List available per-table JSON configs
      - pick_config_file()                — Choose and load existing JSON config
  - Database Operations:
      - validate_table_name(name)         — Validate table naming according to PostgreSQL rules
      - list_tables_in_db(include_meta)   — Retrieve existing public tables from DB
      - find_matching_tables(cols, dt_col)— Identify tables matching a given schema
      - fetch_data(table_name, row_limit) — Fetch data via PostgREST for preview or export

Dependencies & Environment:
  - Integrates with:
      - `api.py` for core TimescaleDB/PostgREST interactions
      - `metadata.py` for centralized table metadata management
      - `.env` file for DB and service credential management
  - Minimal third-party requirements (pandas, requests, dotenv, SQLAlchemy)
  - Designed for Python 3.10+ (type annotations, modern syntax)
  - Terminal and automation friendly with robust logging and error handling
"""

# -----------------------------------------------------------------------------
# Imports & Dependencies
# -----------------------------------------------------------------------------

# === Standard Library ===
import os
import re
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

# === Third-Party Libraries ===
import pandas as pd
import requests
from sqlalchemy import create_engine, text
from dateutil.parser import parse
from dotenv import load_dotenv

# === Internal Modules ===
from ..api import (
    create_table_from_file,
    insert_data_from_file,
    list_table_columns,
    get_table_schema,
    query_table_metadata,
    read_csv,
    detect_datetime_column,
    auto_detect_delimiter,
    save_config_file,
    retrieve_data,
    insert_single_row,
    get_grafana_url,
    OutputFormat,
)

from ..metadata import (
    load_metadata,
    export_meta,
    update_metadata,
    export_all_metadata,
    rebuild_metadata_row,
)

from ..exceptions import DatetimeDetectionError, TableNameError

# -----------------------------------------------------------------------------
# Logging Setup & Environment Variables
# -----------------------------------------------------------------------------

logger_cli = logging.getLogger("cli")
if logger_cli.hasHandlers():
    logger_cli.handlers.clear()
logger_cli.setLevel(logging.INFO)
_logger_hdlr = logging.StreamHandler()
_logger_hdlr.setFormatter(
    logging.Formatter(
        "[CLI] %(asctime)s  %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
)
logger_cli.addHandler(_logger_hdlr)

load_dotenv()
POSTGREST_URL = os.getenv("POSTGREST_URL")

# -----------------------------------------------------------------------------
# Input Validation & Table Name Checks
# -----------------------------------------------------------------------------

_TABLE_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def validate_table_name(name: str) -> None:
    """
    Validates whether the given table name conforms to PostgreSQL naming rules.

    Allowed format:
      - Starts with a lowercase letter or underscore.
      - Contains only lowercase letters, numbers, and underscores.

    Parameters:
      name : str - Table name to validate.

    Raises:
      TableNameError - If the name does not meet the naming convention.
    """

    if not _TABLE_NAME_PATTERN.match(name):
        raise TableNameError(
            f"Invalid table name '{name}'. "
            "Names must start with lowercase letter/_ and contain only lowercase letters, digits, or underscores."
        )


# -----------------------------------------------------------------------------
# Config Directory & File Management
# -----------------------------------------------------------------------------

# Directory to hold per-table JSON configs
CONFIG_DIR = Path.cwd() / "configs"


def ensure_config_dir():
    """
    Ensures that the local 'configs/' directory exists for saving or loading config files.

    If the directory does not exist, it is created with parent directories as needed.
    """
    CONFIG_DIR.mkdir(exist_ok=True)


def list_config_files() -> list[Path]:
    """
    Lists all saved configuration (JSON) files under the 'configs/' directory.

    Returns:
        list[Path]: A sorted list of Path objects for all *.json config files.
    """
    return sorted(CONFIG_DIR.glob("*.json"))


def pick_config_file() -> dict | None:
    """
    Prompts the user to select one of the saved configuration files.

    Behavior:
        - If exactly one config is found, asks whether to load it.
        - If multiple are found, presents a numbered list for user selection.
        - If the user presses Enter or cancels, returns None.

    Returns:
        dict | None: The loaded config dictionary or None if the user skipped.
    """
    files = list_config_files()
    if not files:
        return None

    # Auto-load if exactly one
    if len(files) == 1:
        name = files[0].stem
        if yes_no_prompt(f"Found one config ({name}). Load it?"):
            return json.load(files[0].open())

    # Otherwise list all
    print("Available saved configs:")
    for i, f in enumerate(files, 1):
        print(f"  {i}) {f.name}")
    choice = prompt("Pick a config by number or press Enter to skip: ")
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return json.load(files[int(choice) - 1].open())
    return None


# -----------------------------------------------------------------------------
# Prompt Utilities (prompt, yes/no, confirm, ask for date for grafana)
# -----------------------------------------------------------------------------


def prompt(msg: str, default: str = "") -> str:
    """
    Prompts the user for input, with support for default, back, and exit keywords.

    Special input behaviors:
        - 'b' or 'B' -> returns "(B)" (used by caller to go back)
        - 'e' or 'E' -> exits the program
        - Empty input -> returns the default value

    Parameters:
        msg (str): The prompt message to display.
        default (str): The fallback value if the user presses Enter.

    Returns:
        str: The user input or special token "(B)" if 'b'/'B' was typed.

    Exits:
        Immediately exits the program if user enters 'e' or 'E'.
    """
    while True:
        user_in = input(f"{msg}").strip()
        # partial restart or exit checks:
        if user_in.lower() == "b":
            # Indicate "go back to main menu"
            return "(B)"
        elif user_in.lower() == "e":
            # Exit the entire script
            print("Exiting as requested.")
            sys.exit(0)

        # If user typed nothing, return default
        if user_in == "":
            return default
        return user_in


def confirm_prompt(msg: str) -> bool:
    """
    Prompts the user with a yes/no question and interprets special inputs.

    Acceptable responses:
        - 'y', 'yes' -> returns True
        - 'n', 'no', 'b', 'back' -> returns False (interpreted as decline or go back)
        - 'e', 'exit' -> exits the program immediately

    Parameters:
        msg (str): The prompt message to display.

    Returns:
        bool: True for yes, False for no/back.

    Exits:
        On 'e' or 'exit'.
    """
    while True:
        user_in = input(f"{msg} ([Y]es / [N]o / [B]ack / [E]xit): ").lower().strip()
        if user_in in ["y", "yes"]:
            return True
        elif user_in in ["n", "no"]:
            return False
        elif user_in in ["b", "back"]:
            # interpret 'b' as a "no," so the calling function can do a partial restart if needed
            return False
        elif user_in in ["e", "exit"]:
            print("Exiting as requested.")
            sys.exit(0)
        else:
            print("Please enter [Y]es / [N]o / [B]ack / [E]xit.")


def yes_no_prompt(msg: str) -> bool:
    """
    Asks a pure yes/no question and exits on explicit user request.

    This function is intended for simple binary confirmation (e.g., loading configs).

    Acceptable inputs:
        - 'y', 'yes' -> returns True
        - 'n', 'no' -> returns False
        - 'e', 'exit' -> exits the script

    Parameters:
        msg (str): The question to present.

    Returns:
        bool: True for yes, False for no.

    Exits:
        On 'e' or 'exit'.
    """
    while True:
        ans = input(f"{msg} ([Y]es / [N]o / [E]xit): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        if ans in ("e", "exit"):
            print("Exiting as requested.")
            sys.exit(0)
        print("Please enter Y, N, or E.")


# ----------------------------------------------------------------------
# Helper: ask_date
# ----------------------------------------------------------------------


def ask_date(label: str, min_dt: datetime, max_dt: datetime) -> datetime | None:
    """
    Prompt for a calendar date within [min_dt.date(), max_dt.date()].
    - 'B' returns None (go back), 'E' exits.
    - If the chosen date == min_dt.date(), returns min_dt.
      If == max_dt.date(), returns max_dt.
      Otherwise returns that date at midnight of min_dt's tz.
    """
    tzinfo = min_dt.tzinfo
    min_date, max_date = min_dt.date(), max_dt.date()

    while True:
        y = prompt(f"{label} year (YYYY) or [B]ack / [E]xit: ")
        if y == "(B)":
            return None
        if y.lower() == "e":
            sys.exit(0)

        m = prompt(f"{label} month (1–12) or [B]ack / [E]xit: ")
        if m == "(B)":
            return None
        if m.lower() == "e":
            sys.exit(0)

        d = prompt(f"{label} day (1–31) or [B]ack / [E]xit: ")
        if d == "(B)":
            return None
        if d.lower() == "e":
            sys.exit(0)

        if not (y.isdigit() and m.isdigit() and d.isdigit()):
            print(" All entries must be digits; try again.")
            continue

        yy, mm, dd = int(y), int(m), int(d)
        try:
            candidate = datetime(yy, mm, dd, tzinfo=tzinfo)
        except ValueError:
            print(" Invalid date; try again.")
            continue

        if not (min_date <= candidate.date() <= max_date):
            print(f" Date outside table range ({min_date}–{max_date}); try again.")
            continue

        # stretch to endpoints if at boundary
        if candidate.date() == min_date:
            return min_dt
        if candidate.date() == max_date:
            return max_dt

        # otherwise midnight on that date
        return candidate


# -----------------------------------------------------------------------------
# Input Pickers (file path, delimiter, datetime col, etc.)
# -----------------------------------------------------------------------------


def pick_file_path() -> str | Path:
    """
    Prompts the user for a valid file path to a CSV or TXT file.

    Behavior:
        - Displays the current working directory.
        - Expands '~' and resolves relative paths.
        - Verifies that the file exists and is readable.
        - Supports (B)ack or (E)xit commands.

    Returns:
        str | Path: A valid file path or the string "(B)" if user chooses to go back.
    """
    # Show current working directory using pathlib
    print(f"Current working directory: {Path.cwd()}")

    while True:
        user_in = prompt("Enter path to CSV/TXT file or type [B]ack / [E]xit: ")
        if user_in == "(B)":
            return "(B)"

        # Convert to Path, expand ~ and resolve relative parts
        p = Path(user_in).expanduser().resolve()

        # Validate existence and that it’s a file
        if not p.exists() or not p.is_file():
            print(f"File not found: {p}. Try again or type [B]ack / [E]xit.")
            continue

        return p


def pick_delimiter(file_path: str) -> str:
    """
    Prompts the user to confirm or override the auto-detected delimiter for a file.

    Behavior:
        - Uses `auto_detect_delimiter()` to suggest a default.
        - Allows manual override with ',', ';', '\\t', or '|'.
        - Rejects invalid multi-character delimiters.
        - Supports (B)ack or (E)xit commands.

    Parameters:
        file_path (str): Path to the file for which to detect the delimiter.

    Returns:
        str: The chosen delimiter or "(B)" if the user chooses to go back.
    """
    detected = auto_detect_delimiter(file_path) or ""
    while True:
        msg = (
            f"Auto-detected delimiter is '{detected}'. "
            " Press Enter to accept or type new delimiter or [B]ack / [E]xit: "
        )
        delim = prompt(msg, default=detected)
        if delim == "(B)":
            return "(B)"
        if delim == "":
            if detected == "":
                print("No delimiter was detected or provided. Please enter one.")
                continue
            return detected
        # user typed something
        if len(delim) > 1 and delim not in [r"\t", ",", ";", "|"]:
            print(
                "Delimiter must be ',', ';', '\\t', '|', or a single character. Try again."
            )
            continue
        return delim


def display_columns_and_samples(file_path: str, delimiter: str):
    """
    Loads and displays the first few rows of a CSV/TXT file for user preview.

    Behavior:
        - Prints the detected column names.
        - Prints the first 5 rows of the file for context.
        - Handles errors gracefully and logs them.

    Parameters:
        file_path (str): Path to the input file.
        delimiter (str): Delimiter to use for reading the file.

    Returns:
        pd.DataFrame | None: A DataFrame preview of the file, or None on failure.
    """
    try:
        df = read_csv(file_path, delimiter)
    except Exception as e:
        print(f"Error reading file for sample display: {e}")
        return None

    col_list = list(df.columns)
    print("\nColumns found:", col_list)
    sample_count = min(5, len(df))
    print(f"First {sample_count} rows sample:")
    print(df.head(sample_count))
    return df


def pick_datetime_column_interactive(df: pd.DataFrame) -> str:
    """
    Interactively determines which column to use as the datetime column.

    Behavior:
        - Attempts auto-detection using `detect_datetime_column()`.
        - If a single column is detected, user can accept or override.
        - If multiple or none are found, prompts the user to pick manually.

    Parameters:
        df (pd.DataFrame): DataFrame to inspect.

    Returns:
        str: The chosen datetime column name, or "(B)" to go back.
    """
    try:
        auto_col = detect_datetime_column(df)
        # If we got here, exactly one was found
        msg = f"Auto-detected datetime column is '{auto_col}'. Press Enter to accept or type [B]ack / [E]xit: "
        col = prompt(msg, default=auto_col)
        if col == "(B)":
            return "(B)"
        if col not in df.columns:
            print(f"Column '{col}' not found. Let's pick from the list manually.")
            return pick_from_col_list(df)
        return col
    except DatetimeDetectionError:
        print("Could not auto-detect a single datetime column. Let's pick from list.")
        return pick_from_col_list(df)


def pick_from_col_list(df: pd.DataFrame) -> str:
    """
    Prompts the user to select a column from a DataFrame's columns list.

    Behavior:
        - Lists available columns.
        - Re-prompts on invalid input.
        - Supports (B)ack or (E)xit commands.

    Parameters:
        df (pd.DataFrame): DataFrame whose columns will be listed.

    Returns:
        str: A valid column name selected by the user, or "(B)" to go back.
    """
    col_list = list(df.columns)
    while True:
        print(f"Columns available: {col_list}")
        col = prompt("Enter the exact datetime column name or type [B]ack / [E]xit: ")
        if col == "(B)":
            return "(B)"
        if col in col_list:
            return col
        print(f"Column '{col}' not found. Try again or type [B]ack / [E]xit.")


# -----------------------------------------------------------------------------
# Format, Timezone, Chunking, Duplicates
# -----------------------------------------------------------------------------


def pick_datetime_format_menu() -> Optional[str]:
    """
    Presents a menu of common datetime format strings for parsing timestamps.

    Options:
        1) Auto-detect format
        2) ISO format: %Y-%m-%d %H:%M:%S
        3) EU format:  %d-%m-%Y %H:%M:%S
        4) US format:  %m/%d/%Y %I:%M:%S %p
        5) Custom format input

    Returns:
        str | None: Selected format string, or None for auto-detection.
                    Returns "(B)" if the user chooses to go back.
    """
    while True:
        print("\nDatetime Format Options:")
        print("1) Auto-detect (no explicit format)")
        print("2) %Y-%m-%d %H:%M:%S   (e.g. 2025-03-01 13:45:00)")
        print("3) %d-%m-%Y %H:%M:%S   (e.g. 01-03-2025 13:45:00)")
        print("4) %m/%d/%Y %I:%M:%S %p (e.g. 03/01/2025 01:45:00 PM)")
        print("5) Custom format...")
        user_in = prompt(
            "Press Enter or select '1' for auto detection or select (2-5) or [B]ack / [E]xit. ",
            default="1",
        )
        if user_in == "(B)":
            return "(B)"
        if user_in == "1":
            return None
        elif user_in == "2":
            return "%Y-%m-%d %H:%M:%S"
        elif user_in == "3":
            return "%d-%m-%Y %H:%M:%S"
        elif user_in == "4":
            return "%m/%d/%Y %I:%M:%S %p"
        elif user_in == "5":
            custom_fmt = prompt("Enter custom datetime format or [B]ack / [E]xit. ")
            if custom_fmt == "(B)":
                continue
            if custom_fmt:
                return custom_fmt
            else:
                print("Empty format not valid. Try again or [B]ack / [E]xit.")
        else:
            print("Invalid choice. Please pick 1-5 or [B]ack / [E]xit.")


def pick_timezone_menu(default_tz="UTC") -> str:
    """
    Presents a timezone selection menu with common choices and custom entry.

    Options:
        1) UTC
        2) US/Eastern
        3) Europe/Berlin
        4) Asia/Kolkata
        5) Custom string

    Parameters:
        default_tz (str): Default timezone to use when pressing Enter (default: "UTC").

    Returns:
        str: Selected timezone string or "(B)" to go back.
    """
    while True:
        print("\nTimezone Options:")
        print("1) UTC (default)")
        print("2) US/Eastern")
        print("3) Europe/Berlin")
        print("4) Asia/Kolkata")
        print("5) Custom...")
        user_in = prompt(
            "Press Enter or select '1' for default (UTC) or select (2-5) or [B]ack / [E]xit. ",
            default="1",
        )
        if user_in == "(B)":
            return "(B)"
        elif user_in == "1":
            return "UTC"
        elif user_in == "2":
            return "US/Eastern"
        elif user_in == "3":
            return "Europe/Berlin"
        elif user_in == "4":
            return "Asia/Kolkata"
        elif user_in == "5":
            # custom
            cust = prompt("Enter custom timezone or [B]ack / [E]xit. ")
            if cust == "(B)":
                continue
            # For now, just accept if not empty:
            if cust.strip():
                return cust
            else:
                print("Invalid empty timezone. Try again.")
        else:
            print("Invalid choice. Use 1-5 or [B]ack / [E]xit.")


def pick_chunk_interval_menu(default=7) -> int:
    """
    Prompts the user to select a TimescaleDB chunking interval in days.

    Options:
        1) 1 day
        2) 7 days (default)
        3) 30 days
        4) Custom integer input

    Parameters:
        default (int): Default chunk size in days (used in prompt fallback).

    Returns:
        int: The number of days for the chunk interval.
             Returns -1 if the user chooses to go back.
    """
    while True:
        print("\nChunk Interval:")
        print("1) 1 day")
        print("2) 7 days (default)")
        print("3) 30 days")
        print("4) Custom integer...")
        user_in = prompt(
            "Press Enter or select '2' for default (7 Days) or select (1-3, 4) or [B]ack / [E]xit. ",
            default="2",
        )
        if user_in == "(B)":
            return -1
        if user_in == "1":
            return 1
        elif user_in == "2":
            return 7
        elif user_in == "3":
            return 30
        elif user_in == "4":
            c = prompt(
                "Enter chunk days integer or [B]ack / [E]xit. ", default=str(default)
            )
            if c == "(B)":
                continue
            try:
                val = int(c)
                if val > 0:
                    return val
                else:
                    print("Must be positive. Try again.")
            except ValueError:
                print("Not a valid integer. Try again.")
        else:
            print("Invalid choice. Use 1-4 or [B]ack / [E]xit.")


def pick_allow_duplicates() -> bool:
    """
    Asks the user whether to allow duplicate time-range insertions.

    Behavior:
        - 'y' or 'yes' returns True (allow duplicates).
        - 'n' or 'no' returns False (prevent duplicates).
        - 'b' or 'back' returns "(B)" to signal going back.
        - 'e' or 'exit' exits the script immediately.

    Returns:
        bool | str: True or False based on user input, or "(B)" for back.
    """
    while True:
        user_in = (
            input(
                "Allow duplicate time-range insertion? ([Y]es / [N]o / [B]ack / [E]xit): "
            )
            .lower()
            .strip()
        )
        if user_in in ["y", "yes"]:
            return True
        elif user_in in ["n", "no"]:
            return False
        elif user_in in ["b", "back"]:
            return "(B)"
        elif user_in in ["e", "exit"]:
            print("Exiting as requested.")
            sys.exit(0)
        else:
            print("Please enter [Y]es / [N]o / [B]ack / [E]xit.")


# -----------------------------------------------------------------------------
# Table selection and metadata matching
# -----------------------------------------------------------------------------


def table_selection_menu(title: str = "Available tables") -> str | None:
    """
    Presents a numbered list of user tables (registry row hidden).

    Returns
    -------
    str  - chosen table name
    None - user pressed [B]ack
    """
    tables = list_tables_in_db()
    if not tables:
        print("No user tables found.")
        return None

    print(f"\n{title}:")
    for i, t in enumerate(tables, 1):
        print(f"  {i}) {t}")

    while True:
        pick = prompt("Select by number or [B]ack / [E]xit: ")
        if pick == "(B)":
            return None
        if pick.lower() == "e":
            sys.exit(0)
        if pick.isdigit() and 1 <= int(pick) <= len(tables):
            return tables[int(pick) - 1]
        print("Invalid choice.")


def find_matching_tables(desired_cols: set[str], datetime_col: str) -> list[str]:
    """
    Returns a list of tables whose cached metadata indicates
    they share *exactly* the same column names (ignoring order) **and**
    the same datetime column.

    Notes
    -----
    • Uses only the metadata row → no live SQL needed
    • Ignores tables that don’t have a metadata entry yet
    """
    matches: list[str] = []

    for tbl in list_tables_in_db():
        meta = load_metadata(tbl)
        if not meta:
            continue
        meta_cols = set(meta.schema.keys())
        meta_dt = meta.datetime_col

        if (
            meta_dt == datetime_col
            and meta_cols == desired_cols
            and len(meta_cols) == len(desired_cols)
        ):
            matches.append(tbl)

    return matches


# -----------------------------------------------------------------------------
# CLI Menu Handlers — Table Creation & Insertion
# -----------------------------------------------------------------------------


def run_create_table():
    """
    Interactive flow for "Create Table Only".

    Steps:
        1) Prompt for file path and confirm it exists.
        2) Auto-detect or override the delimiter.
        3) Display column names and a sample of rows.
        4) Let user pick a datetime column.
        5) Let user specify or auto-detect datetime format.
        6) Prompt for timezone.
        7) Prompt for chunk interval (TimescaleDB).
        8) Prompt for new table name and validate it.
        9) Show summary of all selections and confirm.
       10) If confirmed, call `create_table_from_file()` with inputs.
       11) Optionally save the settings to a config JSON file.

    Supports:
        - Backtracking with (B)
        - Exit anytime with (E)
        - Loading and modifying saved config defaults
    """
    print("\n=== Create Table Only ===")

    # ——— Load Defaults -- NEW: Preview the defaults maybe change some? ——————————————————————————
    ensure_config_dir()
    loaded = pick_config_file()
    if loaded:
        defaults = loaded
        skip_prompts = True
    else:
        defaults = {}
        skip_prompts = False
    if defaults:
        print("\nSaved defaults:")
        for k, v in defaults.items():
            disp = v if v not in (None, "") else "(auto)"
            print(f"  • {k}: {disp}")
        use_def = yes_no_prompt("Load these defaults for this run?")
        if use_def:
            # ------  Offer quick edit of any single field  ------
            keys = list(defaults.keys())
            while yes_no_prompt("Modify any of the defaults?"):
                print("\nPick a field to change:")
                for i, k in enumerate(keys, 1):
                    print(f"  {i}) {k}: {defaults[k]}")
                choice = prompt("Number: ")
                if choice == "":  # empty means go back to the “Modify any?” prompt
                    continue
                if not (choice.isdigit() and 1 <= int(choice) <= len(keys)):
                    print("Invalid choice.")
                    continue
                fld = keys[int(choice) - 1]
                # run the matching picker once
                if fld == "file_path":
                    defaults[fld] = pick_file_path()
                elif fld == "delimiter":
                    defaults[fld] = pick_delimiter(defaults["file_path"])
                elif fld == "datetime_col":
                    _df = read_csv(defaults["file_path"], defaults["delimiter"])
                    defaults[fld] = pick_datetime_column_interactive(_df)
                elif fld == "datetime_format":
                    defaults[fld] = pick_datetime_format_menu()
                elif fld == "timezone":
                    defaults[fld] = pick_timezone_menu()
                elif fld == "chunk_days":
                    defaults[fld] = pick_chunk_interval_menu()
                else:
                    print("(No editor for that field)")
            # push into locals and skip prompts
            file_path = Path(defaults["file_path"])
            delim = defaults["delimiter"]
            dt_col = defaults["datetime_col"]
            dt_fmt = defaults["datetime_format"]
            tz = defaults["timezone"]
            chunk = defaults["chunk_days"]
            skip_prompts = True
        else:
            skip_prompts = False
    else:
        skip_prompts = False

    steps = [
        "file_path",
        "delimiter",
        "sample",
        "datetime_col",
        "datetime_format",
        "timezone",
        "chunk_interval",
        "table_name",
        "confirm",
    ]
    data = {}
    df = None
    i = 0

    while i < len(steps):
        step = steps[i]

        if step == "file_path":
            if skip_prompts:
                data["file_path"] = file_path
            else:
                res = pick_file_path()
                if res == "(B)":
                    return
                data["file_path"] = res
            i += 1

        elif step == "delimiter":
            if skip_prompts:
                data["delimiter"] = delim
            else:
                res = pick_delimiter(data["file_path"])
                if res == "(B)":
                    i -= 1
                    continue
                data["delimiter"] = res
            i += 1

        elif step == "sample":
            df = display_columns_and_samples(data["file_path"], data["delimiter"])
            if df is None:
                print("Could not load sample. Aborting.")
                return
            i += 1

        elif step == "datetime_col":
            if skip_prompts:
                data["datetime_col"] = dt_col
            else:
                res = pick_datetime_column_interactive(df)
                if res == "(B)":
                    i -= 2
                    continue
                data["datetime_col"] = res
            i += 1

        elif step == "datetime_format":
            if skip_prompts:
                data["datetime_format"] = dt_fmt
            else:
                res = pick_datetime_format_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["datetime_format"] = res
            i += 1

        elif step == "timezone":
            if skip_prompts:
                data["timezone"] = tz
            else:
                res = pick_timezone_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["timezone"] = res
            i += 1

        elif step == "chunk_interval":
            if skip_prompts:
                data["chunk_days"] = chunk
            else:
                res = pick_chunk_interval_menu(default=7)
                if res < 0:
                    i -= 1
                    continue
                data["chunk_days"] = res
            i += 1

        elif step == "table_name":
            while True:
                res = prompt("Enter new table name (or [B]ack / [E]xit): ")
                if res == "(B)":
                    i -= 1
                    break
                try:
                    validate_table_name(res)
                except TableNameError as e:
                    print(e)
                    continue
                data["table_name"] = res
                i += 1
                break

        elif step == "confirm":
            print(f"\nSummary for Create Table:")
            print(f"  File Path:      {data['file_path']}")
            print(f"  Delimiter:      {data['delimiter']}")
            print(f"  Datetime Col:   {data['datetime_col']}")
            fmt = data["datetime_format"] or "(auto)"
            print(f"  Datetime Format:{fmt}")
            print(f"  Timezone:       {data['timezone']}")
            print(f"  Chunk Days:     {data['chunk_days']}")
            print(f"  Table Name:     {data['table_name']}")
            if confirm_prompt("Confirm creation"):
                while True:
                    ans = (
                        input(
                            "Save these choices as defaults for next time?  ([Y]es / [N]o / [B]ack / [E]xit): "
                        )
                        .strip()
                        .lower()
                    )
                    if ans in ("y", "yes"):
                        # Prompt user for custom filename (default: <table_name>.json)
                        default_name = f"{data['table_name']}.json"
                        filename = prompt(
                            f"Save defaults as [{default_name}] or enter custom filename: ",
                            default=default_name,
                        ).strip()
                        if not filename.endswith(".json"):
                            filename += ".json"
                        custom_path = CONFIG_DIR / filename

                        save_config_file(
                            {
                                "file_path": str(data["file_path"]),
                                "delimiter": data["delimiter"],
                                "datetime_col": data["datetime_col"],
                                "datetime_format": data["datetime_format"],
                                "timezone": data["timezone"],
                                "chunk_days": data.get("chunk_days"),
                                "allow_duplicates": data.get("allow_duplicates", False),
                            },
                            table_name=data["table_name"],
                            path=custom_path,
                        )

                        print(f"Choices have been saved into {custom_path}")

                        break  # proceed with creation/insertion
                    elif ans in ("n", "no"):
                        break  # proceed without saving
                    elif ans in ("b", "back"):
                        # bounce back to the prior “Confirm…” prompt
                        if not confirm_prompt(
                            "Confirm creation"
                        ):  # or “Confirm insertion” / “Confirm create + insert”
                            print("Operation canceled.")
                            return
                        # else if they say “yes” here, we re-show the Save‐defaults loop
                        continue
                    elif ans in ("e", "exit"):
                        print("Exiting as requested.")
                        sys.exit(0)
                    else:
                        print("Please enter [Y]es / [N]o / [B]ack / [E]xit.")

                try:
                    create_table_from_file(
                        file_path=data["file_path"],
                        table_name=data["table_name"],
                        delimiter=data["delimiter"],
                        datetime_col=data["datetime_col"],
                        format=data["datetime_format"],
                        timezone=data["timezone"],
                        chunk_days=data["chunk_days"],
                        derive_stats=False,
                    )
                    print("Table creation succeeded!\n")
                    # show_metadata(data["table_name"])
                except Exception as e:
                    print(f"Error during create_table_from_file: {e}")
            else:
                print("Operation canceled.")
            return


def run_insert_data():
    """
    Interactive flow for "Insert Data Only".

    Steps:
        1) Prompt for CSV/TXT file path.
        2) Auto-detect or override delimiter.
        3) Show DataFrame sample (columns and first rows).
        4) Choose datetime column (auto or manual).
        5) Choose or auto-detect datetime format.
        6) Choose timezone.
        7) Ask if duplicates are allowed.
        8) Prompt for existing table name.
        9) Show summary and confirm.
       10) Call `insert_data_from_file()` with all inputs.
       11) Optionally save choices to config.

    Features:
        - Full backtracking and exit safety.
        - Reusable default configs with editing option.
    """
    print("\n=== Insert Data Only ===")

    # Load Defaults
    ensure_config_dir()
    loaded = pick_config_file()
    if loaded:
        defaults = loaded
        skip_prompts = True
    else:
        defaults = {}
        skip_prompts = False
    if defaults:
        print("\nSaved defaults:")
        for k, v in defaults.items():
            disp = v if v not in (None, "") else "(auto)"
            print(f"  • {k}: {disp}")
        use_def = yes_no_prompt("Load these defaults for this run?")
        if use_def:
            keys = list(defaults.keys())
            while yes_no_prompt("Modify any of the defaults?"):
                print("\nPick a field to change:")
                for i, k in enumerate(keys, 1):
                    print(f"  {i}) {k}: {defaults[k]}")
                choice = prompt("Number: ")
                if choice == "":  # empty means go back to the “Modify any?” prompt
                    continue
                if not (choice.isdigit() and 1 <= int(choice) <= len(keys)):
                    print("Invalid choice.")
                    continue
                fld = keys[int(choice) - 1]
                if fld == "file_path":
                    defaults[fld] = pick_file_path()
                elif fld == "delimiter":
                    defaults[fld] = pick_delimiter(defaults["file_path"])
                elif fld == "datetime_col":
                    _df = read_csv(defaults["file_path"], defaults["delimiter"])
                    defaults[fld] = pick_datetime_column_interactive(_df)
                elif fld == "datetime_format":
                    defaults[fld] = pick_datetime_format_menu()
                elif fld == "timezone":
                    defaults[fld] = pick_timezone_menu()
                elif fld == "allow_duplicates":
                    defaults[fld] = pick_allow_duplicates()
                else:
                    print("(No editor for that field)")
            file_path = Path(defaults["file_path"])
            delim = defaults["delimiter"]
            dt_col = defaults["datetime_col"]
            dt_fmt = defaults["datetime_format"]
            tz = defaults["timezone"]
            allow_dups = defaults["allow_duplicates"]
            skip_prompts = True
        else:
            skip_prompts = False
    else:
        skip_prompts = False

    steps = [
        "file_path",
        "delimiter",
        "sample",
        "datetime_col",
        "datetime_format",
        "timezone",
        "allow_duplicates",
        "table_name",
        "confirm",
    ]
    data = {}
    df = None
    i = 0

    while i < len(steps):
        step = steps[i]

        if step == "file_path":
            if skip_prompts:
                data["file_path"] = file_path
            else:
                res = pick_file_path()
                if res == "(B)":
                    return
                data["file_path"] = res
            i += 1

        elif step == "delimiter":
            if skip_prompts:
                data["delimiter"] = delim
            else:
                res = pick_delimiter(data["file_path"])
                if res == "(B)":
                    i -= 1
                    continue
                data["delimiter"] = res
            i += 1

        elif step == "sample":
            df = display_columns_and_samples(data["file_path"], data["delimiter"])
            if df is None:
                print("Could not load sample. Aborting insertion.")
                return
            i += 1

        elif step == "datetime_col":
            if skip_prompts:
                data["datetime_col"] = dt_col
            else:
                res = pick_datetime_column_interactive(df)
                if res == "(B)":
                    i -= 2
                    continue
                data["datetime_col"] = res
            i += 1

        elif step == "datetime_format":
            if skip_prompts:
                data["datetime_format"] = dt_fmt
            else:
                res = pick_datetime_format_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["datetime_format"] = res
            i += 1

        elif step == "timezone":
            if skip_prompts:
                data["timezone"] = tz
            else:
                res = pick_timezone_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["timezone"] = res
            i += 1

        elif step == "allow_duplicates":
            if skip_prompts:
                data["allow_duplicates"] = allow_dups
            else:
                res = pick_allow_duplicates()
                if res == "(B)":
                    i -= 1
                    continue
                data["allow_duplicates"] = bool(res)
            i += 1

        elif step == "table_name":
            desired_cols = set(df.columns)
            dt_col = data["datetime_col"]
            compatible = find_matching_tables(desired_cols, dt_col)

            if compatible:
                print("\nTables with matching schema:")
                for idx, t in enumerate(compatible, 1):
                    print(f"  {idx}) {t}")
                print("  0) Pick another table")
                while True:
                    pick = prompt("Select (number) or 0 / [B]ack / [E]xit: ")
                    if pick == "(B)":
                        i -= 1
                        break
                    if pick.lower() == "e":
                        sys.exit(0)
                    if pick.isdigit() and 1 <= int(pick) <= len(compatible):
                        data["table_name"] = compatible[int(pick) - 1]
                        i += 1
                        break
                    if pick == "0":
                        print("Generic picker not implemented.")
                        continue
                    print("Invalid selection.")
                continue
            else:
                print(
                    "\nNo matching table found, please create it using option 1 (Create Table Only) or option 4 (Create Table + Insert Data) from the main menu."
                )
                print("Returning to main menu...\n")
                return

        elif step == "confirm":
            print(f"\nSummary of Insert Data:")
            print(f"  File:           {data['file_path']}")
            print(f"  Delimiter:      {data['delimiter']}")
            print(f"  Datetime Col:   {data['datetime_col']}")
            fmt = data["datetime_format"] or "(auto)"
            print(f"  Datetime Format:{fmt}")
            print(f"  Timezone:       {data['timezone']}")
            print(f"  Allow Dups:     {data['allow_duplicates']}")
            print(f"  Table Name:     {data['table_name']}")
            if confirm_prompt("Confirm creation"):
                while True:
                    ans = (
                        input(
                            "Save these choices as defaults for next time?  ([Y]es / [N]o / [B]ack / [E]xit): "
                        )
                        .strip()
                        .lower()
                    )
                    if ans in ("y", "yes"):
                        # Prompt user for custom filename (default: <table_name>.json)
                        default_name = f"{data['table_name']}.json"
                        filename = prompt(
                            f"Save defaults as [{default_name}] or enter custom filename: ",
                            default=default_name,
                        ).strip()
                        if not filename.endswith(".json"):
                            filename += ".json"
                        custom_path = CONFIG_DIR / filename

                        save_config_file(
                            {
                                "file_path": str(data["file_path"]),
                                "delimiter": data["delimiter"],
                                "datetime_col": data["datetime_col"],
                                "datetime_format": data["datetime_format"],
                                "timezone": data["timezone"],
                                "chunk_days": data.get("chunk_days"),
                                "allow_duplicates": data.get("allow_duplicates", False),
                            },
                            table_name=data["table_name"],
                            path=custom_path,
                        )

                        print(f"Choices have been saved into {custom_path}")
                        break
                    elif ans in ("n", "no"):
                        break
                    elif ans in ("b", "back"):
                        if not confirm_prompt("Confirm creation"):
                            print("Operation canceled.")
                            return

                        continue
                    elif ans in ("e", "exit"):
                        print("Exiting as requested.")
                        sys.exit(0)
                    else:
                        print("Please enter [Y]es / [N]o / [B]ack / [E]xit.")
                try:
                    insert_data_from_file(
                        file_path=data["file_path"],
                        table_name=data["table_name"],
                        delimiter=data["delimiter"],
                        datetime_col=data["datetime_col"],
                        format=data["datetime_format"],
                        timezone=data["timezone"],
                        allow_duplicates=data["allow_duplicates"],
                    )
                    print("Data insertion done.")
                except Exception as e:
                    print(f"Error during insert_data_from_file: {e}")
            else:
                print("Operation canceled.")
            return


def run_create_and_insert():
    """
    Interactive flow for "Create Table + Insert Data".

    Combines both creation and insertion in one workflow.

    Steps:
        1) File path input and delimiter detection.
        2) Column sample preview.
        3) Datetime column selection.
        4) Datetime format and timezone selection.
        5) Chunk interval and new table name.
        6) Confirmation and optional config save.
        7) Executes:
            - `create_table_from_file(...)`
            - `insert_data_from_file(...)`

    Notes:
        - Duplicate prevention is enforced by default.
        - Compatible with config loading/editing.
    """
    print("\n=== Create Table + Insert Data ===")

    # Load Defaults
    ensure_config_dir()
    loaded = pick_config_file()
    if loaded:
        defaults = loaded
        skip_prompts = True
    else:
        defaults = {}
        skip_prompts = False
    if defaults:
        print("\nSaved defaults:")
        for k, v in defaults.items():
            disp = v if v not in (None, "") else "(auto)"
            print(f"  • {k}: {disp}")
        use_def = yes_no_prompt("Load these defaults for this run?")
        if use_def:
            keys = list(defaults.keys())
            while yes_no_prompt("Modify any of the defaults?"):
                print("\nPick a field to change:")
                for i, k in enumerate(keys, 1):
                    print(f"  {i}) {k}: {defaults[k]}")
                choice = prompt("Number: ")
                if choice == "":
                    continue
                if not (choice.isdigit() and 1 <= int(choice) <= len(keys)):
                    print("Invalid choice.")
                    continue
                fld = keys[int(choice) - 1]
                if fld == "file_path":
                    defaults[fld] = pick_file_path()
                elif fld == "delimiter":
                    defaults[fld] = pick_delimiter(defaults["file_path"])
                elif fld == "datetime_col":
                    _df = read_csv(defaults["file_path"], defaults["delimiter"])
                    defaults[fld] = pick_datetime_column_interactive(_df)
                elif fld == "datetime_format":
                    defaults[fld] = pick_datetime_format_menu()
                elif fld == "timezone":
                    defaults[fld] = pick_timezone_menu()
                elif fld == "chunk_days":
                    defaults[fld] = pick_chunk_interval_menu()
                else:
                    print("(No editor for that field)")
            file_path = Path(defaults["file_path"])
            delim = defaults["delimiter"]
            dt_col = defaults["datetime_col"]
            dt_fmt = defaults["datetime_format"]
            tz = defaults["timezone"]
            chunk = defaults["chunk_days"]
            skip_prompts = True
        else:
            skip_prompts = False
    else:
        skip_prompts = False

    steps = [
        "file_path",
        "delimiter",
        "sample",
        "datetime_col",
        "datetime_format",
        "timezone",
        "chunk_interval",
        "table_name",
        "confirm",
    ]
    data = {}
    df = None
    i = 0

    while i < len(steps):
        step = steps[i]

        if step == "file_path":
            if skip_prompts:
                data["file_path"] = file_path
            else:
                res = pick_file_path()
                if res == "(B)":
                    return
                data["file_path"] = res
            i += 1

        elif step == "delimiter":
            if skip_prompts:
                data["delimiter"] = delim
            else:
                res = pick_delimiter(data["file_path"])
                if res == "(B)":
                    i -= 1
                    continue
                data["delimiter"] = res
            i += 1

        elif step == "sample":
            df = display_columns_and_samples(data["file_path"], data["delimiter"])
            if df is None:
                print("Could not load sample. Aborting.")
                return
            i += 1

        elif step == "datetime_col":
            if skip_prompts:
                data["datetime_col"] = dt_col
            else:
                res = pick_datetime_column_interactive(df)
                if res == "(B)":
                    i -= 2
                    continue
                data["datetime_col"] = res
            i += 1

        elif step == "datetime_format":
            if skip_prompts:
                data["datetime_format"] = dt_fmt
            else:
                res = pick_datetime_format_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["datetime_format"] = res
            i += 1

        elif step == "timezone":
            if skip_prompts:
                data["timezone"] = tz
            else:
                res = pick_timezone_menu()
                if res == "(B)":
                    i -= 1
                    continue
                data["timezone"] = res
            i += 1

        elif step == "chunk_interval":
            if skip_prompts:
                data["chunk_days"] = chunk
            else:
                res = pick_chunk_interval_menu(default=7)
                if res < 0:
                    i -= 1
                    continue
                data["chunk_days"] = res
            i += 1

        elif step == "table_name":
            while True:
                res = prompt("Enter new table name (or [B]ack / [E]xit): ")
                if res == "(B)":
                    i -= 1
                    break
                try:
                    validate_table_name(res)
                except TableNameError as e:
                    print(e)
                    continue
                data["table_name"] = res
                i += 1
                break

        elif step == "confirm":
            print(f"\nSummary for Create + Insert:")
            print(f"  File Path:      {data['file_path']}")
            print(f"  Delimiter:      {data['delimiter']}")
            print(f"  Datetime Col:   {data['datetime_col']}")
            fmt = data["datetime_format"] or "(auto)"
            print(f"  Datetime Format:{fmt}")
            print(f"  Timezone:       {data['timezone']}")
            print(f"  Chunk Days:     {data['chunk_days']}")
            print(f"  Table Name:     {data['table_name']}")
            if confirm_prompt("Confirm creation"):
                while True:
                    ans = (
                        input(
                            "Save these choices as defaults for next time?  ([Y]es / [N]o / [B]ack / [E]xit): "
                        )
                        .strip()
                        .lower()
                    )
                    if ans in ("y", "yes"):
                        # Prompt user for custom filename (default: <table_name>.json)
                        default_name = f"{data['table_name']}.json"
                        filename = prompt(
                            f"Save defaults as [{default_name}] or enter custom filename: ",
                            default=default_name,
                        ).strip()
                        if not filename.endswith(".json"):
                            filename += ".json"
                        custom_path = CONFIG_DIR / filename

                        save_config_file(
                            {
                                "file_path": str(data["file_path"]),
                                "delimiter": data["delimiter"],
                                "datetime_col": data["datetime_col"],
                                "datetime_format": data["datetime_format"],
                                "timezone": data["timezone"],
                                "chunk_days": data.get("chunk_days"),
                                "allow_duplicates": data.get("allow_duplicates", False),
                            },
                            table_name=data["table_name"],
                            path=custom_path,
                        )

                        print(f"Choices have been saved into {custom_path}")
                        break
                    elif ans in ("n", "no"):
                        break
                    elif ans in ("b", "back"):
                        if not confirm_prompt("Confirm creation"):
                            print("Operation canceled.")
                            return

                        continue
                    elif ans in ("e", "exit"):
                        print("Exiting as requested.")
                        sys.exit(0)
                    else:
                        print("Please enter [Y]es / [N]o / [B]ack / [E]xit.")
                try:
                    create_table_from_file(
                        file_path=data["file_path"],
                        table_name=data["table_name"],
                        delimiter=data["delimiter"],
                        datetime_col=data["datetime_col"],
                        format=data["datetime_format"],
                        timezone=data["timezone"],
                        chunk_days=data["chunk_days"],
                        derive_stats=False,
                    )
                    insert_data_from_file(
                        file_path=data["file_path"],
                        table_name=data["table_name"],
                        delimiter=data["delimiter"],
                        datetime_col=data["datetime_col"],
                        format=data["datetime_format"],
                        timezone=data["timezone"],
                        allow_duplicates=False,
                    )
                    print("Create + Insert successful.")
                except Exception as e:
                    print(f"Error during create+insert: {e}")
            else:
                print("Operation canceled.")
            return


def run_insert_single_row():
    """
    Interactive flow for inserting exactly one row into an existing hypertable.

    Steps:
      1) List all public tables and prompt user to select one.
      2) Introspect that table’s columns and display them.
      3) Prompt the user for a value for each column.
      4) Ask which column is the timestamp, then format & timezone.
      5) Ask whether duplicate‐timestamp inserts are allowed.
      6) Call `insert_single_row()` and report success or error.
    """
    print("\n=== Insert Single Row ===")
    tables = list_tables_in_db()
    for i, t in enumerate(tables, 1):
        print(f"  {i}) {t}")
    choice = prompt("Select a table by number or [B]ack / [E]xit: ")
    if choice == "(B)":
        return
    table = tables[int(choice) - 1]

    cols = list_table_columns(table)
    types = get_table_schema(table)
    print("Columns:", cols)

    row: dict[str, Any] = {}
    for col in cols:
        while True:
            val = input(f"Enter value for '{col}': ").strip()
            # Allow "now" for timestamp column
            if col == cols[0]:  # or auto-detect: use first column as time
                if val.lower() in ("now", ""):
                    row[col] = datetime.utcnow()
                    break
                try:
                    # Let python dateutil handle most formats
                    row[col] = parse(val, dayfirst=True)
                    break
                except Exception:
                    print(
                        " Invalid date. Type 'now' or a valid timestamp (e.g. 01-03-2025 00:43:00)."
                    )
                    continue

            # Numeric columns: enforce float conversion (comma->dot)
            if types[col] in ("integer", "double precision"):
                try:
                    cleaned = val.replace(",", ".")
                    # integer vs float
                    row[col] = (
                        int(cleaned) if types[col] == "integer" else float(cleaned)
                    )
                    break
                except Exception:
                    print(" Invalid number; please enter digits (e.g. 123 or 123.45).")
                    continue

            # Text columns: accept anything
            row[col] = val
            break

    # 4) Inject
    try:
        insert_single_row(
            table_name=table,
            row=row,
            datetime_col=None,  # let API auto-detect
            format=None,  # skip format menu
            timezone="UTC",  # assume UTC
            allow_duplicates=False,
        )
        print(" Single row inserted.")
    except Exception as e:
        print(f" Error inserting single row: {e}")


# -----------------------------------------------------------------------------
# Metadata Menu
# -----------------------------------------------------------------------------

KV_RE = re.compile(r"\s*([^=]+?)\s*=\s*(.*?)\s*$")


def parse_units_line(line: str) -> dict | None:
    """
    Accepts:  temp=°C, pressure=kPa
              energy = kWh ; current = A
    Returns  {'temp':'°C', 'pressure':'kPa', ...}  or None on bad syntax.
    """
    pairs = re.split(r"[;,]", line)
    out: dict[str, str] = {}
    for p in pairs:
        if not p.strip():
            continue
        m = KV_RE.match(p)
        if not m:
            return None
        key, val = m.groups()
        out[key] = val
    return out


def prompt_units_interactively(schema: dict[str, str], current: dict | None) -> dict:
    """

    Walks through each column, lets user hit <Enter> to keep,
    type 'none' to clear, or 'B'/'E' as usual.

    """
    current = current or {}
    new_units = {}

    print("\nEnter engineering units (press Enter to keep current):")
    for col in schema.keys():
        default = current.get(col, "")
        raw = input(f"  {col} [{default}]: ").strip()
        if raw.lower() == "b":
            return "(B)"  # let caller treat as “go back”
        if raw.lower() == "e":
            sys.exit(0)
        if raw == "":
            if default != "":
                new_units[col] = default
        elif raw.lower() == "none":
            new_units[col] = None
        else:
            new_units[col] = raw
    return new_units


def show_metadata(table: str) -> None:
    """
    Loads a _timeseries_metadata row and prints it nicely.
    """
    meta = load_metadata(table)
    if not meta:
        print(f"No metadata row found for '{table}'.")
        return
    from dataclasses import asdict

    print(json.dumps(asdict(meta), indent=2, default=str))


def edit_units_notes(meta) -> tuple[dict | None, str | None] | str:
    """
    Interactive editor for units + notes.

    Returns
    -------
    (units_dict_or_None, notes_or_None)
        • Only the fields the user actually changed.
    "(B)"
        • User decided to go back one level.
    """

    # ---------- UNITS ----------
    while True:
        print("\nChoose editing mode for units:")
        print("  1) Prompt column-by-column (interactive)")
        print("  2) Paste JSON or key=val list")
        print("  B) Back   E) Exit")
        mode = prompt("Select (1/2/B/E): ", default="1").lower()
        if mode == "(b)" or mode == "b":
            return "(B)"
        if mode == "e":
            sys.exit(0)

        schema_cols = list(meta.schema.keys())

        if mode in ("", "1"):
            units_dict = prompt_units_interactively(meta.schema, meta.units)
            if units_dict == "(B)":
                continue  # back to mode menu
            # Only keep keys that are in schema, and drop None values
            units_dict = {
                k: v
                for k, v in units_dict.items()
                if k in schema_cols and v is not None
            }
            break
        elif mode == "2":
            paste = prompt(
                "Paste JSON or key=val list (e.g. temp=°C, pressure=kPa) "
                "or [B]ack / [E]xit:\n"
            )
            if paste == "(B)":
                continue
            if paste.lower() == "e":
                sys.exit(0)
            # try JSON
            try:
                ud = json.loads(paste)
                if isinstance(ud, dict):
                    # Only keep keys that are in schema, and drop None values
                    units_dict = {
                        k: v
                        for k, v in ud.items()
                        if k in schema_cols and v is not None
                    }
                    break
            except Exception:
                pass
            # try key=val
            kv = parse_units_line(paste)
            if kv is not None:
                # Merge with existing, but only for schema columns, and drop None values
                merged = {**(meta.units or {}), **kv}
                units_dict = {
                    k: v
                    for k, v in merged.items()
                    if k in schema_cols and v is not None
                }
                break
            print("Could not parse – please retry.")
        else:
            print("Pick 1, 2, B, or E.")
            continue

    # ---------- NOTES ----------
    print("\nCurrent notes (blank if none):")
    print(meta.notes or "<none>")
    if not confirm_prompt("Add / edit notes"):
        notes_final = None  # keep unchanged
    else:
        print("Enter notes – blank line to finish, B to abort, E to exit.")
        lines: list[str] = []
        while True:
            l = input("> ")
            if l.lower() == "b":
                notes_final = None  # unchanged
                break
            if l.lower() == "e":
                sys.exit(0)
            if l == "" and lines:
                notes_final = "\n".join(lines)
                break
            lines.append(l)

    return units_dict, notes_final


def run_metadata_menu() -> None:
    """
    _timeseries_metadata utility submenu

      1) Show metadata row                 (single table)
      2) Export metadata to JSON           (single table)
      3) Edit units / notes                (single table)
      4) Delete metadata row               (single table - optional export)
      5) Export *all* metadata (JSON)      (whole registry)
      6) Rebuild metadata row              (reset → auto-derived core fields)
      7) Back
    """
    while True:
        print("\n=== Metadata tools ===")
        print("1) Show metadata row")
        print("2) Export metadata to JSON")
        print("3) Edit units / notes")
        print("4) Delete metadata row")
        print("5) Export *all* metadata (JSON)")
        print("6) Rebuild metadata row")
        print("7) Back")
        choice = prompt("Select (1-7): ", default="7").strip()

        # ── quick outs ───────────────────────────────────────────────────
        if choice in ("7", "(B)"):
            return
        if choice.lower() == "e":
            sys.exit(0)

        # ── option 5: global dump (no table needed) ─────────────────────
        if choice == "5":
            def_name = "all_metadata.json"
            out = prompt(
                f"Output path (default ./{def_name}) or [B]ack / [E]xit: ",
                default=def_name,
            )
            if out == "(B)":
                continue
            if out.lower() == "e":
                sys.exit(0)
            p = Path(out).expanduser().resolve()
            if p.exists() and not confirm_prompt(f"{p.name} exists – overwrite"):
                print("Export cancelled.")
                continue
            try:
                export_all_metadata(p)
                print(f"Registry exported to {p}")
            except Exception as exc:
                print(f"Error: {exc}")
            continue  # back to top of submenu

        # ── the rest need a target table ────────────────────────────────
        table = table_selection_menu("Target table")
        if table in (None, "(B)"):
            continue
        if table.lower() == "e":
            sys.exit(0)
        try:
            validate_table_name(table)
        except TableNameError as err:
            print(err)
            continue

        # 1) ── show row ─────────────────────────────────────────────────
        if choice == "1":
            show_metadata(table)

        # 2) ── export single row ───────────────────────────────────────
        elif choice == "2":
            out = prompt(
                "Output path (default ./<table>_meta.json) or [B]ack / [E]xit: ",
                default=f"{table}_meta.json",
            )
            if out == "(B)":
                continue
            if out.lower() == "e":
                sys.exit(0)
            p = Path(out).expanduser().resolve()
            if p.exists() and not confirm_prompt(f"{p.name} exists – overwrite"):
                print("Export cancelled.")
                continue
            try:
                export_meta(table, path=p)
                print(f"Metadata exported to {p}")
            except Exception as exc:
                print(f"Error: {exc}")

        # 3) ── edit units / notes ──────────────────────────────────────
        elif choice == "3":
            meta = load_metadata(table)
            if not meta:
                print("No metadata row yet – insert some data first.")
                continue
            res = edit_units_notes(meta)
            if res == "(B)":
                continue
            new_units, new_notes = res
            if new_units is None and new_notes is None:
                print("Nothing modified.")
                continue
            print("\nSummary of changes:")
            if new_units is not None:
                print("  Units:", new_units)
            if new_notes is not None:
                print("  Notes:", repr(new_notes))
            if not confirm_prompt("Save these changes"):
                print("Update cancelled.")
                continue
            try:
                update_metadata(
                    table_name=table,
                    units=new_units,
                    notes=new_notes,
                )
                print("Metadata updated.")
            except Exception as exc:
                print(f"Error: {exc}")

        # 4) ── delete row  (with “export before delete?”) ──────────────
        elif choice == "4":
            if not confirm_prompt(f"Really delete metadata row for '{table}'"):
                continue
            if confirm_prompt("Export to JSON first"):
                backup = Path(f"{table}_meta_backup.json").resolve()
                try:
                    export_meta(table, backup)
                    print(f"Row exported to {backup}")
                except Exception as exc:
                    print(f"Export failed: {exc}")
                    if not confirm_prompt("Proceed with delete anyway"):
                        continue
            try:
                engine = create_engine(
                    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
                    f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DB_HOST')}:"
                    f"{os.getenv('DB_PORT')}/{os.getenv('POSTGRES_DB')}",
                    pool_pre_ping=True,
                )
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            'DELETE FROM "_timeseries_metadata" WHERE table_name = :t'
                        ),
                        {"t": table},
                    )
                print("Row removed (table itself left intact).")
            except Exception as exc:
                print(f"Error deleting row: {exc}")

        # 6) ── rebuild row (delete → recompute) ────────────────────────
        elif choice == "6":
            if not confirm_prompt(f"Regenerate metadata row for '{table}'"):
                continue
            if confirm_prompt("Export current row to JSON first"):
                backup = Path(f"{table}_meta_backup.json").resolve()
                try:
                    export_meta(table, backup)
                    print(f"Row exported to {backup}")
                except Exception as exc:
                    print(f"Export failed: {exc}")
                    if not confirm_prompt("Proceed with rebuild anyway"):
                        continue
            try:
                rebuild_metadata_row(table)
                print("Metadata row regenerated.")
            except Exception as exc:
                print(f"Error: {exc}")

        else:
            print("Pick 1-7.")


# -----------------------------------------------------------------------------
# RETRIEVE DATA MENU
# -----------------------------------------------------------------------------


def list_tables_in_db(*, include_meta: bool = False) -> list[str]:
    """
    Returns a list of public-schema tables.

    Parameters
    ----------
    include_meta : bool
        • False (default) – hides the internal “_timeseries_metadata” table
        • True            – return *all* tables, including the registry
    """
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASS = os.getenv("POSTGRES_PASSWORD")
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    engine_str = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(engine_str)

    query = text(f"""
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_type   = 'BASE TABLE'
           {"AND table_name <> '_timeseries_metadata'" if not include_meta else ""}
         ORDER BY table_name;
    """)

    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query)]


def fetch_data(table_name: str, row_limit: Optional[int]) -> list[dict]:
    """
    Fetches data from a specified table via PostgREST.

    Parameters:
        table_name (str): Name of the table to retrieve data from.
        row_limit (int | None): Optional row limit; if None, retrieves all rows.

    Returns:
        list[dict]: A list of dictionaries representing table rows.
                    Returns an empty list if no data or if an error occurs.

    Notes:
        - Uses GET requests with optional `limit` parameter.
        - Prints error message if request fails.
    """
    params = {}
    if row_limit is not None:
        params["limit"] = row_limit
    try:
        r = requests.get(f"{POSTGREST_URL}/{table_name}", params=params)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from '{table_name}': {e}")
        return []
    return r.json()


def run_retrieve_data():
    """
    Interactive flow for retrieving and exporting data from a TimescaleDB table.

    Steps:
        1) List all public tables in the database.
        2) Let the user select one from the list.
        3) Prompt for number of rows to fetch (or all).
        4) Fetch data via PostgREST and show preview (first 5 rows).
        5) Let user choose export format (CSV, JSON, Excel, TXT).
        6) Save the data to a local file.

    Returns:
        None. Outputs file on success or error message on failure.

    Features:
        - Safe exit and backtracking with [B]ack / [E]xit.
        - Uses `retrieve_data()` from `api.py` to export.
    """
    print("\n=== Retrieve Data ===")
    # 1) List tables
    tables = list_tables_in_db()
    if not tables:
        print("No tables found in the database.")
        return

    print("Available Tables:")
    for i, t in enumerate(tables, start=1):
        print(f"  {i}) {t}")

    # 2) user picks a table
    while True:
        choice = prompt("Select a table by number, or [B]ack / [E]xit: ")
        if choice == "(B)":
            return
        if choice.lower() == "e":
            print("Exiting.")
            sys.exit(0)
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(tables):
                table_name = tables[idx - 1]
                break
        print("Invalid choice. Try again or [B]ack / [E]xit.")

    print(f"Selected table: '{table_name}'")

    # 3) row limit
    while True:
        row_in = prompt(
            "How many rows to retrieve? Positive integer or [A]ll / [B]ack / [E]xit: "
        ).lower()
        if row_in == "(B)":
            return
        elif row_in == "e":
            print("Exiting.")
            sys.exit(0)
        elif row_in == "a":
            row_limit = None
            break
        elif row_in.isdigit() and int(row_in) > 0:
            row_limit = int(row_in)
            break
        print(
            "Invalid input. Enter a positive integer, 'a' for all or [B]ack / [E]xit."
        )

    # 4) fetch
    data_list = fetch_data(table_name, row_limit)
    if not data_list:
        print("No data returned (or error). Aborting retrieval.")
        return
    df = pd.DataFrame(data_list)
    print("\nData preview (first 5 rows):")
    print(df.head())

    # 5) export
    formats = ["csv", "json", "excel", "txt"]
    print("\nChoose export format:")
    for i, f in enumerate(formats, start=1):
        print(f"  {i}) {f.upper()}")

    while True:
        fch = prompt("Select format by number, or [B]ack / [E]xit: ")
        if fch == "(B)":
            return
        if fch.lower() == "e":
            sys.exit(0)
        if fch.isdigit():
            idx = int(fch)
            if 1 <= idx <= len(formats):
                chosen_fmt = formats[idx - 1]
                break
        print("Invalid choice. Try again or [B]ack / [E]xit.")

    # 6) build filename and save

    if chosen_fmt == "excel":
        chosen_fmt = "xlsx"

    file_name = f"{table_name}.{chosen_fmt}"

    try:
        path = retrieve_data(
            table_name=table_name,
            row_limit=row_limit,
            output_format=OutputFormat(chosen_fmt),
            output_path=Path(file_name),
        )
        # print(f"Data successfully saved as '{file_name}' to '{Path}'!")
        print(
            f"\n Export successfully completed!\n File: {path.name}\n Saved to: {path.parent.resolve()}"
        )
    except Exception as e:
        print(f"Error exporting data: {e}")


# -----------------------------------------------------------------------------
# CLI Menu Handlers — Data Retrieval & Export
# -----------------------------------------------------------------------------


def run_grafana_link():
    """
    Interactive flow for generating a Grafana Explore URL.

    Steps:
      1) List tables -> pick one.
      2) Show row count & time range.
      3) List numeric columns -> pick one.
      4) Prompt for max rows to plot
      5) Use full range? Y -> use min/max; N -> custom start/end (YYYY, MM, DD).
      5) Confirm:
           Y -> generate & print URL and return.
           N -> restart at step 1.
           B -> back to step 3.
           E -> exit.
    """
    print("\n=== Generate Grafana Link ===")

    while True:
        # Step 1: Table selection
        tables = list_tables_in_db()
        if not tables:
            print("No tables found.")
            return
        print("\nAvailable tables:")
        for i, t in enumerate(tables, 1):
            print(f"  {i}) {t}")
        tbl_choice = prompt("Select a table by number or [B]ack / [E]xit: ")
        if tbl_choice == "(B)":
            return
        if tbl_choice.lower() == "e":
            sys.exit(0)
        if not (tbl_choice.isdigit() and 1 <= int(tbl_choice) <= len(tables)):
            print("Invalid selection.")
            continue

        table = tables[int(tbl_choice) - 1]
        meta = query_table_metadata(table)
        print(
            f"\n'{table}' -> {meta['row_count']} rows, from {meta['min_time']} to {meta['max_time']}"
        )
        min_dt, max_dt = meta["min_time"], meta["max_time"]

        # Step 3: Column selection
        while True:
            schema = get_table_schema(table)
            numeric = [
                c for c, dt in schema.items() if dt in ("integer", "double precision")
            ]
            if not numeric:
                print("No numeric columns available.")
                return
            print("Numeric columns:")
            for i, col in enumerate(numeric, 1):
                print(f"  {i}) {col}")
            col_choice = prompt("Pick a column by number or [B]ack / [E]xit: ")
            if col_choice == "(B)":
                break  # back to table loop
            if col_choice.lower() == "e":
                sys.exit(0)
            if not (col_choice.isdigit() and 1 <= int(col_choice) <= len(numeric)):
                print("Invalid selection.")
                continue

            value_col = numeric[int(col_choice) - 1]

            # Step 4: Row‐limit prompt
            while True:
                lim = prompt(
                    "Max rows to plot (positive integer, default 1000) or [B]ack: ",
                    default="1000",
                )
                if lim == "(B)":
                    break  # back to column loop
                if not lim.isdigit() or int(lim) <= 0:
                    print(" Enter a positive integer or [B]ack.")
                    continue
                limit = int(lim)
                break
            else:
                continue  # user backed out -> re-prompt column
            # if user hit back:
            if lim == "(B)":
                continue

            # Step 5: Time‐range
            while True:
                use_full = prompt(
                    "Use full time range? ([Y]es / [N]o / [E]xit): ", default="Y"
                ).lower()
                if use_full in ("y", "yes", ""):
                    start_time, end_time = min_dt, max_dt
                    break
                if use_full in ("e", "exit"):
                    sys.exit(0)
                if use_full in ("n", "no"):
                    # collect custom start & end using the top-level ask_date
                    while True:
                        start = ask_date("Start", min_dt, max_dt)
                        if start is None:
                            break  # user hit [B]ack → go back to full/custom prompt
                        end = ask_date("End", min_dt, max_dt)
                        if end is None:
                            break
                        if start > end:
                            print("↳ Start must be ≤ End; try again.")
                            continue
                        # if they chose the same date, our helper will return min_dt/max_dt or date midnight:
                        start_time, end_time = start, end
                        break
                    # if they backed out completely, re-prompt full/custom
                    if "start_time" not in locals():
                        continue
                    break
                print("Please enter Y, N, or E.")

            # Auto-expand single-point ranges
            if start_time == end_time:
                print(" Same date entered; plotting the full 24 h of that day instead.")
                end_time = start_time + timedelta(days=1)

            # Step 6: Confirmation
            while True:
                print("\nSummary:")
                print(f"  Table      : {table}")
                print(f"  Y-axis col : {value_col}")
                print(f"  Max rows   : {limit}")
                print(f"  Time range : {start_time} -> {end_time}")
                ans = prompt(
                    "Generate Grafana URL? ([Y]es / [N]o=restart table / [B]ack=column / [E]xit): "
                ).lower()
                if ans in ("y", "yes"):
                    url = get_grafana_url(
                        table_name=table,
                        value_col=value_col,
                        from_time=start_time,
                        to_time=end_time,
                        limit=limit,
                    )
                    print("\nGrafana Explore URL:\n", url, "\n")
                    return
                if ans in ("n", "no"):
                    break  # out -> back to table loop
                if ans in ("b", "back"):
                    break  # out -> back to column loop
                if ans in ("e", "exit"):
                    sys.exit(0)
                print("Please enter Y, N, B, or E.")

            # if they chose “no” -> restart at table selection
            if ans in ("n", "no"):
                break  # out to table loop


# -----------------------------------------------------------------------------
# Main Menu Loop & Entrypoint
# -----------------------------------------------------------------------------


def main_menu():
    """
    Displays the top-level menu and prompts the user to choose an action.

    Menu Options:
        1) Create Table Only
        2) Insert Data Only
        3) Insert Single Row
        4) Create Table + Insert Data
        5) Retrieve Data
        6) Generate Grafana Link
        7) Metadata tools
        8) Exit

    Returns:
        str: User's selected option (defaults to '8' if blank).
             Returns "(B)" for back, or exits on 'E'.
    """
    print("\n=== TimescaleDB Ingestion CLI ===")
    print("1) Create Table Only")
    print("2) Insert Data Only")
    print("3) Insert Single Row")
    print("4) Create Table + Insert Data")
    print("5) Retrieve Data")
    print("6) Generate Grafana Link")
    print("7) Metadata tools")
    print("8) Exit")
    return prompt("Select (1-8): ", default="8")


def cli_loop():
    """
    Main interactive loop for the TimescaleDB CLI.

    Repeatedly shows the main menu and dispatches to:
      - run_create_table()
      - run_insert_data()
      - run_insert_single_row()
      - run_create_and_insert()
      - run_retrieve_data()
      - run_grafana_link()
      - run_metadata_menu()

    Handles invalid inputs, back commands, and clean exit.
    """
    while True:
        choice = main_menu()
        if choice == "(B)":
            continue
        if choice.lower() == "e":
            print("Exiting.")
            sys.exit(0)

        if choice == "1":
            run_create_table()
        elif choice == "2":
            run_insert_data()
        elif choice == "3":
            run_insert_single_row()
        elif choice == "4":
            run_create_and_insert()
        elif choice == "5":
            run_retrieve_data()
        elif choice == "6":
            run_grafana_link()
        elif choice == "7":
            run_metadata_menu()
        elif choice == "8":
            print("Exiting. Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice. Please pick 1-8.")


def main():
    """
    Entry point for the CLI script.

    Launches the interactive menu loop.
    """
    cli_loop()


if __name__ == "__main__":
    main()
