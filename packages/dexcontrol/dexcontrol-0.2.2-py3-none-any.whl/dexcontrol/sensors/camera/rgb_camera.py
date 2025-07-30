# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""RGB camera sensor implementation using Zenoh subscriber."""

import numpy as np
import zenoh

from dexcontrol.utils.subscribers.camera import RGBCameraSubscriber


class RGBCameraSensor:
    """RGB camera sensor using Zenoh subscriber.

    This sensor provides RGB image data from a camera using the
    RGBCameraSubscriber for efficient data handling with lazy decoding.
    """

    def __init__(
        self,
        configs,
        zenoh_session: zenoh.Session,
    ) -> None:
        """Initialize the RGB camera sensor.

        Args:
            configs: Configuration for the RGB camera sensor.
            zenoh_session: Active Zenoh session for communication.
        """
        self._name = configs.name

        # Create the RGB camera subscriber
        self._subscriber = RGBCameraSubscriber(
            topic=configs.topic,
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
            True if receiving data, False otherwise.
        """
        return self._subscriber.is_active()

    def wait_for_active(self, timeout: float = 5.0) -> bool:
        """Wait for the camera sensor to start receiving data.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if sensor becomes active, False if timeout is reached.
        """
        return self._subscriber.wait_for_active(timeout)

    def get_obs(self) -> np.ndarray | None:
        """Get the latest RGB image data.

        Returns:
            Latest RGB image as numpy array (HxWxC) if available, None otherwise.
        """
        return self._subscriber.get_latest_data()

    def get_rgb_image(self) -> np.ndarray | None:
        """Get the latest RGB image.

        Returns:
            Latest RGB image as numpy array (HxWxC) if available, None otherwise.
        """
        return self._subscriber.get_latest_image()

    @property
    def fps(self) -> float:
        """Get the current FPS measurement.

        Returns:
            Current frames per second measurement.
        """
        return self._subscriber.fps

    @property
    def name(self) -> str:
        """Get the sensor name.

        Returns:
            Sensor name string.
        """
        return self._name
