# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass, field


@dataclass
class ChassisConfig:
    _target_: str = "dexcontrol.core.chassis.Chassis"
    control_pub_topic: str = "control/chassis"
    state_sub_topic: str = "state/chassis"
    dof: int = 2
    center_to_wheel_axis_dist: float = (
        0.219  # the distance between base center and wheel axis in m
    )
    wheels_dist: float = 0.41  # the distance between two wheels in m (0.41 for vega_rc2, 0.45 for vega_1)
    joint_name: list[str] = field(
        default_factory=lambda: ["L_wheel_j1", "L_wheel_j2", "R_wheel_j1", "R_wheel_j2"]
    )
    max_vel: float = 0.6
