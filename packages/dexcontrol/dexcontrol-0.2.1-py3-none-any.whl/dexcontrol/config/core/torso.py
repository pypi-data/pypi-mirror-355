# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass, field


@dataclass
class TorsoConfig:
    _target_: str = "dexcontrol.core.torso.Torso"
    state_sub_topic: str = "state/torso"
    control_pub_topic: str = "control/torso"
    dof: int = 3
    joint_name: list[str] = field(
        default_factory=lambda: ["torso_j1", "torso_j2", "torso_j3"]
    )
    default_vel: float = 0.4  # rad/s, will be used if joint_vel is not provided
    max_vel: float = 0.6  # max velocity of torso joint, will be used to clip
    # the joint_vel, Highly recommended to set this value
    # not higher than 0.6 rad/s
    pose_pool: dict[str, list[float]] = field(
        default_factory=lambda: {
            "home": [0.0, 0.0, 0.0],
            "folded": [0.0, 0.0, -1.5708],
            "crouch20_low": [0.0, 0.0, -0.35],
            "crouch20_medium": [0.52, 1.05, 0.18],
            "crouch20_high": [0.78, 1.57, 0.44],
            "crouch45_low": [0.0, 0.0, -0.79],
            "crouch45_medium": [0.52, 1.05, -0.26],
            "crouch45_high": [0.78, 1.57, 0],
            "crouch90_low": [0.0, 0.0, -1.57],
            "crouch90_medium": [0.52, 1.05, -1.04],
            "crouch90_high": [0.78, 1.57, -0.78],
        }
    )
