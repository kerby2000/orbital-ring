"""Named physical and numerical constants used by the kernel.

Earth parameters are deliberately not defaults for scenario loading. They are
provided here as documented reference values and must still appear in YAML.
"""

from __future__ import annotations

import math

# Exact conventional standard acceleration due to gravity (SI), used only to
# interpret inputs such as ``1000 g_0``.
STANDARD_GRAVITY_M_S2 = 9.80665

# Reference values used in the supplied scenario, not silently substituted.
REFERENCE_EARTH_MEAN_RADIUS_M = 6_371_000.0
REFERENCE_EARTH_MU_M3_S2 = 3.986_004_418e14
REFERENCE_EARTH_ROTATION_RAD_S = 7.292_115_0e-5

TAU = 2.0 * math.pi
MODEL_VERSION = "0.2.0"
L0_LABEL = "L0 closed-form scaling"
L1_LABEL = "L1 numerical two-body propagation"
