# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from hydra.core.config_store import ConfigStore

from .vega import Vega1Config, VegaConfig

# Register the configs
cs = ConfigStore.instance()
cs.store(name="vega", node=VegaConfig)
cs.store(name="vega_rc2", node=VegaConfig)
cs.store(name="vega_1", node=Vega1Config)
