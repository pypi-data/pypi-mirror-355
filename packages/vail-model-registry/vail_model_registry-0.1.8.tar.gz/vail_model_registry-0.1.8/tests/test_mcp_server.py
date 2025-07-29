import os

import numpy as np
import pytest

import vail.vail_mcp.server as mcp_server_module
from vail.registry import RegistryInterface
from vail.registry.local_interface import LocalRegistryInterface
from vail.utils.env import load_env
from vail.vail_mcp import (
    add_model,
    compare_fp_pairs,
    compute_fingerprint_similarity,
    generate_fingerprint,
    get_fingerprint_vectors,
    get_hardware_profile,
    get_model_template,
    list_models,
)

# Load test environment variables
load_env("test")


def get_connection_string():
    return os.getenv("DATABASE_URL")


@pytest.fixture()
def local_registry(tmp_path):
    connection_string = get_connection_string()
    if not connection_string:
        pytest.skip("DATABASE_URL environment variable not set in .env.test")
    if "test" not in connection_string:
        raise ValueError(
            "DATABASE_URL must include 'test' to prevent accidental modifications to production database"
        )
    return LocalRegistryInterface(
        connection_string=connection_string, local_db_path=str(tmp_path / "test.duckdb")
    )


@pytest.fixture
def global_registry():
    """Create a RegistryInterface instance for testing (PostgreSQL global test DB)."""
    connection_string = get_connection_string()
    if not connection_string:
        pytest.skip("DATABASE_URL environment variable not set in .env.test")
    if "test" not in connection_string:
        raise ValueError(
            "DATABASE_URL must include 'test' to prevent accidental modifications to production database"
        )
    
    # Ensure the test database schema is set up
    RegistryInterface.setup_global_registry(connection_string)

    return RegistryInterface(connection_string)


@pytest.fixture
def prime_mcp_with_global_test_registry(global_registry):
    """Sets the MCP server's global REGISTRY to the global PostgreSQL test DB."""
    original_server_registry = mcp_server_module.REGISTRY
    mcp_server_module.REGISTRY = (
        global_registry  # registry is the global PostgreSQL test DB
    )
    yield
    mcp_server_module.REGISTRY = (
        original_server_registry  # Or None for stricter isolation
    )


@pytest.fixture
def prime_mcp_with_local_test_registry(local_registry):
    """Sets the MCP server's global REGISTRY to a local DuckDB instance, synced from global."""
    # Populate the local registry from the global test database
    # (which is populated by the autouse setup_database fixture via the 'registry' fixture)
    sync_result = local_registry.sync_models_from_global(use_last_sync_time=False)
    if sync_result is None or sync_result[0] == 0:
        # Optionally, skip or fail if no models could be synced, as tests might rely on this data.
        # For now, we'll proceed, but tests should be aware.
        raise ValueError(
            "Error: No models were synced to the local registry during prime_mcp_with_local_test_registry."
        )

    original_server_registry = mcp_server_module.REGISTRY
    mcp_server_module.REGISTRY = local_registry
    yield
    mcp_server_module.REGISTRY = original_server_registry  # Or None


NEW_MODEL_SAMPLE_INFO = {
    "model_name": "Athene-v2",
    "model_maker": "Nexusflow.ai",
    "quantization": "bf16",
    "context_length": 32768,
    "params_count": 72000000000,
    "source_type": "huggingface_api",
    "source_identifier": '{"loader_class":"AutoModelForCausalLM", "checkpoint":"Nexusflow\/Athene-V2-Chat"}',
    "license_type": "Nexusflow.ai License Terms for Personal Use",
    "link": "https:\/\/huggingface.co\/Nexusflow\/Athene-V2-Chat",
    "requires_auth": False,
    "human_verified": "X",
    "comment": "Have updated to HF page for link",
}


@pytest.fixture(autouse=True)
def setup_database(
    global_registry, sample_model_info, sample_source_info, sample_fingerprint_info
):
    """Set up the database with sample data before each test."""
    # Clean up any existing data
    with global_registry._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fingerprints")
            cur.execute("DELETE FROM model_sources")
            cur.execute("DELETE FROM models")
            cur.execute("DELETE FROM hardware_info")
            conn.commit()

    # Add sample models, sources, and fingerprints
    model_ids = []
    source_ids = []

    # First add models and sources to get their IDs
    for model_info, source_info in zip(sample_model_info, sample_source_info):
        print(f"Adding model: {model_info['model_name']}")
        model_id = global_registry.add_model(model_info)
        model_ids.append(model_id)

        source_id = global_registry.add_model_source(
            model_id, source_info["source_type"], source_info
        )
        source_ids.append(source_id)

    # Then add fingerprints using registry method
    for model_id, fingerprint_info in zip(model_ids, sample_fingerprint_info):
        print(f"Adding fingerprint for model_id: {model_id}")
        fingerprint_type = fingerprint_info["fingerprint_type"]
        fingerprint_vector = np.array(fingerprint_info["fingerprint_vector"])
        fingerprint_config = fingerprint_info["fingerprint_config"]

        try:
            fingerprint_id = global_registry.register_fingerprint(
                model_id=model_id,
                fingerprint_type=fingerprint_type,
                fingerprint_vector=fingerprint_vector,
                fingerprint_config=fingerprint_config,
            )
            print(f"Added fingerprint {fingerprint_id} for model {model_id}")
        except Exception as e:
            print(f"Error adding fingerprint for model {model_id}: {e}")

    yield  # Run the test

    # Cleanup is handled by the cleanup_database fixture

@pytest.fixture(autouse=True)
def cleanup_database(global_registry):
    """Clean up the database after each test."""
    yield  # Run the test
    # After test completes, clean up
    with global_registry._get_connection() as conn:
        with conn.cursor() as cur:
            # Delete in correct order to respect foreign key constraints
            cur.execute("DELETE FROM fingerprints")
            cur.execute("DELETE FROM model_sources")
            cur.execute("DELETE FROM models")
            cur.execute("DELETE FROM hardware_info")
            conn.commit()

@pytest.fixture
def sample_model_info():
    """Create sample model information for testing."""
    return [
        {
            "model_name": "Phi-4",
            "model_maker": "Microsoft",
            "quantization": "bf16",
            "context_length": 16384,
            "params_count": 14000000000,
        },
        {
            "model_name": "Phi-3 Mini",
            "model_maker": "Microsoft",
            "quantization": "bf16",
            "context_length": 4096,
            "params_count": 3800000000,
        },
        {
            "model_name": "t5_v1_1-small_conditional_generation",
            "model_maker": "google",
            "quantization": "",
            "context_length": 1024,
            "params_count": 60000000,
        },
        {
            "model_name": "Airoboros-70B-3.3",
            "model_maker": "jondurbin",
            "quantization": "bf16",
            "params_count": 70000000000,
        },
    ]


@pytest.fixture
def sample_source_info():
    """Create sample source information for testing."""
    return [
        {
            "source_type": "huggingface_api",
            "source_identifier": '{"loader_class":"AutoModelForCausalLM", "checkpoint":"microsoft/phi-4"}',
            "license": "MIT",
            "link": "https://huggingface.co/microsoft/phi-4",
            "human_verified": "X",
            "requires_auth": False,
            "comment": "",
        },
        {
            "source_type": "huggingface_api",
            "source_identifier": '{"loader_class":"AutoModelForCausalLM", "checkpoint":"microsoft/Phi-3-mini-4k-instruct"}',
            "license": "MIT",
            "link": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct",
            "human_verified": "X",
            "comment": "",
        },
        {
            "source_type": "huggingface_api",
            "source_identifier": '{"loader_class":"T5ForConditionalGeneration","checkpoint":"google/t5-v1_1-small"}',
            "license": "Apache 2.0",
            "link": "https://huggingface.co/google/t5-v1_1-small",
            "human_verified": "X",
            "requires_auth": False,
            "comment": "",
        },
        {
            "source_type": "huggingface_api",
            "source_identifier": '{"loader_class":"AutoModelForCausalLM", "checkpoint":"jondurbin/airoboros-70b-3.3"}',
            "license": "Llama 3",
            "link": "https://huggingface.co/jondurbin/airoboros-70b-3.3",
            "human_verified": "X",
            "requires_auth": False,
            "comment": "",
        },
    ]


@pytest.fixture
def sample_fingerprint_info():
    """Create sample fingerprint information for testing."""
    return [
        {
            "fingerprint_type": "input_output",
            "fingerprint_vector": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "fingerprint_config": {
                "method_name": "input_output_linear_approximation",
                "method_type": "input_output",
                "n0": 10,
            },
        },
        {
            "fingerprint_type": "input_output",
            "fingerprint_vector": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1],
            "fingerprint_config": {
                "method_name": "input_output_linear_approximation",
                "method_type": "input_output",
                "n0": 10,
            },
        },
        {
            "fingerprint_type": "input_output",
            "fingerprint_vector": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
            "fingerprint_config": {
                "method_name": "input_output_linear_approximation",
                "method_type": "input_output",
                "n0": 10,
            },
        },
        {
            "fingerprint_type": "input_output",
            "fingerprint_vector": [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
            "fingerprint_config": {
                "method_name": "input_output_linear_approximation",
                "method_type": "input_output",
                "n0": 10,
            },
        },
    ]


################################################################################
### Test MCP tools, some with Local and Global, some with Global only
################################################################################


@pytest.mark.parametrize(
    "registry_fixture",
    ["prime_mcp_with_global_test_registry", "prime_mcp_with_local_test_registry"],
)
@pytest.mark.usefixtures("registry_fixture")
def test_list_models(registry_fixture):
    response = list_models()
    assert "models" in response
    assert "total" in response
    assert "offset" in response
    assert "limit" in response
    assert len(response["models"]) > 0
    assert "Phi-4" in [model.model_name for model in response["models"]]


def test_get_model_template():
    # Test without source type
    response = get_model_template()
    assert "model_info_template" in response
    assert "examples" in response

    # Test with source type
    response = get_model_template(source_type="huggingface_api")
    assert "source_info_template" in response


@pytest.mark.usefixtures("prime_mcp_with_global_test_registry")
def test_add_model():
    response = add_model(
        model_info=NEW_MODEL_SAMPLE_INFO, source_info=NEW_MODEL_SAMPLE_INFO
    )
    assert "model_id" in response
    assert "source_id" in response
    assert "message" in response


@pytest.mark.parametrize(
    "registry_fixture",
    ["prime_mcp_with_global_test_registry", "prime_mcp_with_local_test_registry"],
)
@pytest.mark.usefixtures("registry_fixture")
def test_get_fingerprint_vectors(registry_fixture):
    """Test retrieving fingerprint vectors."""
    # Get model IDs from the populated registry
    models_response = list_models(limit=2)
    model_ids = [model.model_id for model in models_response["models"]]

    if not model_ids:
        pytest.skip("No models found in the registry to test fingerprint retrieval.")

    response = get_fingerprint_vectors(model_ids=model_ids)
    assert isinstance(response, dict)
    assert "results" in response

    results = response["results"]
    assert isinstance(results, list)
    assert len(results) > 0

    # At least one fingerprint should be successful
    success_count = 0
    for result in results:
        assert "model_id" in result
        assert "status" in result
        if result["status"] == "success":
            assert "fingerprint_vector" in result
            assert isinstance(result["fingerprint_vector"], list)
            success_count += 1
        else:
            assert "error" in result

    assert success_count > 0, (
        "Expected at least one fingerprint to be retrieved successfully"
    )


@pytest.mark.parametrize(
    "registry_fixture",
    ["prime_mcp_with_global_test_registry", "prime_mcp_with_local_test_registry"],
)
@pytest.mark.usefixtures("registry_fixture")
def test_generate_fingerprint(registry_fixture, request):
    """Test generating a fingerprint."""
    # Specifically target the t5 model since it's smaller and faster to process
    target_model_name = "t5_v1_1-small_conditional_generation"

    # Get the appropriate registry based on fixture
    registry = mcp_server_module.get_registry()

    # Find the specific model by name
    models = registry.find_models()
    target_model = None
    for model in models:
        # Using the model.name property which is directly accessible
        if model.name == target_model_name:
            target_model = model
            break

    if not target_model:
        pytest.skip(f"Model {target_model_name} not found in the registry.")

    model_id = target_model.model_info["model_id"]

    sources = target_model.model_info["sources"]
    if not sources:
        pytest.skip(f"No sources found for model_id {model_id}.")

    source_id = sources[0]["source_id"]
    fingerprint_type = "input_output"  # Example type

    # Note: Actual generation might fail in test env depending on dependencies
    response = generate_fingerprint(
        source_id=source_id, fingerprint_type=fingerprint_type, override=True
    )

    # Assert that status is "success"
    assert "status" in response
    assert response["status"] == "success"

    # Verify that fingerprint data is returned
    assert isinstance(response["fingerprint_config"], dict)

    # For global registry, check fingerprint_id is returned
    if registry.registry_type != "local":
        assert response["fingerprint_id"] is not None
    # For local registry, fingerprint_id should be None
    else:
        assert response["fingerprint_id"] is None


def test_compare_fp_pairs():
    """Test comparing fingerprint pairs (using dummy data)."""
    dummy_vector = [0.1] * 10  # Example vector
    response = compare_fp_pairs(
        vector_ref1=dummy_vector,
        vector_var1=dummy_vector,
        vector_ref2=dummy_vector,
        vector_var2=dummy_vector,
        family1_name="FamilyA",
        family2_name="FamilyB",
        model_name_ref1="ModelA_ref",
        model_name_var1="ModelA_var",
        model_name_ref2="ModelB_ref",
        model_name_var2="ModelB_var",
    )
    assert "status" in response
    assert response["status"] == "success"
    assert "visualization_path" in response
    assert response["visualization_path"].endswith(".png")
    assert os.path.exists(response["visualization_path"])
    os.remove(response["visualization_path"])  # Clean up the generated file


def test_compute_fingerprint_similarity():
    """Test the compute_fingerprint_similarity MCP tool."""
    vec1 = [0.1, 0.2, 0.7]
    vec2 = [0.1, 0.3, 0.6]  # Slightly different

    # Expected L1 similarity: 1 - 0.5 * sum(|v1-v2|) = 1 - 0.5 * (|0.1-0.1| + |0.2-0.3| + |0.7-0.6|)
    # = 1 - 0.5 * (0 + 0.1 + 0.1) = 1 - 0.5 * 0.2 = 1 - 0.1 = 0.9
    expected_similarity = 0.9

    response = compute_fingerprint_similarity(vector1=vec1, vector2=vec2)

    assert response["status"] == "success"
    assert response["similarity_method"] == "l1"
    assert np.isclose(response["similarity"], expected_similarity)


@pytest.mark.usefixtures("prime_mcp_with_global_test_registry")
def test_add_model_invalid_data():
    # Test with invalid model info
    with pytest.raises(ValueError) as exc_info:
        add_model(model_info={"invalid": "data"}, source_info=NEW_MODEL_SAMPLE_INFO)
    assert "Failed to add model" in str(exc_info.value)

    # Test with invalid source info
    with pytest.raises(ValueError) as exc_info:
        add_model(model_info=NEW_MODEL_SAMPLE_INFO, source_info={"invalid": "data"})
    assert "Failed to add model" in str(exc_info.value)


@pytest.mark.usefixtures("prime_mcp_with_local_test_registry")
def test_get_hardware_profile():
    response = get_hardware_profile()
    assert "cpu" in response
    assert "memory" in response
    assert "gpu" in response
    assert "disk" in response
    assert "system" in response
    assert "last_updated" in response
