"""
Test module for the models module.
"""

import traceback
from datetime import datetime, timedelta

import pytest

from vail.registry import Model as RegistryModel
from vail.registry.models import ModelFilterCriteria
from vail.utils.env import load_env

# Load test environment variables
load_env("test")


@pytest.fixture
def valid_huggingface_source():
    return {
        "source_type": "huggingface_api",
        "requires_auth": False,
        "source_identifier": '{"loader_class": "AutoModelForCausalLM", "checkpoint": "deepcogito/cogito-v1-preview-llama-3B"}',
    }


@pytest.fixture
def valid_onnx_source():
    return {
        "source_type": "onnx_file",
        "source_identifier": {"file_path": "path/to/model.onnx"},
        "requires_auth": False,
    }


@pytest.fixture
def invalid_source():
    return {
        "source_type": "invalid_type",
        "source_identifier": {},
        "requires_auth": False,
    }


def test_validate_source_huggingface(valid_huggingface_source):
    """Test validate_source with a valid Hugging Face source"""
    try:
        assert RegistryModel.validate_source(valid_huggingface_source) is True
    except Exception:
        print("\nError in test_validate_source_huggingface:")
        print(traceback.format_exc())
        raise


def test_validate_source_onnx(valid_onnx_source):
    """Test validate_source with a valid ONNX source"""
    try:
        assert RegistryModel.validate_source(valid_onnx_source) is True
    except Exception:
        print("\nError in test_validate_source_onnx:")
        print(traceback.format_exc())
        raise


def test_validate_source_invalid(invalid_source):
    """Test validate_source with an invalid source type"""
    try:
        assert RegistryModel.validate_source(invalid_source) is False
    except Exception:
        print("\nError in test_validate_source_invalid:")
        print(traceback.format_exc())
        raise


def test_validate_source_missing_required_fields():
    """Test validate_source with missing required fields"""
    try:
        invalid_source = {
            "source_type": "huggingface_api",
            "source_identifier": {},  # Missing required fields
        }
        assert RegistryModel.validate_source(invalid_source) is False
    except Exception:
        print("\nError in test_validate_source_missing_required_fields:")
        print(traceback.format_exc())
        raise


def test_validate_source_missing_source_type():
    """Test validate_source with missing source_type"""
    try:
        invalid_source = {
            "source_identifier": {
                "loader_class": "AutoModelForCausalLM",
                "checkpoint": "mistralai/Mistral-7B-v0.1",
            }
        }
        assert RegistryModel.validate_source(invalid_source) is False
    except Exception:
        print("\nError in test_validate_source_missing_source_type:")
        print(traceback.format_exc())
        raise


def test_validate_source_missing_source_identifier():
    """Test validate_source with missing source_identifier"""
    try:
        invalid_source = {"source_type": "huggingface_api"}
        assert RegistryModel.validate_source(invalid_source) is False
    except Exception:
        print("\nError in test_validate_source_missing_source_identifier:")
        print(traceback.format_exc())
        raise


def test_validate_source_with_auth_required():
    """Test validate_source with authentication required"""
    try:
        source_with_auth = {
            "source_type": "huggingface_api",
            "source_identifier": {
                "loader_class": "AutoModelForCausalLM",
                "checkpoint": "microsoft/Phi-3-mini-4k-instruct",
            },
            "requires_auth": True,
        }

        assert RegistryModel.validate_source(source_with_auth) is True
    except Exception:
        print("\nError in test_validate_source_with_auth_required:")
        print(traceback.format_exc())
        raise


def test_model_filter_criteria():
    """Test ModelFilterCriteria dataclass"""
    criteria = ModelFilterCriteria(
        maker="Mistral",
        params_count_eq=1000000,
        quantization="8-bit",
        updated_since=datetime.now() - timedelta(days=1),
    )

    assert criteria.maker == "Mistral"
    assert criteria.params_count_eq == 1000000


def test_model_filter_criteria_to_sql_filters():
    """Test ModelFilterCriteria to_sql_filters method for different styles and aliases."""
    now = datetime.now()
    criteria_full = ModelFilterCriteria(
        maker="Mistral",
        params_count_eq=1000000,
        params_count_gt=500000,
        params_count_lte=2000000,
        quantization="8-bit",
        updated_since=now,
    )

    # Test case 1: DuckDB style ('?') without alias
    where_clause, params = criteria_full.to_sql_filters(placeholder_style="?")
    expected_where_duckdb = (
        "model_maker = ? AND "
        "params_count = ? AND params_count > ? AND params_count <= ? AND "
        "quantization = ? AND last_updated >= ?"
    )
    assert where_clause == expected_where_duckdb
    assert params == ["Mistral", 1000000, 500000, 2000000, "8-bit", now]

    # Test case 2: PostgreSQL style ('%s') without alias
    where_clause, params = criteria_full.to_sql_filters(placeholder_style="%s")
    expected_where_postgres = (
        "model_maker = %s AND "
        "params_count = %s AND params_count > %s AND params_count <= %s AND "
        "quantization = %s AND last_updated >= %s"
    )
    assert where_clause == expected_where_postgres
    assert params == ["Mistral", 1000000, 500000, 2000000, "8-bit", now]

    # Test case 3: DuckDB style ('?') with alias 'm'
    where_clause, params = criteria_full.to_sql_filters(
        table_alias="m", placeholder_style="?"
    )
    expected_where_duckdb_alias = (
        "m.model_maker = ? AND "
        "m.params_count = ? AND m.params_count > ? AND m.params_count <= ? AND "
        "m.quantization = ? AND m.last_updated >= ?"
    )
    assert where_clause == expected_where_duckdb_alias
    assert params == ["Mistral", 1000000, 500000, 2000000, "8-bit", now]

    # Test case 4: PostgreSQL style ('%s') with alias 'm'
    where_clause, params = criteria_full.to_sql_filters(
        table_alias="m", placeholder_style="%s"
    )
    expected_where_postgres_alias = (
        "m.model_maker = %s AND "
        "m.params_count = %s AND m.params_count > %s AND m.params_count <= %s AND "
        "m.quantization = %s AND m.last_updated >= %s"
    )
    assert where_clause == expected_where_postgres_alias
    assert params == ["Mistral", 1000000, 500000, 2000000, "8-bit", now]

    # Test case 5: No filters set
    criteria_empty = ModelFilterCriteria()
    where_clause, params = criteria_empty.to_sql_filters()
    assert where_clause == "1=1"
    assert params == []

    # Test case 6: Single filter (maker)
    criteria_single = ModelFilterCriteria(maker="TestMaker")
    where_clause, params = criteria_single.to_sql_filters(
        table_alias="x", placeholder_style="%s"
    )
    assert where_clause == "x.model_maker = %s"
    assert params == ["TestMaker"]

    # Test case 7: Single filter (params_count_eq), default placeholder
    criteria_single_params = ModelFilterCriteria(params_count_eq=500)
    where_clause, params = criteria_single_params.to_sql_filters()
    assert where_clause == "params_count = ?"
    assert params == [500]

    # Test case 8: Single filter (params_count_gt)
    criteria_gt = ModelFilterCriteria(params_count_gt=1000)
    where_clause, params = criteria_gt.to_sql_filters(
        table_alias="t", placeholder_style="%s"
    )
    assert where_clause == "t.params_count > %s"
    assert params == [1000]

    # Test case 9: Single filter (params_count_lte)
    criteria_lte = ModelFilterCriteria(params_count_lte=2000)
    where_clause, params = criteria_lte.to_sql_filters(placeholder_style="?")
    assert where_clause == "params_count <= ?"
    assert params == [2000]
