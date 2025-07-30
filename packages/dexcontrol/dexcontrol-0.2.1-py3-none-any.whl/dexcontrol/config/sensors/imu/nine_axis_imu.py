# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass


@dataclass
class NineAxisIMUConfig:
    _target_: str = "dexcontrol.sensors.imu.nine_axis_imu.NineAxisIMUSensor"
    topic: str = "/imu/nine_axis"
    name: str = "nine_axis_imu"
    enable_fps_tracking: bool = False
    fps_log_interval: int = 30
