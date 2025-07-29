# src/autoclean/utils/database.py
"""Database utilities for the autoclean package using SQLite."""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from autoclean.utils.logging import message

# Global lock for thread safety
_db_lock = threading.Lock()

# Global database path
DB_PATH = None


def set_database_path(path: Path) -> None:
    """Set the global database path.

    Parameters
    ----------
    path : Path
        The path to the autoclean directory.
    """
    global DB_PATH  # pylint: disable=global-statement
    DB_PATH = path


class DatabaseError(Exception):
    """Custom exception for database operations."""

    def __init__(self, error_message: str):
        self.message = error_message
        super().__init__(self.message)


class RecordNotFoundError(Exception):
    """Custom exception for when a database record is not found."""

    def __init__(self, error_message: str):
        self.message = error_message
        super().__init__(self.message)


def _serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format.

    Parameters
    ----------
    obj : Any
        Object to serialize.

    Returns
    -------
    Any
        JSON-serializable object.
    """
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        # Preserve all dictionary keys and values, converting non-serializable values to strings
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        return str(obj)


def get_run_record(run_id: str) -> dict:
    """Get a run record from the database by run ID.

    Parameters
    ----------
    run_id : str
        The string ID of the run to retrieve.

    Returns
    -------
    run_record : dict
        The run record if found, None if not found
    """
    run_record = manage_database(operation="get_record", run_record={"run_id": run_id})
    return run_record


def _validate_metadata(metadata: dict) -> bool:
    """Validates metadata structure and types.

    Parameters
    ----------
    metadata : dict
        The metadata to validate.

    Returns
    -------
    bool
        True if the metadata is valid, False otherwise.
    """
    if not isinstance(metadata, dict):
        return False
    return all(isinstance(k, str) for k in metadata.keys())


def _get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Get a database connection with proper configuration.

    Parameters
    ----------
    db_path : Path
        Path to the SQLite database file.

    Returns
    -------
    sqlite3.Connection
        Configured database connection.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
    return conn


def manage_database(
    operation: str,
    run_record: Optional[Dict[str, Any]] = None,
    update_record: Optional[Dict[str, Any]] = None,
) -> Any:
    """Manage database operations with thread safety.

    Parameters
    ----------
    operation : str
        Operations can be:

        - **create_collection**: Create a new collection.
        - **store**: Store a new record.
        - **update**: Update an existing record.
        - **update_status**: Update the status of an existing record.
        - **drop_collection**: Drop the collection.
        - **get_collection**: Get the collection.
        - **get_record**: Get a record from the collection.

    run_record : dict
        The record to store.
    update_record : dict
        The record updates.

    Returns
    -------
    Any
        Operation-specific return value.
    """
    db_path = DB_PATH / "pipeline.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _db_lock:  # Ensure only one thread can access the database at a time
        try:
            conn = _get_db_connection(db_path)
            cursor = conn.cursor()

            if operation == "create_collection":
                # Create table only if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL,
                        task TEXT,
                        unprocessed_file TEXT,
                        status TEXT,
                        success BOOLEAN,
                        json_file TEXT,
                        report_file TEXT,
                        metadata TEXT,
                        error TEXT
                    )
                """
                )
                conn.commit()
                message("info", f"✓ Ensured 'pipeline_runs' table exists in {db_path}")

            elif operation == "store":
                if not run_record:
                    raise ValueError("Missing run_record for store operation")

                # Convert metadata to JSON string, handling Path objects
                metadata_json = json.dumps(
                    _serialize_for_json(run_record.get("metadata", {}))
                )

                cursor.execute(
                    """
                    INSERT INTO pipeline_runs (
                        run_id, created_at, task, unprocessed_file, status,
                        success, json_file, report_file, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        run_record["run_id"],
                        run_record.get("timestamp", datetime.now().isoformat()),
                        run_record.get("task"),
                        (
                            str(run_record.get("unprocessed_file"))
                            if run_record.get("unprocessed_file")
                            else None
                        ),
                        run_record.get("status"),
                        run_record.get("success", False),
                        (
                            str(run_record.get("json_file"))
                            if run_record.get("json_file")
                            else None
                        ),
                        (
                            str(run_record.get("report_file"))
                            if run_record.get("report_file")
                            else None
                        ),
                        metadata_json,
                    ),
                )
                conn.commit()
                record_id = cursor.lastrowid
                message("info", f"✓ Stored new record with ID: {record_id}")
                return record_id

            elif operation in ["update", "update_status"]:
                if not update_record or "run_id" not in update_record:
                    raise ValueError("Missing run_id in update_record")

                run_id = update_record["run_id"]

                # Check if record exists
                cursor.execute(
                    "SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)
                )
                existing_record = cursor.fetchone()

                if not existing_record:
                    raise RecordNotFoundError(f"No record found for run_id: {run_id}")

                if operation == "update_status":
                    cursor.execute(
                        """
                        UPDATE pipeline_runs
                        SET status = ?
                        WHERE run_id = ?
                    """,
                        (
                            f"{update_record['status']} at {datetime.now().isoformat()}",
                            run_id,
                        ),
                    )
                else:
                    update_components = []
                    current_update_values = []  # Using a distinct name for clarity

                    # Handle metadata update if 'metadata' key exists in update_record
                    if "metadata" in update_record:
                        metadata_to_update = update_record["metadata"]
                        if not _validate_metadata(metadata_to_update):
                            raise ValueError("Invalid metadata structure for update")

                        # Fetch existing metadata
                        cursor.execute(
                            "SELECT metadata FROM pipeline_runs WHERE run_id = ?",
                            (run_id,),
                        )
                        row_with_metadata = cursor.fetchone()
                        existing_metadata_str = (
                            row_with_metadata["metadata"] if row_with_metadata else "{}"
                        )
                        current_metadata = json.loads(existing_metadata_str or "{}")

                        # Serialize the new metadata fragment and merge it
                        serialized_new_metadata_fragment = _serialize_for_json(
                            metadata_to_update
                        )
                        current_metadata.update(serialized_new_metadata_fragment)
                        final_metadata_json = json.dumps(current_metadata)

                        update_components.append("metadata = ?")
                        current_update_values.append(final_metadata_json)

                    # Handle other fields present in update_record
                    for key, value in update_record.items():
                        if key == "run_id" or key == "metadata":
                            continue

                        update_components.append(f"{key} = ?")
                        if isinstance(value, Path):
                            current_update_values.append(str(value))
                        else:
                            current_update_values.append(value)

                    # Only execute the UPDATE SQL statement if there are actual fields to set
                    if update_components:
                        # Add the run_id for the WHERE clause; it's the last parameter for the query
                        current_update_values.append(run_id)

                        set_clause_sql = ", ".join(update_components)
                        query = f"UPDATE pipeline_runs SET {set_clause_sql} WHERE run_id = ?"

                        cursor.execute(query, tuple(current_update_values))
                    else:
                        message(
                            "debug",
                            f"For 'update' operation on run_id '{run_id}', no non-metadata fields were identified for SET clause. update_record: {update_record}. Metadata might have been updated if processed.",
                        )

                conn.commit()
                message("debug", f"Record {operation} successful for run_id: {run_id}")

            elif operation == "drop_collection":
                cursor.execute("DROP TABLE IF EXISTS pipeline_runs")
                conn.commit()
                message("warning", f"'pipeline_runs' table dropped from {db_path}")

            elif operation == "get_collection":
                cursor.execute("SELECT * FROM pipeline_runs")
                records = [dict(row) for row in cursor.fetchall()]
                return records

            elif operation == "get_record":
                if not run_record or "run_id" not in run_record:
                    raise ValueError("Missing run_id in run_record")

                cursor.execute(
                    "SELECT * FROM pipeline_runs WHERE run_id = ?",
                    (run_record["run_id"],),
                )
                record = cursor.fetchone()

                if not record:
                    raise RecordNotFoundError(
                        f"No record found for run_id: {run_record['run_id']}"
                    )

                # Convert record to dict and parse metadata JSON
                record_dict = dict(record)
                if record_dict.get("metadata"):
                    record_dict["metadata"] = json.loads(record_dict["metadata"])
                return record_dict

            conn.close()

        except Exception as e:
            error_context = {
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
            message("error", f"Database operation failed: {error_context}")
            raise DatabaseError(f"Operation '{operation}' failed: {e}") from e
