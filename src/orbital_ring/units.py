"""Unit parsing at the configuration boundary."""

from __future__ import annotations

from typing import Any

import pint

from orbital_ring.constants import STANDARD_GRAVITY_M_S2

ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
ureg.define(f"g_0 = {STANDARD_GRAVITY_M_S2} * meter / second ** 2")


class UnitError(ValueError):
    """Raised when a required physical input is missing or dimensionally wrong."""


def parse_quantity(value: Any, unit: str, field: str) -> float:
    """Parse a unit-bearing string and return the magnitude in ``unit``.

    Bare numerics are rejected for dimensional values. This makes the YAML
    boundary explicit and prevents kilometre/metre or gram/kilogram mistakes.
    """

    if not isinstance(value, str):
        raise UnitError(
            f"{field} must be a unit-bearing string (for example '500 km'); "
            f"got {value!r}"
        )
    try:
        quantity = ureg.Quantity(value)
        return float(quantity.to(unit).magnitude)
    except (pint.PintError, ValueError, TypeError) as exc:
        raise UnitError(f"invalid units for {field}: {value!r}; expected {unit}") from exc

