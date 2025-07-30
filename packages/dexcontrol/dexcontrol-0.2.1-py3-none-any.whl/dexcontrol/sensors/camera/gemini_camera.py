# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""Gemini RGBD camera sensor implementation using Zenoh subscriber."""

import numpy as np
import zenoh

from dexcontrol.utils.subscribers.camera import RGBDCameraSubscriber


class GeminiCameraSensor:
    """Gemini RGBD camera sensor using Zenoh subscriber.

    This sensor provides both RGB and depth image data from an Orbbec Gemini camera
    using the RGBDCameraSubscriber for efficient data handling with lazy decoding.
    """

    def __init__(
        self,
        configs,
        zenoh_session: zenoh.Session,
    ) -> None:
        """Initialize the Gemini RGBD camera sensor.

        Args:
            rgb_topic: Zenoh topic for RGB data.
            depth_topic: Zenoh topic for depth data.
            zenoh_session: Active Zenoh session for communication.
            name: Name for the sensor instance.
            enable_fps_tracking: Whether to track and log FPS metrics.
            fps_log_interval: Number of frames between FPS calculations.
        """
        self._name = configs.name

        # Create the RGBD camera subscriber
        self._subscriber = RGBDCameraSubscriber(
            rgb_topic=configs.rgb_topic,
            depth_topic=configs.depth_topic,
            zenoh_session=zenoh_session,
            name=f"{self._name}_subscriber",
            enable_fps_tracking=configs.enable_fps_tracking,
            fps_log_interval=configs.fps_log_interval,
        )

    def shutdown(self) -> None:
        """Shutdown the camera sensor."""
        self._subscriber.shutdown()

    def is_active(self) -> bool:
        """Check if the camera sensor is actively receiving data.

        Returns:
            True if both RGB and depth are receiving data, False otherwise.
        """
        return self._subscriber.is_active()

    def wait_for_active(self, timeout: float = 5.0) -> bool:
        """Wait for the camera sensor to start receiving data.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if both RGB and depth become active, False if timeout is reached.
        """
        return self._subscriber.wait_for_active(timeout)

    def get_obs(self, obs_keys: list[str] | None = None) -> dict[str, np.ndarray] | None:
        """Get the latest RGBD data.

        Returns:
            Tuple of (rgb, depth) if both available, None otherwise.
        """
        if obs_keys is None:
            obs_keys = ["rgb", "depth"]
        obs_out = {}
        for key in obs_keys:
            if key == "rgb":
                obs_out[key] = self._subscriber.get_latest_rgb()
            elif key == "depth":
                obs_out[key] = self._subscriber.get_latest_depth()
            else:
                raise ValueError(f"Invalid observation key: {key}")
        return obs_out

    def get_rgb_image(self) -> np.ndarray | None:
        """Get the latest RGB image.

        Returns:
            Latest RGB image as numpy array (HxWxC) if available, None otherwise.
        """
        return self._subscriber.get_latest_rgb()

    def get_depth_image(self) -> np.ndarray | None:
        """Get the latest depth image.

        Returns:
            Latest depth image as numpy array (HxW) with values in meters if available, None otherwise.
        """
        return self._subscriber.get_latest_depth()

    @property
    def rgb_fps(self) -> float:
        """Get the RGB stream FPS measurement.

        Returns:
            Current RGB frames per second measurement.
        """
        return self._subscriber.rgb_fps

    @property
    def depth_fps(self) -> float:
        """Get the depth stream FPS measurement.

        Returns:
            Current depth frames per second measurement.
        """
        return self._subscriber.depth_fps

    @property
    def fps(self) -> float:
        """Get the combined FPS measurement (minimum of RGB and depth).

        Returns:
            Current frames per second measurement.
        """
        return min(self.rgb_fps, self.depth_fps)

    @property
    def name(self) -> str:
        """Get the sensor name.

        Returns:
            Sensor name string.
        """
        return self._name
