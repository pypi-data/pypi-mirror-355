# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""DexControl: Robot Control Interface Library.

This package provides interfaces for controlling and monitoring robot systems.
It serves as the primary API for interacting with Dexmate robots.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# DO NOT REMOVE this following import, it is needed for hydra to find the config
import dexcontrol.config  # pylint: disable=unused-import
from dexcontrol.robot import Robot
from dexcontrol.utils.constants import COMM_CFG_PATH_ENV_VAR

# Package-level constants
LIB_PATH: Final[Path] = Path(__file__).resolve().parent
CFG_PATH: Final[Path] = LIB_PATH / "config"


def get_comm_cfg_path() -> Path:
    default_path = list(
        Path("~/.dexmate/comm/zenoh/").expanduser().glob("**/zenoh_peer_config.json5")
    )
    if len(default_path) == 0:
        raise FileNotFoundError(
            "No zenoh_peer_config.json5 file found in ~/.dexmate/comm/zenoh/"
        )
    return default_path[0]


COMM_CFG_PATH: Final[Path] = Path(
    os.getenv(COMM_CFG_PATH_ENV_VAR, get_comm_cfg_path())
).expanduser()

ROBOT_CFG_PATH: Final[Path] = CFG_PATH

__all__ = ["Robot", "LIB_PATH", "CFG_PATH", "COMM_CFG_PATH", "ROBOT_CFG_PATH"]
