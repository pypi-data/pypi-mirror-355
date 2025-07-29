"""
Runs methods in the cloud using beam
"""

from typing import Any, Callable

from beam import Image, function

from vail.utils.env import get_env_var_keys


class BeamProvider:
    """
    Provides support for cloud execution of arbitrary code.
    """

    def __init__(self, device_type: str = "cpu", dockerfile_path: str = "./Dockerfile"):
        allowed_devices = [
            "cpu",
            "a100-40",
            "a100-80",
            "a10g",
            "a6000",
            "h100",
            "l4",
            "rtx4090",
            "t4",
        ]
        if device_type.lower() not in allowed_devices:
            raise ValueError(
                f"Invalid device type: {device_type}. Valid types are: {allowed_devices}"
            )
        self.device_type = device_type.upper() if device_type.lower() != "cpu" else None
        self.image = Image().from_dockerfile(dockerfile_path)

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Pass in a function and its arguments and it will be executed in a remote enviornment using beam.cloud
        """
        secrets = get_env_var_keys()
        if self.device_type:
            # Run on cloud GPU
            cloud_func = function(
                image=self.image, gpu=self.device_type, secrets=secrets
            )(func)
        else:
            # Run on cloud CPU
            cloud_func = function(image=self.image, secrets=secrets)(func)
        return cloud_func.remote(*args, **kwargs)
