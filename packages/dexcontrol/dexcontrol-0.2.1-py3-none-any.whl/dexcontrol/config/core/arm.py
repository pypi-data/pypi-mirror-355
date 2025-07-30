# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ArmConfig:
    _target_: str = "dexcontrol.core.arm.Arm"
    state_sub_topic: str = "state/arm/right"
    wrench_sub_topic: str = "state/wrench/right"
    control_pub_topic: str = "control/arm/right"
    set_mode_query: str = "mode/arm/right"
    dof: int = 7
    joint_name: list[str] = field(
        default_factory=lambda: [f"R_arm_j{i + 1}" for i in range(7)]
    )
    joint_limit: list[list[float]] = field(
        default_factory=lambda: [[-np.pi, np.pi] for _ in range(7)]
    )
    pose_pool: dict[str, list[float]] = field(
        default_factory=lambda: {
            "folded": [-1.57079, 0.0, 0, -3.1, 0, 0, 0.69813],
            "folded_closed_hand": [-1.57079, 0.0, 0, -3.1, 0, 0, 0.9],
            "L_shape": [-0.064, 0.3, 0.0, -1.556, -1.271, 0.0, 0.0],
            "zero": [1.57079, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )
