#!/usr/bin/env python
"""
FastMCP Server Implementation for the Model Registry

This module implements a FastMCP server that exposes the model registry functionality.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from fastapi import HTTPException
from fastmcp import Context, FastMCP
from pydantic import BaseModel

from vail.fingerprint.metrics import l1_similarity
from vail.registry import Model, RegistryInterface
from vail.registry.local_interface import LocalRegistryInterface
from vail.registry.models import ModelFilterCriteria
from vail.utils import HardwareInfo
from vail.utils.env import load_env
from vail.vail_mcp.resources import (
    compare_fp_pairs_impl,
    generate_fingerprint_impl,
    get_fingerprint_vectors_impl,
)
from vail.vail_mcp.validation import (
    validate_model_info,
    validate_model_source,
    validate_source_info,
)

# =============================================
# Initialize Environment
# =============================================

# Registry will be initialized when needed
REGISTRY = None


def get_registry(
    registry_type: str = "global", local_db_path: str = "local_registry.duckdb"
):
    """Get the registry instance, initializing it if necessary."""
    global REGISTRY
    if REGISTRY is None:
        load_env()
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set.")

        if registry_type == "local":
            REGISTRY = LocalRegistryInterface(
                connection_string=db_url, local_db_path=local_db_path
            )
        elif registry_type == "global":
            REGISTRY = RegistryInterface(db_url)
        else:
            raise ValueError(
                f"Invalid registry_type: {registry_type}. Must be 'local' or 'global'."
            )
    return REGISTRY


# Initialize FastMCP server
mcp_server = FastMCP(
    "VAIL Model Registry MCP Server",
    description="Simple interface for LLMs to interact with the model registry",
    version="1.0.0",
    tools=[
        {
            "name": "list_models",
            "description": "List all models available in the registry.",
            "parameters": {
                "maker": {
                    "type": "string",
                    "description": "Filter by model maker (empty string for no filter)",
                    "required": False,
                    "default": "",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of models to return",
                    "required": False,
                    "default": 10,
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of models to skip",
                    "required": False,
                    "default": 0,
                },
            },
        },
        {
            "name": "get_hardware_profile",
            "description": "Get the current hardware profile of the machine.",
            "parameters": {},
        },
        {
            "name": "get_model_template",
            "description": "Get a template with examples showing the required format and fields for adding a model to the registry.",
            "parameters": {
                "source_type": {
                    "type": "string",
                    "description": "Optional - get template specific to a source type (huggingface_api, onnx, or gguf)",
                    "required": False,
                    "enum": ["huggingface_api", "onnx", "gguf"],
                }
            },
        },
        {
            "name": "add_model",
            "description": "Add a new model to the registry with source information.",
            "parameters": {
                "model_info": {
                    "type": "object",
                    "description": "Information about the model",
                    "required": True,
                    "properties": {
                        "model_maker": {
                            "type": "string",
                            "description": "Organization or individual that created the model",
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Unique name of the model",
                        },
                        "params_count": {
                            "type": "integer",
                            "description": "Number of parameters in the model, formatted as a number without commas",
                        },
                        "context_length": {
                            "type": "integer",
                            "description": "Maximum sequence length the model can handle, formatted as a number without commas",
                        },
                        "link": {
                            "type": "string",
                            "description": "URL to the model's documentation or card",
                        },
                        "license_type": {
                            "type": "string",
                            "description": "Type of license the model is released under",
                        },
                        "quantization": {
                            "type": "string",
                            "description": "Quantization format (e.g. FP32, FP16, INT8)",
                            "required": True,
                        },
                    },
                },
                "source_info": {
                    "type": "object",
                    "description": "Information about the model source",
                    "required": True,
                    "properties": {
                        "source_type": {
                            "type": "string",
                            "description": "Type of source - must be one of: huggingface_api, onnx, or gguf",
                            "enum": ["huggingface_api", "onnx", "gguf"],
                        },
                        "source_identifier": {
                            "type": "string",
                            "description": 'JSON-serialized string containing source-specific information. For huggingface_api sources, must include \'loader_class\' and \'checkpoint\' fields, e.g.: \'{"loader_class":"AutoModelForCausalLM", "checkpoint":"Nexusflow/Athene-V2-Chat"}\'',
                            "examples": [
                                '{"loader_class":"AutoModelForCausalLM", "checkpoint":"Nexusflow/Athene-V2-Chat"}'
                            ],
                        },
                        "requires_auth": {
                            "type": "boolean",
                            "description": "Whether authentication is required",
                            "default": False,
                        },
                    },
                },
            },
        },
        {
            "name": "get_fingerprint_vectors",
            "description": "Get the fingerprint vector for a specific fingerprint type for multiple models.",
            "parameters": {
                "model_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of model IDs.",
                    "required": True,
                },
                "fingerprint_type": {
                    "type": "string",
                    "description": "The type of fingerprint (e.g., 'input_output', 'weight', 'architecture') to retrieve for all specified model IDs.",
                    "required": True,
                },
            },
        },
        {
            "name": "generate_fingerprint",
            "description": "Generates a specified type of fingerprint for a model identified by its source ID. Avoids regeneration if a fingerprint of that type already exists, unless overridden.",
            "parameters": {
                "source_id": {
                    "type": "string",
                    "description": "ID of the specific model source entry to fingerprint.",
                    "required": True,
                },
                "fingerprint_type": {
                    "type": "string",
                    "description": "The type of fingerprint to generate (e.g., 'input_output', 'weight', 'architecture').",
                    "required": True,
                },
                "override": {
                    "type": "boolean",
                    "description": "If True, generate a new fingerprint even if one of the specified type already exists for this model.",
                    "required": False,
                    "default": False,
                },
                "use_remote": {
                    "type": "boolean",
                    "description": "Whether to use remote execution via Beam (True) or local execution (False).",
                    "required": False,
                    "default": True,
                },
            },
        },
        {
            "name": "compare_fp_pairs",
            "description": "Generates a fingerprint visualization comparing two pairs of fingerprint vectors (reference vs variant).",
            "parameters": {
                "vector_ref1": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Fingerprint vector of the first reference model.",
                    "required": True,
                },
                "vector_var1": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Fingerprint vector of the first variant model.",
                    "required": True,
                },
                "vector_ref2": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Fingerprint vector of the second reference model.",
                    "required": True,
                },
                "vector_var2": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Fingerprint vector of the second variant model.",
                    "required": True,
                },
                "family1_name": {
                    "type": "string",
                    "description": "Name for the first pair/family of models.",
                    "required": True,
                },
                "family2_name": {
                    "type": "string",
                    "description": "Name for the second pair/family of models.",
                    "required": True,
                },
                "model_name_ref1": {
                    "type": "string",
                    "description": "Name of the first reference model.",
                    "required": True,
                },
                "model_name_var1": {
                    "type": "string",
                    "description": "Name of the first variant model.",
                    "required": True,
                },
                "model_name_ref2": {
                    "type": "string",
                    "description": "Name of the second reference model.",
                    "required": True,
                },
                "model_name_var2": {
                    "type": "string",
                    "description": "Name of the second variant model.",
                    "required": True,
                },
            },
        },
        {
            "name": "compute_fingerprint_similarity",
            "description": "Directly compares two fingerprint vectors using l1_similarity from the VAIL metrics.",
            "parameters": {
                "vector1": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "First fingerprint vector",
                    "required": True,
                },
                "vector2": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Second fingerprint vector",
                    "required": True,
                },
            },
        },
    ],
)


# =============================================
# Pydantic Model Definitions
# =============================================


class ModelSource(BaseModel):
    source_id: int
    source_type: str
    source_identifier: dict
    requires_auth: Optional[bool]
    created_at: Optional[datetime]


class ModelResponse(BaseModel):
    model_id: int
    model_maker: str
    model_name: str
    params_count: int
    context_length: Optional[int]
    quantization: str
    created_at: Optional[datetime]
    sources: List[ModelSource]

    @classmethod
    def from_model(cls, model: Model) -> "ModelResponse":
        """
        Create a ModelResponse from a Model object.

        Args:
            model: Model object

        Returns:
            ModelResponse object
        """
        model_dict = model.to_dict()

        # Convert sources to the expected format
        sources = []
        for source in model_dict.get("sources", []):
            sources.append(
                ModelSource(
                    source_id=source.get("source_id", ""),
                    source_type=source.get("source_type", ""),
                    source_identifier=source.get("source_identifier", {}),
                    requires_auth=source.get("requires_auth") or False,
                    created_at=source.get("created_at", datetime.now()),
                )
            )

        return cls(
            model_id=model_dict.get("model_id", ""),
            model_maker=model_dict.get("model_maker", ""),
            model_name=model_dict.get("model_name", ""),
            params_count=model_dict.get("params_count", 0),
            context_length=model_dict.get("context_length", None),
            quantization=model_dict.get("quantization", ""),
            created_at=model_dict.get("created_at", datetime.now()),
            sources=sources,
        )


class ModelsResponse(BaseModel):
    models: List[ModelResponse]
    total: int
    offset: int
    limit: int


class CPUInfo(BaseModel):
    count: int
    physical_count: int
    model: str
    frequency: dict


class MemoryInfo(BaseModel):
    total: int
    available: int
    percent: float


class GPUInfo(BaseModel):
    name: str
    memory_total: int
    memory_allocated: int
    memory_cached: int
    detection_method: Optional[str] = None


class DiskInfo(BaseModel):
    total: int
    available: int
    percent: float


class SystemInfo(BaseModel):
    os: str
    os_version: str
    python_version: str
    torch_version: str
    cuda_version: Optional[str]


class HardwareProfile(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo
    gpu: List[GPUInfo]
    disk: DiskInfo
    system: SystemInfo
    last_updated: datetime

    @classmethod
    def from_hardware_info(cls, hardware_info: HardwareInfo) -> "HardwareProfile":
        """
        Create a HardwareProfile from a HardwareInfo object.

        Args:
            hardware_info: HardwareInfo object

        Returns:
            HardwareProfile object
        """
        hardware_dict = hardware_info.to_dict()

        return cls(
            cpu=CPUInfo(**hardware_dict["cpu"]),
            memory=MemoryInfo(**hardware_dict["memory"]),
            gpu=[GPUInfo(**gpu) for gpu in hardware_dict["gpu"]],
            disk=DiskInfo(**hardware_dict["disk"]),
            system=SystemInfo(**hardware_dict["system"]),
            last_updated=hardware_dict["last_updated"],
        )


# =============================================
# Public MCP Tools
# =============================================


@mcp_server.tool("list_models")
def list_models(
    maker: Optional[str] = "",
    limit: int = 10,
    offset: int = 0,
    ctx: Context = None,
) -> Dict:
    """
    List all models available in the registry.

    Args:
        maker: Filter by model maker (empty string for no filter)
        limit: Maximum number of models to return
        offset: Number of models to skip
        ctx: MCP context

    Returns:
        Dictionary with models and pagination information
    """
    try:
        if ctx:
            ctx.info(f"Finding models with maker={maker}")
        # Create filter criteria from parameters
        filter_criteria = ModelFilterCriteria(maker=maker if maker else None)

        # Get models from registry using the find_models method with filter criteria
        models = get_registry().find_models(filters=filter_criteria)

        # Apply pagination
        total = len(models)
        paginated_models = models[offset : offset + limit]

        # Convert Model objects to response format using the from_model class method
        model_responses = []
        for model in paginated_models:
            if ctx:
                ctx.debug(f"Processing model: {model.model_info.get('model_name')}")
            model_responses.append(ModelResponse.from_model(model))

        return {
            "models": model_responses,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        if ctx:
            ctx.error(message=f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_server.tool("get_hardware_profile")
def get_hardware_profile(ctx: Context = None) -> Dict:
    """
    Get the current hardware profile of the machine.

    Args:
        ctx: MCP context

    Returns:
        Dictionary with hardware profile information
    """
    try:
        if ctx:
            ctx.info("Getting hardware profile")

        if get_registry().registry_type != "local":
            raise HTTPException(
                status_code=400,
                detail="Hardware profile is only available for local registry",
            )

        # Get hardware info from registry
        hardware_info = get_registry().get_saved_hardware_info()

        # Convert HardwareInfo object to HardwareProfile
        return HardwareProfile.from_hardware_info(hardware_info).model_dump()

    except Exception as e:
        if ctx:
            ctx.error(message=f"Error getting hardware profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_server.tool("get_model_template")
def get_model_template(source_type: Optional[str] = None, ctx: Context = None) -> Dict:
    """
    Get a template showing the required format and fields for adding a model to the registry.

    Args:
        source_type: Optional source type to get specific template for
        ctx: MCP context

    Returns:
        Dictionary with template and examples
    """
    try:
        # Base model info template that's always required
        template = {
            "model_info_template": {
                "model_maker": "organization_name",  # e.g. "meta", "google", "anthropic"
                "model_name": "unique_model_name",  # e.g. "llama-2-7b-chat"
                "params_count": 7000000000,  # Number of parameters, e.g. 7B = 7000000000
                "context_length": 131072,  # Maximum sequence length the model can handle
                "license_type": "llama2",  # e.g. "apache-2.0", "mit", "llama2"
                "quantization": "fp16",  # e.g. "fp32", "fp16", "int8", "int4"
            },
            "examples": {
                "llama2_example": {
                    "model_info": {
                        "model_maker": "meta",
                        "model_name": "llama-2-7b-chat",
                        "params_count": 7000000000,
                        "context_length": 131072,
                        "license_type": "llama2",
                        "quantization": "fp16",
                    }
                }
            },
        }

        # Add source info templates based on source type
        source_templates = {
            "huggingface_api": {
                "source_info_template": {
                    "source_type": "huggingface_api",
                    "source_identifier": json.dumps(
                        {
                            "loader_class": "AutoModelForCausalLM",  # Required for huggingface_api
                            "checkpoint": "organization/model-name",  # Required for huggingface_api
                        }
                    ),
                    "requires_auth": True,  # Optional, defaults to False
                },
                "example": {
                    "source_info": {
                        "source_type": "huggingface_api",
                        "source_identifier": json.dumps(
                            {
                                "loader_class": "AutoModelForCausalLM",
                                "checkpoint": "meta-llama/Llama-2-7b-chat",
                            }
                        ),
                        "requires_auth": True,
                    }
                },
            },
            "onnx": {
                "source_info_template": {
                    "source_type": "onnx",
                    "source_identifier": json.dumps(
                        {"model_path": "/path/to/model.onnx"}
                    ),
                    "requires_auth": False,
                }
            },
            "gguf": {
                "source_info_template": {
                    "source_type": "gguf",
                    "source_identifier": json.dumps(
                        {"model_path": "/path/to/model.gguf"}
                    ),
                    "requires_auth": False,
                }
            },
        }

        if source_type:
            if source_type not in source_templates:
                raise ValueError(
                    f"Invalid source_type. Must be one of: {', '.join(source_templates.keys())}"
                )
            template["source_info_template"] = source_templates[source_type][
                "source_info_template"
            ]
            if "example" in source_templates[source_type]:
                template["examples"]["with_source"] = {
                    **template["examples"]["llama2_example"],
                    **source_templates[source_type]["example"],
                }
        else:
            # If no specific source type requested, include all source templates
            template["source_info_templates"] = {
                source_type: info["source_info_template"]
                for source_type, info in source_templates.items()
            }
            # Add complete example with huggingface source
            template["examples"]["complete_example"] = {
                **template["examples"]["llama2_example"],
                **source_templates["huggingface_api"]["example"],
            }

        return template

    except Exception as e:
        if ctx:
            ctx.error(message=f"Error getting model template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_server.tool("add_model")
def add_model(model_info: Dict, source_info: Dict, ctx: Context = None) -> Dict:
    """
    Add a new model to the registry with source information.

    Args:
        model_info: Dictionary containing model information
        source_info: Dictionary containing source information
        ctx: MCP context

    Returns:
        Dictionary with model ID and source ID
    """
    registry = get_registry()
    if registry.registry_type == "local":
        print("Local registry does not support manual model addition")
        return
    try:
        if ctx:
            ctx.info(f"Adding model: {model_info.get('model_name')}")

        # Validate model info using imported function
        validate_model_info(model_info)

        # Validate source info using imported function
        validate_source_info(source_info)

        # Validate model source configuration using imported function
        validate_model_source(source_info)

        # ===== All validation passed, now add to database =====
        if ctx:
            ctx.info("Validation passed, adding model to registry")

        # Add model to registry
        model_id = get_registry().add_model(model_info)

        # Add source to registry
        source_id = get_registry().add_model_source(
            model_id,
            source_info["source_type"],
            {
                "source_identifier": source_info["source_identifier"],
                "requires_auth": source_info.get("requires_auth", False),
            },
        )

        return {
            "model_id": model_id,
            "source_id": source_id,
            "message": "Model and source added successfully",
        }

    except Exception as e:
        if ctx:
            ctx.error(message=f"Error adding model: {str(e)}")
        raise ValueError(f"Failed to add model: {str(e)}")


@mcp_server.tool("get_fingerprint_vectors")
def get_fingerprint_vectors(
    model_ids: List[str], fingerprint_type: str = "input_output", ctx: Context = None
) -> Dict:
    """
    Retrieve the fingerprint vector for a given fingerprint type for multiple model IDs.

    Args:
        model_ids: A list of model IDs.
        fingerprint_type: The type of the fingerprint to retrieve for all models. Defaults to "input_output".
        ctx: MCP context (unused).

    Returns:
        Dictionary containing a list of results, one for each model ID.
        Each result indicates success or failure and includes the vector or an error message.
    """
    return get_fingerprint_vectors_impl(model_ids, fingerprint_type, get_registry())


@mcp_server.tool("generate_fingerprint")
def generate_fingerprint(
    source_id: str,
    fingerprint_type: str,
    override: bool = False,
    use_remote: bool = False,
    ctx: Context = None,
) -> Dict:
    """
    Generates a specified type of fingerprint for a model identified by its source ID, returning
    the fingerprint. If the registry is global, the fingerprint is registered in the global registry.

    Args:
        source_id: ID of the specific model source entry.
        fingerprint_type: Type of fingerprint to generate.
        override: Whether to regenerate if fingerprint already exists.
        use_remote: Whether to use remote execution via Beam (True) or local execution (False).
        ctx: MCP context.

    Returns:
        Dictionary indicating success or failure, and the fingerprint ID if generated.
    """
    try:
        if ctx:
            # Log entry point with context
            ctx.info(
                f"Received request to generate fingerprint: type='{fingerprint_type}', source_id='{source_id}', override={override}, use_remote={use_remote}"
            )

        # Call the core implementation logic from resources.py
        result = generate_fingerprint_impl(
            registry=get_registry(),
            source_id=source_id,
            fingerprint_type=fingerprint_type,
            override=override,
            use_remote=use_remote,
        )

        # Log the outcome with context
        if ctx:
            if result.get("status") == "skipped":
                ctx.info(f"Skipped fingerprint generation: {result.get('message')}")
            elif result.get("status") == "success":
                ctx.info(f"Successfully generated fingerprint: {result.get('message')}")
            # Errors are handled by the except block

        return result  # Return the dictionary directly from the implementation

    # Handle exceptions raised by the implementation logic
    except ValueError as e:
        error_message = f"Error generating fingerprint (validation/logic): {str(e)}"
        if ctx:
            ctx.error(message=error_message)  # Log with context
        # Raise ValueError for client-side errors (bad input, config errors)
        raise ValueError(error_message)
    except HTTPException as e:
        # Handle errors specifically from remote execution or internal server issues
        error_message = f"Error generating fingerprint (server/execution): {e.detail}"
        if ctx:
            ctx.error(message=error_message)  # Log with context
        # Re-raise HTTPException
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        error_message = f"Unexpected error generating fingerprint: {str(e)}"
        if ctx:
            ctx.error(message=error_message)  # Log full traceback with context
        # Raise as a generic server error
        raise HTTPException(status_code=500, detail=error_message)


# TODO: Make tool more useful; either allow for multiple pairs, or just generate fp for a single model
@mcp_server.tool("compare_fp_pairs")
def compare_fp_pairs(
    vector_ref1: List[float],
    vector_var1: List[float],
    vector_ref2: List[float],
    vector_var2: List[float],
    family1_name: str,
    family2_name: str,
    model_name_ref1: str,
    model_name_var1: str,
    model_name_ref2: str,
    model_name_var2: str,
    ctx: Context = None,
) -> Dict:
    """
    Generates and saves a fingerprint visualization comparing two pairs of fingerprint vectors.

    Args:
        vector_ref1: Fingerprint vector of the first reference model.
        vector_var1: Fingerprint vector of the first variant model.
        vector_ref2: Fingerprint vector of the second reference model.
        vector_var2: Fingerprint vector of the second variant model.
        family1_name: Name for the first pair/family of models.
        family2_name: Name for the second pair/family of models.
        model_name_ref1: Name of the first reference model.
        model_name_var1: Name of the first variant model.
        model_name_ref2: Name of the second reference model.
        model_name_var2: Name of the second variant model.
        ctx: MCP context.

    Returns:
        Dictionary containing the path to the saved visualization PNG file.
    """
    try:
        if ctx:
            ctx.info(
                f"Received request to compare fingerprint pairs: families='{family1_name}', '{family2_name}'"
            )

        # Call the core implementation logic from resources.py
        result = compare_fp_pairs_impl(
            vector_ref1=vector_ref1,
            vector_var1=vector_var1,
            vector_ref2=vector_ref2,
            vector_var2=vector_var2,
            family1_name=family1_name,
            family2_name=family2_name,
            model_name_ref1=model_name_ref1,
            model_name_var1=model_name_var1,
            model_name_ref2=model_name_ref2,
            model_name_var2=model_name_var2,
        )

        # Log the outcome with context
        if ctx:
            if result.get("status") == "success":
                ctx.info(
                    f"Successfully generated comparison visualization at: {result.get('visualization_path')}"
                )
            # Errors are handled by the except block

        return result

    except ValueError as e:
        # Handle known errors from the implementation (e.g., visualization failure)
        error_message = f"Error comparing fingerprints: {str(e)}"
        if ctx:
            ctx.error(message=error_message)
        # Raise as ValueError (likely bad input or internal viz issue)
        raise ValueError(error_message)
    except Exception as e:
        # Catch any other unexpected errors
        error_message = f"Unexpected error comparing fingerprints: {str(e)}"
        if ctx:
            ctx.error(message=error_message)
        # Raise as a generic server error
        raise HTTPException(status_code=500, detail=error_message)


@mcp_server.tool("compute_fingerprint_similarity")
def compute_fingerprint_similarity(
    vector1: List[float],
    vector2: List[float],
    ctx: Context = None,
) -> Dict:
    """
    Directly compares two fingerprint vectors using l1_similarity from the VAIL metrics.

    Args:
        vector1: First fingerprint vector
        vector2: Second fingerprint vector
        ctx: MCP context

    Returns:
        Dictionary containing status and similarity score
    """
    try:
        # Log request if context is available
        if ctx:
            ctx.info("Computing l1 similarity between two fingerprint vectors")

        # Convert vectors to numpy arrays
        vec1 = np.array(vector1)
        vec2 = np.array(vector2)

        # Compute similarity
        similarity_score = l1_similarity(vec1, vec2)

        if ctx:
            ctx.info(f"Successfully computed l1 similarity: {similarity_score}")

        return {
            "status": "success",
            "similarity": similarity_score,
            "similarity_method": "l1",
        }
    except Exception as e:
        if ctx:
            ctx.error(message=f"Error computing l1 similarity: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in fingerprint comparison: {str(e)}"
        )
