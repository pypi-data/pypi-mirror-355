# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Modes of the laser as defined in the EN207 standard.
"""

from typing import Union
from enum import StrEnum


class Mode(StrEnum):
    """
    Possible modes of the laser as defined
    in EN207 standard.
    """

    D = "D"  #: Continuous t > 0.25s
    I = "I"  #: Long pulse 1ms <= t < 0.25s
    R = "R"  #: Short pulse 1ns <= t < 1ms
    M = "M"  #: Ultra short pulse t < 1ns


def get_test_by_pulse_duration(pulse_duration: Union[float, int]) -> Mode:
    """Return the mode of the laser depending on the pulse
    duration. The pulse duration is expected in second. It
    should be a float (or an int) greater or equal than 0.
    A value of 0 is assumed to mean "continuous wave (CW)"
    and mode D is returned.

    Args:
        pulse_duration (float): duration of the pulse in seconds.

    Raises:
        ValueError: if the pulse duration is not a float (or an int).
        ValueError: if the pulse duration is strictly lower than 0.

    Returns:
        Mode: the mode corresponding to the given pulse duration as per EN207.
    """
    if not isinstance(pulse_duration, (float, int)):
        raise ValueError("pulse_duration must be a float (or int)")

    if pulse_duration < 0:
        raise ValueError(
            f"pulse_duration must be greater or equal than 0 (got {pulse_duration})"
        )

    if pulse_duration == 0:
        return Mode.D

    if pulse_duration < 1e-9:
        return Mode.M

    if pulse_duration < 1e-3:
        return Mode.R

    if pulse_duration < 0.25:
        return Mode.I

    return Mode.D
