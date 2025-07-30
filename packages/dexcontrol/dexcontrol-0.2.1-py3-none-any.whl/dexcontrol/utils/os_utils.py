"""Operating system utility functions."""

import os
from typing import Final

from loguru import logger

from dexcontrol.utils.constants import ROBOT_NAME_ENV_VAR


def resolve_key_name(key: str) -> str:
    """Resolves a key name for zenoh topic by prepending robot name.

    Args:
        key: Original key name (e.g. 'lidar' or '/lidar')

    Returns:
        Resolved key with robot name prepended (e.g. 'robot/lidar')
    """
    # Get robot name from env var or use default
    robot_name: Final[str] = os.getenv(ROBOT_NAME_ENV_VAR, "robot")

    # Remove leading slash if present
    key = key.lstrip("/")

    # Combine robot name and key with single slash
    return f"{robot_name}/{key}"


def get_robot_model() -> str:
    """Get the robot model from the environment variable."""
    robot_model_abb_mapping = dict(vg="vega")
    robot_name = os.getenv(ROBOT_NAME_ENV_VAR, "robot")
    robot_model_abb = robot_name.split("/")[-1].split("-")[0][:2]
    if robot_model_abb not in robot_model_abb_mapping:
        raise ValueError(f"Unknown robot model: {robot_model_abb}")
    model = robot_model_abb_mapping[robot_model_abb] + "-" + robot_name.split("-")[-1]
    logger.info(f"The current robot model is: {model}")
    return model
