# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from dataclasses import dataclass, field


@dataclass
class HandConfig:
    _target_: str = "dexcontrol.core.hand.HandF5D6"
    state_sub_topic: str = "state/hand/right"
    control_pub_topic: str = "control/hand/right"
    dof: int = 6
    joint_name: list[str] = field(
        default_factory=lambda: [
            "R_th_j1",
            "R_ff_j1",
            "R_mf_j1",
            "R_rf_j1",
            "R_lf_j1",
            "R_th_j0",
        ]
    )

    # Not to modify the following varaibles unless you change a different hand
    control_joint_names: list[str] = field(
        default_factory=lambda: ["th_j1", "ff_j1", "mf_j1", "rf_j1", "lf_j1", "th_j0"]
    )
    joint_pos_open: list[float] = field(
        default_factory=lambda: [0.18313, 0.29012, 0.28084, 0.28498, 0.28204, -0.034]
    )
    joint_pos_close: list[float] = field(
        default_factory=lambda: [
            -0.64862,
            -1.17584,
            -1.16855,
            -1.17493,
            -1.17277,
            1.6,
        ]
    )
