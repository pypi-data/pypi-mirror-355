"""Constants used throughout the dexcontrol package."""

from typing import Final

# Environment variable for robot name
ROBOT_NAME_ENV_VAR: Final[str] = "ROBOT_NAME"

# Environment variable for communication config path
COMM_CFG_PATH_ENV_VAR: Final[str] = "DEXMATE_COMM_CFG_PATH"

# Environment variable to disable heartbeat monitoring
DISABLE_HEARTBEAT_ENV_VAR: Final[str] = "DEXCONTROL_DISABLE_HEARTBEAT"
