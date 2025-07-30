# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass


@dataclass
class GeminiCameraConfig:
    _target_: str = "dexcontrol.sensors.camera.gemini_camera.GeminiCameraSensor"
    rgb_topic: str = "camera/gemini/rgb"
    depth_topic: str = "camera/gemini/depth"
    name: str = "gemini_camera"
    enable_fps_tracking: bool = False
    fps_log_interval: int = 30
