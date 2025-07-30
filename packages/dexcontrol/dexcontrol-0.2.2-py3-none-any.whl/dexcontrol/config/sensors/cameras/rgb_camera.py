# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass


@dataclass
class RGBCameraConfig:
    _target_: str = "dexcontrol.sensors.camera.rgb_camera.RGBCameraSensor"
    topic: str = "/camera/rgb"
    name: str = "rgb_camera"
    enable_fps_tracking: bool = False
    fps_log_interval: int = 30
