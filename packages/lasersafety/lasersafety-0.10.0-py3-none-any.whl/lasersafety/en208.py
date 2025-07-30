# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Compute scale numbers using the EN208 standard.
"""

from typing import Union

import numpy as np

from lasersafety.utils import (
    validate_wavelength_en208,
    validate_strictly_positive_number,
)


def continuous_scale_number_en208(
    average_power: Union[float, int],
    area: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Compute the cotninuous scale number for en208.

    It computes the power density by dividing the power density
    by the area and uses it to return the sccale number.

    Args:
        average_power (Union[float, int]): the average power, in W.
        area (Union[float, int]): the beam area, in m^2.
        wavelength (Union[float, int]): the wavelength, in m.

    Returns:
        int: the scale number for the continuous laser.
    """
    # Checks
    validate_strictly_positive_number(average_power, "average power")
    validate_strictly_positive_number(area, "area")
    validate_wavelength_en208(wavelength)

    power_density = average_power / area

    # log(P)-3
    return np.ceil(np.log10(power_density) - 3).astype(int)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def pulsed_scale_number_en208(
    peak_power: Union[float, int],
    pulse_energy: Union[float, int],
    area: Union[float, int],
    pulse_duration: Union[float, int],
    repetition_rate: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Compute the scale number for the EN208 standard
    for pulsed lasers.

    It computes the corrected energy density by using the pulse
    energy, the area and the repetion rate, then returns the
    scale number.

    Args:
        peak_power (Union[float, int]): the peak power, in W.
        pulse_energy (Union[float, int]): the pulse energy, in J.
        area (Union[float, int]): the beam area, in m^2.
        pulse_duration (Union[float, int]): the pulse duration, in s.
        repetition_rate (Union[float, int]): the repetition rate, in Hz.
        wavelength (Union[float, int]): the wavelength, in m.

    Raises:
        ValueError: if pulse duration is less or equal than 1 ns.

    Returns:
        int: the scale number for the EN208 standard.
    """
    # Checks
    validate_strictly_positive_number(peak_power, "peak power")
    validate_strictly_positive_number(pulse_energy, "pulse energy")
    validate_strictly_positive_number(area, "area")
    validate_strictly_positive_number(pulse_duration, "pulse duration")
    validate_strictly_positive_number(repetition_rate, "repetition rate")
    validate_wavelength_en208(wavelength)

    if pulse_duration >= 2e-4:
        # treat as continuous as per EN208
        return continuous_scale_number_en208(
            pulse_energy * repetition_rate, area, wavelength
        )

    if pulse_duration <= 1e-9:
        raise ValueError("EN208 standard consider pulse duration > 1ns.")

    # Compute corrected energy density
    energy_density = pulse_energy / area
    number_pulses = repetition_rate * 10
    energy_density *= number_pulses**0.25

    # log(E/2)+1
    return np.ceil(np.log10(energy_density / 2) + 1).astype(int)
