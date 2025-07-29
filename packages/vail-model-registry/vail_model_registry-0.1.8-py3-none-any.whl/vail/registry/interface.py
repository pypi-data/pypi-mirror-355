"""
Registry Interface for the Unified Fingerprinting Framework

This module provides an interface to the model registry database for fingerprinting.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

from vail.utils import setup_logging

from .models import Model, ModelFilterCriteria

# Set up logging
logger = setup_logging(log_file_name="model_registry.log")


class RegistryInterface:
    """Interface for interacting with the model registry database."""

    @property
    def registry_type(self) -> str:
        return "global"

    def __init__(self, connection_string: str, use_production: bool = False):
        """
        Initialize the registry interface.

        Args:
            connection_string: PostgreSQL connection string
            use_production: Whether to use the production database schema (default: False, use dev)
        """
        self.connection_string = connection_string
        self.schema = "prod" if use_production else "dev"

    # ============= Private Methods =============

    def _get_connection(self):
        """Get a database connection."""
        conn = psycopg2.connect(self.connection_string)
        # The following enables the pgvector extension to work in these schemas
        conn.cursor().execute("SET search_path TO dev, prod, public;")
        register_vector(conn)
        return conn

    @staticmethod
    def setup_global_registry(connection_string: str):
        """Set up the necessary database tables and extensions in both dev and prod schemas."""
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Create pgvector extension if it doesn't exist
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Create schemas if they don't exist
                cur.execute("CREATE SCHEMA IF NOT EXISTS dev;")
                cur.execute("CREATE SCHEMA IF NOT EXISTS prod;")

                for schema in ["dev", "prod"]:
                    # Create models table
                    cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema}.models (
                        id SERIAL PRIMARY KEY,
                        model_maker TEXT,
                        model_name TEXT,
                        params_count BIGINT,
                        context_length BIGINT,
                        quantization TEXT,
                        license TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                    # Create model_sources table
                    cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema}.model_sources (
                        id SERIAL PRIMARY KEY,
                        model_id INTEGER REFERENCES {schema}.models(id),
                        source_type TEXT NOT NULL,                            -- huggingface_api, openai, anthropic, ollama, etc.
                        source_identifier JSON NOT NULL,                      -- repo_id, model name, etc.
                        requires_auth BOOLEAN DEFAULT FALSE,                  -- Whether authentication is required
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                    # Create fingerprints table
                    cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema}.fingerprints (
                        id SERIAL PRIMARY KEY,
                        model_id INTEGER REFERENCES {schema}.models(id),
                        fingerprint_type TEXT NOT NULL,                       -- input_output, weight, architecture
                        fingerprint_vector vector,                      -- Vector representation for similarity search
                        fingerprint_config JSONB,                             -- Configuration used to generate the fingerprint
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                conn.commit()

    # ============= Public Methods =============

    def get_model_loader_info(self, model_id: str) -> Dict:
        """
        Get model loader information from the registry.

        Args:
            model_id: ID of the model

        Returns:
            Dictionary with model loader information including all model data and sources
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Query model and sources in a single join query
                cur.execute(
                    f"""
                    SELECT 
                        m.id as model_id,
                        m.model_maker,
                        m.model_name,
                        m.params_count,
                        m.context_length,
                        m.quantization,
                        m.license,
                        m.created_at as model_created_at,
                        m.last_updated as model_last_updated,
                        s.id as source_id,
                        s.source_type,
                        s.source_identifier,
                        s.requires_auth,
                        s.created_at as source_created_at,
                        s.last_updated as source_last_updated
                    FROM {self.schema}.models m
                    LEFT JOIN {self.schema}.model_sources s ON m.id = s.model_id
                    WHERE m.id = %s
                """,
                    (model_id,),
                )

                results = cur.fetchall()

                # Construct comprehensive model info dictionary
                model_info = {
                    "model_id": str(results[0][0]),
                    "model_maker": results[0][1],
                    "model_name": results[0][2],
                    "params_count": results[0][3],
                    "context_length": results[0][4],
                    "quantization": results[0][5],
                    "license": results[0][6],
                    "created_at": results[0][7].isoformat() if results[0][7] else None,
                    "last_updated": results[0][8].isoformat()
                    if results[0][8]
                    else None,
                    "sources": [],
                }

                # Add all sources
                for row in results:
                    if row[9]:  # If source_id is not None
                        source = {
                            "source_id": row[9],
                            "source_type": row[10],
                            "source_identifier": row[11],
                            "requires_auth": row[12],
                            "created_at": row[13].isoformat() if row[13] else None,
                            "last_updated": row[14].isoformat() if row[14] else None,
                        }
                        model_info["sources"].append(source)

                return model_info

    def remove_model(self, model_id: str):
        """
        Remove a model from the registry.

        Args:
            model_id: ID of the model to remove
        """
        with self._get_connection() as conn:
            logger.info(f"Removing model with ID: {model_id} from {self.schema} schema")
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {self.schema}.fingerprints
                    WHERE model_id = %s
                """,
                    (model_id,),
                )

                cur.execute(
                    f"""
                    DELETE FROM {self.schema}.model_sources
                    WHERE model_id = %s
                """,
                    (model_id,),
                )

                cur.execute(
                    f"""
                    DELETE FROM {self.schema}.models
                    WHERE id = %s
                """,
                    (model_id,),
                )

                conn.commit()

    def add_model(self, model_info: Dict, override_checks: bool = False) -> str:
        """
        Add a model to the registry.

        Args:
            model_info: Dictionary containing model information
            override_checks: Whether to override validation checks (for prod schema)

        Returns:
            str: ID of the added model
        """
        with self._get_connection() as conn:
            logger.info(f"Adding model: {model_info} to {self.schema} schema")

            # For production schema, perform validation checks
            if self.schema == "prod" and not override_checks:
                with conn.cursor() as cur:
                    # Check if model with same name already exists
                    cur.execute(
                        f"""
                        SELECT id FROM {self.schema}.models 
                        WHERE LOWER(model_name) = LOWER(%s)
                    """,
                        (model_info.get("model_name", ""),),
                    )

                    existing_model = cur.fetchone()

                    if existing_model:
                        logger.warning(
                            f"Model with name {model_info.get('model_name')} already exists in production database. Skipping."
                        )
                        return str(existing_model[0])

            with conn.cursor() as cur:
                # First try to get existing model
                cur.execute(
                    """
                    SELECT id FROM models WHERE model_name = %s
                """,
                    (model_info.get("model_name", None),),
                )
                existing = cur.fetchone()

                if existing:
                    logger.info(f"Model {model_info.get('model_name')} already exists")
                    return str(existing[0])

                # If not exists, insert new model
                cur.execute(
                    """
                    INSERT INTO models (model_maker, model_name, params_count, context_length, quantization, license, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        model_info.get("model_maker", None),
                        model_info.get("model_name", None),
                        model_info.get("params_count", None),
                        model_info.get("context_length", None),
                        model_info.get("quantization", None),
                        model_info.get("license", None),
                        model_info.get("created_at", datetime.now()),
                    ),
                )
                return str(cur.fetchone()[0])

    def add_model_source(
        self,
        model_id: str,
        source_type: str,
        source_info: Dict,
        override_checks: bool = False,
    ) -> str:
        """
        Add a source for a model in the registry.

        Args:
            model_id: ID of the model
            source_type: Type of source (huggingface, openai, anthropic, ollama, etc.)
            source_info: Dictionary containing source information
            override_checks: Whether to override validation checks (for prod schema)

        Returns:
            str: ID of the added model source
        """
        with self._get_connection() as conn:
            logger.info(f"Adding model source: {source_info} to {self.schema} schema")

            # For production schema, perform validation checks
            if self.schema == "prod" and not override_checks:
                with conn.cursor() as cur:
                    # Check if source with same identifier already exists
                    source_identifier = source_info.get("source_identifier", None)
                    if source_identifier:
                        # Ensure source_identifier is converted to JSON string for comparison
                        source_identifier_json = json.dumps(source_identifier)
                        cur.execute(
                            f"""
                            SELECT id FROM {self.schema}.model_sources 
                            WHERE LOWER(source_identifier::text) = LOWER(%s)
                        """,
                            (source_identifier_json,),
                        )

                        if cur.fetchone():
                            logger.warning(
                                f"Model source with identifier {source_identifier} already exists in production database. Skipping."
                            )
                            return None

            # Convert source_identifier to JSON string if it's a dictionary
            source_identifier = source_info.get("source_identifier", None)
            if isinstance(source_identifier, dict):
                source_identifier_json = json.dumps(source_identifier)
            else:
                source_identifier_json = source_identifier

            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.schema}.model_sources (model_id, source_type, source_identifier, requires_auth, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        model_id,
                        source_type,
                        source_identifier_json,
                        source_info.get("requires_auth", False),
                        source_info.get("created_at", datetime.now()),
                    ),
                )
                source_id = str(cur.fetchone()[0])

                # Update the parent model's last_updated timestamp
                cur.execute(
                    f"""
                    UPDATE {self.schema}.models 
                    SET last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """,
                    (model_id,),
                )

                return source_id

    # ============= Fingerprint Methods =============

    def register_fingerprint(
        self,
        model_id: str,
        fingerprint_type: str,
        fingerprint_vector: np.ndarray,
        fingerprint_config: Dict,
        override_checks: bool = False,
    ) -> str:
        """
        Register a fingerprint with the registry.

        Args:
            model_id: ID of the model
            fingerprint_type: Type of fingerprint (input_output, weight, architecture)
            fingerprint_vector: Fingerprint data as numpy array
            fingerprint_config: Configuration used to generate the fingerprint
            override_checks: Whether to override validation checks (for prod schema)

        Returns:
            str: ID of the registered fingerprint
        """
        # Convert the fingerprint data to the format expected by the registry
        fingerprint_vector = fingerprint_vector.flatten()

        # Register the fingerprint
        with self._get_connection() as conn:
            logger.info(
                f"Registering fingerprint of type {fingerprint_type} for model {model_id} in {self.schema} schema"
            )

            # For production schema, perform validation checks
            if self.schema == "prod" and not override_checks:
                with conn.cursor() as cur:
                    # 1. Check if identical fingerprint_vector already exists
                    cur.execute(
                        f"""
                        SELECT id FROM {self.schema}.fingerprints 
                        WHERE fingerprint_vector = %s::vector
                    """,
                        (fingerprint_vector.tolist(),),
                    )

                    if cur.fetchone():
                        logger.warning(
                            "Identical fingerprint vector already exists in production database. Skipping."
                        )
                        return None

                    # 2. Check if another fingerprint already exists for this model_id and fingerprint_type
                    cur.execute(
                        f"""
                        SELECT id FROM {self.schema}.fingerprints 
                        WHERE model_id = %s AND fingerprint_type = %s
                    """,
                        (model_id, fingerprint_type),
                    )

                    if cur.fetchone():
                        logger.warning(
                            f"Fingerprint for model_id {model_id} with type {fingerprint_type} already exists in production database. Skipping."
                        )
                        return None

            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.schema}.fingerprints 
                    (model_id, fingerprint_type, fingerprint_vector, fingerprint_config)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        model_id,
                        fingerprint_type,
                        fingerprint_vector.tolist(),
                        json.dumps(fingerprint_config),
                    ),
                )

                fingerprint_id = cur.fetchone()[0]
                conn.commit()

                return str(fingerprint_id)

    def get_fingerprint(
        self, model_id: str, fingerprint_type: str
    ) -> Optional[np.ndarray]:
        """
        Get a fingerprint from the registry.

        Args:
            model_id: ID of the model
            fingerprint_type: Type of fingerprint (input_output, weight, architecture)

        Returns:
            Fingerprint as numpy array, or None if not found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT fingerprint_vector
                    FROM {self.schema}.fingerprints
                    WHERE model_id = %s AND fingerprint_type = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (model_id, fingerprint_type),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                # Convert to numpy array
                return np.array(row[0])

    def get_fingerprint_config(
        self, model_id: str, fingerprint_type: str
    ) -> Optional[Dict]:
        """
        Get a fingerprint configuration from the registry.

        Args:
            model_id: ID of the model
            fingerprint_type: Type of fingerprint (input_output, weight, architecture)

        Returns:
            Fingerprint configuration as a dictionary, or None if not found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT fingerprint_config
                    FROM {self.schema}.fingerprints
                    WHERE model_id = %s AND fingerprint_type = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (model_id, fingerprint_type),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                # Convert from JSON string to dictionary
                if isinstance(row[0], str):
                    return json.loads(row[0])
                return row[0]

    def get_all_fingerprints(self, model_id: str) -> Dict[str, Dict]:
        """
        Get all fingerprints for a model from the registry.

        Args:
            model_id: ID of the model

        Returns:
            Dictionary mapping fingerprint types to their data and config, or empty dict if none found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        id,
                        fingerprint_type,
                        fingerprint_vector,
                        fingerprint_config,
                        created_at,
                        last_updated
                    FROM {self.schema}.fingerprints
                    WHERE model_id = %s
                    ORDER BY created_at DESC
                """,
                    (model_id,),
                )

                fingerprints = {}
                for row in cur.fetchall():
                    fingerprint_type = row[1]
                    fingerprint_vector = row[2]
                    fingerprint_config = row[3]
                    created_at = row[4]
                    last_updated = row[5]

                    # Convert config from JSON string if needed
                    if isinstance(fingerprint_config, str):
                        fingerprint_config = json.loads(fingerprint_config)

                    fingerprints[fingerprint_type] = {
                        "id": row[0],
                        "vector": fingerprint_vector,
                        "config": fingerprint_config,
                        "created_at": created_at,
                        "last_updated": last_updated,
                    }

                return fingerprints

    # ============= Model Search & Count Methods =============

    def get_model_id_from_source_id(self, source_id: str) -> str:
        """Retrieve the model_id associated with a given source_id."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT model_id FROM {self.schema}.model_sources WHERE id = %s",
                        (source_id,),
                    )
                    result = cur.fetchone()
                    if result:
                        return str(result[0])
                    else:
                        return None
        except Exception as e:
            logger.error(f"Error fetching model_id for source_id {source_id}: {e}")
            return None

    def count_models(self) -> int:
        """
        Count the total number of models in the registry.

        Returns:
            int: Total number of models
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {self.schema}.models
                """
                )
                return cur.fetchone()[0]

    def find_model(self, model_id: str) -> Optional[Model]:
        """
        Find a model in the registry by its ID.

        Args:
            model_id: ID of the model to find

        Returns:
            Model object with its sources and fingerprints, or None if not found
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 
                        m.id as model_id,
                        m.model_maker,
                        m.model_name,
                        m.params_count,
                        m.context_length,
                        m.quantization,
                        m.license,
                        m.created_at,
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'source_id', s.id,
                                    'source_type', s.source_type,
                                    'source_identifier', s.source_identifier,
                                    'requires_auth', s.requires_auth,
                                    'created_at', s.created_at
                                )
                            )
                            FROM {self.schema}.model_sources s
                            WHERE s.model_id = m.id
                        ) as sources,
                        m.last_updated
                    FROM {self.schema}.models m
                    WHERE m.id = %s
                """,
                    (model_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                # Construct model dictionary from row data
                model_dict = {
                    "model_id": row[0],
                    "model_maker": row[1],
                    "model_name": row[2],
                    "params_count": row[3],
                    "context_length": row[4],
                    "quantization": row[5],
                    "license": row[6],
                    "created_at": row[7],
                    "sources": row[8] if row[8] else [],
                    "last_updated": row[9],
                }

                # Instantiate Model correctly using name and model_info
                return Model(name=model_dict["model_name"], model_info=model_dict)

    def find_models(
        self,
        filters: Optional[ModelFilterCriteria] = None,
    ) -> List[Model]:
        """
        Find models in the registry that match the given criteria.

        Args:
            filters: ModelFilterCriteria object with filter conditions.

        Returns:
            List of Model objects with their sources and fingerprints
        """
        with self._get_connection() as conn:
            logger.debug("Finding models by criteria")
            with conn.cursor() as cur:
                # Build the query
                query = f"""
                    SELECT 
                        m.id as model_id,
                        m.model_maker,
                        m.model_name,
                        m.params_count,
                        m.context_length,
                        m.quantization,
                        m.license,
                        m.created_at,
                        m.last_updated,
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'source_id', s.id,
                                    'source_type', s.source_type,
                                    'source_identifier', s.source_identifier,
                                    'requires_auth', s.requires_auth,
                                    'created_at', s.created_at,
                                    'last_updated', s.last_updated
                                )
                            )
                            FROM {self.schema}.model_sources s
                            WHERE s.model_id = m.id
                        ) as sources
                    FROM {self.schema}.models m
                    WHERE 1=1
                """
                params = []

                # Add filters if provided
                if filters and not filters.is_empty():
                    filter_conditions, filter_params = filters.to_sql_filters(table_alias='m', placeholder_style='%s')
                    logger.debug(f"Filter conditions: {filter_conditions}")
                    logger.debug(f"Filter params: {filter_params}")
                    # Add last_updated filter if provided
                    query += f" AND {filter_conditions}"
                    params.extend(filter_params)

                query += " GROUP BY m.id, m.model_maker, m.model_name, m.params_count, m.context_length, m.quantization, m.license, m.created_at, m.last_updated"

                cur.execute(query, params)
                rows = cur.fetchall()

                # Convert rows to Model objects
                models = []
                for row in rows:
                    model_dict = {
                        "model_id": row[0],
                        "model_maker": row[1],
                        "model_name": row[2],
                        "params_count": row[3],
                        "context_length": row[4],
                        "quantization": row[5],
                        "license": row[6],
                        "created_at": row[7],
                        "last_updated": row[8],
                        "sources": row[9] if row[9] else [],
                    }

                    # Create a Model object
                    model = Model(name=model_dict["model_name"], model_info=model_dict)
                    models.append(model)

                return models

    # ============= Model Management Methods =============

    def copy_model_to_production(
        self, model_id: str, override_checks: bool = False
    ) -> Optional[str]:
        """
        Copy a model from dev to production database.

        Args:
            model_id: ID of the model in dev schema
            override_checks: Whether to override validation checks

        Returns:
            str: ID of the copied model in production, or None if checks failed
        """
        # First get model and source info from dev
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        m.model_maker,
                        m.model_name,
                        m.params_count,
                        m.context_length,
                        m.quantization,
                        m.license,
                        m.created_at
                    FROM dev.models m
                    WHERE m.id = %s
                """,
                    (model_id,),
                )

                model_data = cur.fetchone()
                if not model_data:
                    logger.error(f"Model with ID {model_id} not found in dev schema")
                    return None

                # Get source info
                cur.execute(
                    """
                    SELECT 
                        s.source_type,
                        s.source_identifier,
                        s.requires_auth,
                        s.created_at
                    FROM dev.model_sources s
                    WHERE s.model_id = %s
                """,
                    (model_id,),
                )

                source_data = cur.fetchone()

        # Create prod registry interface
        prod_registry = RegistryInterface(self.connection_string, use_production=True)

        # Create model info dict
        model_info = {
            "model_maker": model_data[0],
            "model_name": model_data[1],
            "params_count": model_data[2],
            "context_length": model_data[3],
            "quantization": model_data[4],
            "license": model_data[5],
            "created_at": model_data[6],
        }

        # Add model to production
        prod_model_id = prod_registry.add_model(
            model_info, override_checks=override_checks
        )
        if not prod_model_id:
            return None

        # Add source info
        if source_data:
            source_info = {
                "source_identifier": source_data[1],
                "requires_auth": source_data[2],
                "created_at": source_data[3],
            }

            prod_registry.add_model_source(
                model_id=prod_model_id,
                source_type=source_data[0],
                source_info=source_info,
                override_checks=override_checks,
            )

        return prod_model_id

    def copy_fingerprint_to_production(
        self,
        model_id: str,
        fingerprint_type: str,
        prod_model_id: str,
        override_checks: bool = False,
    ) -> Optional[str]:
        """
        Copy a fingerprint from dev to production database.

        Args:
            model_id: ID of the model in dev schema
            fingerprint_type: Type of fingerprint to copy
            prod_model_id: ID of the model in production schema
            override_checks: Whether to override validation checks

        Returns:
            str: ID of the copied fingerprint in production, or None if checks failed
        """
        # Get fingerprint data from dev
        fingerprint_data = self.get_fingerprint(model_id, fingerprint_type)
        if fingerprint_data is None:
            logger.error(
                f"Fingerprint of type {fingerprint_type} for model {model_id} not found in dev schema"
            )
            return None

        # Get fingerprint config
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fingerprint_config
                    FROM dev.fingerprints
                    WHERE model_id = %s AND fingerprint_type = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (model_id, fingerprint_type),
                )

                config_data = cur.fetchone()
                if not config_data:
                    logger.error(
                        f"Fingerprint config for model {model_id} and type {fingerprint_type} not found in dev schema"
                    )
                    return None

                fingerprint_config = config_data[0]

        # Create prod registry interface
        prod_registry = RegistryInterface(self.connection_string, use_production=True)

        # Register fingerprint in production
        return prod_registry.register_fingerprint(
            model_id=prod_model_id,
            fingerprint_type=fingerprint_type,
            fingerprint_vector=fingerprint_data,
            fingerprint_config=fingerprint_config,
            override_checks=override_checks,
        )

    def check_duplicate_fingerprints_in_prod(self) -> List[Dict]:
        """
        Check for duplicate fingerprints in the production database.

        Returns:
            List of dictionaries with duplicate fingerprint information
        """
        if self.schema != "prod":
            # Create prod registry interface
            prod_registry = RegistryInterface(
                self.connection_string, use_production=True
            )
            return prod_registry.check_duplicate_fingerprints_in_prod()

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Find duplicate fingerprint vectors
                cur.execute("""
                    SELECT 
                        f1.fingerprint_vector,
                        array_agg(f1.id) as fingerprint_ids,
                        array_agg(f1.model_id) as model_ids
                    FROM prod.fingerprints f1
                    JOIN prod.fingerprints f2 ON 
                        f1.fingerprint_vector::text = f2.fingerprint_vector::text AND 
                        f1.id < f2.id
                    GROUP BY f1.fingerprint_vector
                """)

                duplicates = []
                for row in cur.fetchall():
                    duplicates.append(
                        {
                            "fingerprint_ids": row[1],
                            "model_ids": row[2],
                            "duplicate_type": "identical_vector",
                        }
                    )

                return duplicates

    def check_multiple_fingerprints_per_model_in_prod(self) -> List[Dict]:
        """
        Check for multiple fingerprints for the same model_id and fingerprint_type in production.

        Returns:
            List of dictionaries with information about models that have multiple fingerprints
        """
        if self.schema != "prod":
            # Create prod registry interface
            prod_registry = RegistryInterface(
                self.connection_string, use_production=True
            )
            return prod_registry.check_multiple_fingerprints_per_model_in_prod()

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Find models with multiple fingerprints of the same type
                cur.execute("""
                    SELECT 
                        model_id,
                        fingerprint_type,
                        COUNT(*) as fingerprint_count,
                        array_agg(id) as fingerprint_ids
                    FROM prod.fingerprints
                    GROUP BY model_id, fingerprint_type
                    HAVING COUNT(*) > 1
                """)

                multiples = []
                for row in cur.fetchall():
                    multiples.append(
                        {
                            "model_id": row[0],
                            "fingerprint_type": row[1],
                            "fingerprint_count": row[2],
                            "fingerprint_ids": row[3],
                        }
                    )

                return multiples
