import subprocess
import sys
from pathlib import Path
from typing import Dict, Generator, List, Optional

import duckdb
import numpy as np
import pytest

from vail.registry import RegistryInterface  # For global_registry interaction
from vail.utils.env import load_env

from .test_local_registry import (
    cleanup_database,
    global_registry,
    local_registry,
    sample_model_info,
    sample_source_info,
)

# Load test environment variables to ensure we use the test database
load_env("test")

# Expected tables to be created by 'vail init' in a default local setup
EXPECTED_TABLES_IN_INIT = sorted(
    ["models", "model_sources", "fingerprints", "hardware_info", "sync_metadata"]
)

# Columns to exclude from direct content comparison for certain tables
# because their timestamps are expected to change on re-runs.
# Or, their actual values are not deterministic for idempotency check (e.g. sync timestamp itself)
VOLATILE_COLUMNS_BY_TABLE = {
    "hardware_info": ["last_updated"],
    "models": [
        "created_at",
        "last_updated",
    ],  # Local created_at/last_updated will change
    "model_sources": [
        "created_at",
        "last_updated",
    ],  # Local created_at/last_updated will change
    "fingerprints": [
        "created_at",
        "last_updated",
    ],  # Local created_at/last_updated will change
    "sync_metadata": [
        "value"
    ],  # The timestamp value for 'models_last_sync' will change
}

# Command to run vail init. Using "python -m vail.cli" is more robust.
VAIL_CLI_MODULE = "vail.cli"


@pytest.fixture
def temp_db_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Pytest fixture to provide a temporary directory and a .duckdb path within it."""
    db_path = tmp_path / "test_registry.duckdb"
    yield db_path
    # Teardown: Ensure the db file and its .wal file are removed after the test
    if db_path.exists():
        db_path.unlink()
    wal_path = tmp_path / "test_registry.duckdb.wal"
    if wal_path.exists():
        wal_path.unlink()


def run_vail_init_cmd(db_path: Path, global_db_url: Optional[str] = None):
    """Helper function to execute the 'vail init' command."""
    command = [
        sys.executable,
        "-m",
        VAIL_CLI_MODULE,
        "init",
        "--local-db-path",
        str(db_path),
        "--no-env-file",
        "--database-url",
        global_db_url,
        "--sync-all-models",
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    result.check_returncode()  # Raise an exception if return code is non-zero


def get_db_state_for_idempotency_check(db_path: Path) -> dict:
    """
    Captures the state of the database relevant for the idempotency check.
    - Schema: list of table names.
    - Content: data from expected tables; volatile columns are excluded.
    """
    state = {"schema": [], "content": {}}
    # If db_path does not exist, duckdb.connect below will raise an error,
    # which is desired behavior for the test to fail clearly.

    with duckdb.connect(str(db_path), read_only=True) as conn:
        tables_in_db_query = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        ).fetchall()
        state["schema"] = sorted(
            [
                row[0]
                for row in tables_in_db_query
                if not row[0].endswith("_id_seq") and row[0] != "vail_init_test"
            ]
        )

        for table_name in EXPECTED_TABLES_IN_INIT:
            if table_name not in state["schema"]:
                # This case should ideally not be reached if schema check is robust.
                # If a table is missing, it implies an issue with init.
                # The test will likely fail on schema assertion or here if this path is taken.
                state["content"][table_name] = "Table Missing"
                continue

            cols_info_query = conn.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()
            all_column_names = [col[1] for col in cols_info_query]

            columns_to_select = []
            volatile_cols_for_table = VOLATILE_COLUMNS_BY_TABLE.get(table_name, [])

            for col_name in all_column_names:
                if col_name not in volatile_cols_for_table:
                    columns_to_select.append(col_name)

            if not columns_to_select:
                if table_name == "sync_metadata" and "key" in all_column_names:
                    # Check if 'models_last_sync' key exists, as its value is volatile
                    sync_key_present = conn.execute(
                        "SELECT 1 FROM sync_metadata WHERE key = 'models_last_sync' LIMIT 1"
                    ).fetchone()
                    if sync_key_present:
                        state["content"][table_name] = "'models_last_sync' key exists"
                    else:
                        state["content"][table_name] = (
                            "No non-volatile columns to select, and 'models_last_sync' key not found"
                        )
                else:
                    state["content"][table_name] = "No non-volatile columns to select"
                continue

            # Determine ORDER BY clause for stable comparison
            order_by_clause = ""
            if table_name == "models":
                if "id" in columns_to_select:
                    order_by_clause = " ORDER BY id"
            elif table_name == "model_sources":
                # Order by model_id (FK), then by its own PK if available and selected
                order_parts = []
                if "model_id" in columns_to_select:
                    order_parts.append("model_id")
                if "id" in columns_to_select:
                    order_parts.append("id")
                if order_parts:
                    order_by_clause = f" ORDER BY {', '.join(order_parts)}"
            elif table_name == "fingerprints":
                order_parts = []
                if "model_id" in columns_to_select:
                    order_parts.append("model_id")
                if "id" in columns_to_select:
                    order_parts.append("id")  # its own PK
                if "fingerprint_type" in columns_to_select:
                    order_parts.append("fingerprint_type")
                if order_parts:
                    order_by_clause = f" ORDER BY {', '.join(order_parts)}"
            elif table_name == "hardware_info":  # Only one row expected
                if "id" in columns_to_select:
                    order_by_clause = " ORDER BY id"
            # For sync_metadata, if 'key' is selected, it's the natural order.
            elif table_name == "sync_metadata":
                if "key" in columns_to_select:
                    order_by_clause = " ORDER BY key"

            query = f"SELECT {', '.join(columns_to_select)} FROM {table_name}{order_by_clause}"

            if table_name == "sync_metadata" and columns_to_select == ["key"]:
                data = conn.execute(
                    f"SELECT key FROM {table_name} WHERE key = 'models_last_sync' {order_by_clause}"
                ).fetchall()
                if data and data[0][0] == "models_last_sync":
                    state["content"][table_name] = "'models_last_sync' key exists"
                else:
                    state["content"][table_name] = conn.execute(query).fetchall()
            else:
                state["content"][table_name] = conn.execute(query).fetchall()
    return state  # Return the collected state


# We need the global_registry and cleanup_database fixtures from test_local_registry
# Pytest should discover them. We also need sample_model_info.
# If they are not automatically discovered, we might need to import them explicitly
# or adjust the pytest configuration (e.g. conftest.py)


def test_vail_init_with_sync_db_idempotency(
    temp_db_dir: Path,
    global_registry: RegistryInterface,  # From test_local_registry.py
    sample_model_info: List[Dict],  # From test_local_registry.py
    sample_source_info: List[Dict],  # From test_local_registry.py
    # cleanup_database fixture is autouse=True in test_local_registry.py
):
    """
    Tests that running 'vail init' twice with model syncing does not change
    the significant contents or schema of the local database.
    """
    db_path = temp_db_dir
    global_db_url = global_registry.connection_string  # Use the test global DB

    # --- Setup: Add a model to the global registry ---
    # Make model name unique for this test run to avoid stale data
    model_to_add_global = sample_model_info[0].copy()
    model_source_to_add_global = sample_source_info[0].copy()
    global_model_name = model_to_add_global["model_name"]

    global_model_id = global_registry.add_model(model_info=model_to_add_global)
    assert global_model_id is not None, (
        f"Failed to add model {global_model_name} to global_registry"
    )
    # Then, add the source explicitly

    global_registry.add_model_source(
        model_id=global_model_id,
        source_type=model_source_to_add_global["source_type"],
        source_info=model_source_to_add_global,  # Pass the whole source dict here for convenience,
        # although including source_type within this dict is redundant.
    )

    # Add a dummy fingerprint to the global model
    global_registry.register_fingerprint(
        model_id=global_model_id,
        fingerprint_type="test_fp",
        fingerprint_vector=np.array([0.1, 0.2]),
        fingerprint_config={"version": "1.0"},
    )

    # Verify global DB state before subprocess call
    with global_registry._get_connection() as conn_verify:
        with conn_verify.cursor() as cur_verify:
            cur_verify.execute(
                "SELECT id, source_type, source_identifier FROM dev.model_sources WHERE model_id = %s",
                (global_model_id,),
            )
            sources_in_db = cur_verify.fetchall()
            print(
                f"VERIFY GLOBAL DB: Sources for model_id {global_model_id}: {sources_in_db}"
            )

    # 1. Run vail init first time (with sync)
    run_vail_init_cmd(db_path, global_db_url=global_db_url)
    db_state1 = get_db_state_for_idempotency_check(db_path)

    # --- Sanity checks for the first run ---
    assert db_state1["schema"] == EXPECTED_TABLES_IN_INIT, (
        f"Initial 'vail init' did not create the expected tables. Found: {db_state1['schema']}"
    )

    # hardware_info checks
    assert (
        isinstance(db_state1["content"]["hardware_info"], list)
        and len(db_state1["content"]["hardware_info"]) == 1
    ), "hardware_info table should have one row."

    # Check model related tables (content based on non-volatile columns)
    print("***DB STATE 1 CONTENT***", db_state1["content"])

    assert len(db_state1["content"]["models"]) == 1, (
        f"Expected 1 model synced, found content: {db_state1['content']['models']}"
    )
    assert len(db_state1["content"]["model_sources"]) == 1, (
        f"Expected 1 model source synced, found content: {db_state1['content']['model_sources']}"
    )

    assert len(db_state1["content"]["fingerprints"]) == 1, (
        f"Expected 1 fingerprint synced, found content: {db_state1['content']['fingerprints']}"
    )

    # Check a specific non-volatile field of the synced model
    # Querying the model table directly for more specific check of synced data.
    with duckdb.connect(str(db_path), read_only=True) as conn:
        synced_model_name_tuple = conn.execute(
            "SELECT model_name FROM models ORDER BY id LIMIT 1"
        ).fetchone()
    assert (
        synced_model_name_tuple is not None
        and synced_model_name_tuple[0] == global_model_name
    ), (
        f"Synced model name incorrect. Expected {global_model_name}, got {synced_model_name_tuple[0] if synced_model_name_tuple else 'None'}"
    )

    # sync_metadata check
    assert db_state1["content"]["sync_metadata"] == "'models_last_sync' key exists", (
        f"sync_metadata content incorrect after first sync: {db_state1['content']['sync_metadata']}"
    )

    # 2. Run vail init second time (with sync)

    run_vail_init_cmd(db_path, global_db_url=global_db_url)
    db_state2 = get_db_state_for_idempotency_check(db_path)

    # 3. Compare the states
    assert db_state1["schema"] == db_state2["schema"], (
        f"Database schema changed after second init.\\nSchema 1: {db_state1['schema']}\\nSchema 2: {db_state2['schema']}"
    )

    for table_name in EXPECTED_TABLES_IN_INIT:
        assert db_state1["content"][table_name] == db_state2["content"][table_name], (
            f"Content of table '{table_name}' changed after second init.\\nState 1: {db_state1['content'][table_name]}\\nState 2: {db_state2['content'][table_name]}"
        )
