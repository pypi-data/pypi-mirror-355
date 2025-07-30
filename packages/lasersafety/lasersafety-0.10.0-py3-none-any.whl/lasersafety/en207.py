# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Compute scale numbers using the EN207 standard.
"""

from typing import Union

import numpy as np

from lasersafety.modes import Mode, get_test_by_pulse_duration
from lasersafety.utils import (
    validate_wavelength_en207,
    validate_strictly_positive_number,
)


def continuous_scale_number(
    average_power: Union[float, int],
    area: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Find the scale number for a continuous beam. This
    method uses the average power (in W), the area (in m^2)
    and the wavelength in m. The power density is computed by
    dividing the average power by the area. Depending on the
    wavelength, the scale number is returned.

    Args:
        average_power (Union[float, int]): average power, in W.
        area (Union[float, int]): beam area, in m^2.
        wavelength (Union[float, int]): wavelength, in m.

    Returns:
        int: scale number for the continuous beam.
    """
    # Checks
    validate_wavelength_en207(wavelength)
    validate_strictly_positive_number(average_power, "averge power")
    validate_strictly_positive_number(area, "area")

    # Compute the density
    power_density = average_power / area

    # Use the formula depending on the wavelength

    # 180nm -315 nm
    if wavelength <= 315e-9:
        # log(P)+3
        res = np.log10(power_density) + 3

    # > 315 nm - 1400 nm
    elif wavelength <= 1400e-9:
        # log(P)-1
        res = np.log10(power_density) - 1

    # 1400 nm - 1 mm
    else:
        # log(P) - 3
        res = np.log10(power_density) - 3

    return np.max((1, np.ceil(res))).astype(int)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def pulsed_scale_number(
    peak_power: Union[float, int],
    pulse_energy: Union[float, int],
    area: Union[float, int],
    pulse_duration: Union[float, int],
    repetition_rate: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Compute the scale number for a pulsed beam. This is
    done by using the peak power (in W), the pulse energy
    (in J), the area (in m^2), the pulse duration (in s),
    the repetition rate (in Hz) and the wavelength (in m).

    The laser mode is computed using the pulse duration. Then,
    it calls either :py:func:`~lasersafety.en207._pulsed_scale_number_ir`
    or :py:func:`~lasersafety.en207._pulsed_scale_number_m` with
    the pulse energy, the area, the repetition rate and the
    wavelength.

    Args:
        peak_power (Union[float, int]): peak power, in W.
        pulse_energy (Union[float, int]): pulse energy, in J.
        area (Union[float, int]): beam area, in m^2.
        pulse_duration (Union[float, int]): pulse duration, in s.
        repetition_rate (Union[float, int]): repetition rate, in Hz.
        wavelength (Union[float, int]): wavelength, in m.

    Raises:
        Exception: when using this function with a mode D laser.

    Returns:
        int: the scale number for the pulsed beam.
    """

    # Checks
    validate_strictly_positive_number(peak_power, "peak power")
    validate_strictly_positive_number(pulse_energy, "pulse energy")
    validate_strictly_positive_number(area, "area")
    validate_strictly_positive_number(pulse_duration, "pulse duration")
    validate_strictly_positive_number(repetition_rate, "repetition rate")
    validate_wavelength_en207(wavelength)

    mode = get_test_by_pulse_duration(pulse_duration)

    assert mode in (Mode.D, Mode.I, Mode.R, Mode.M)

    if mode == Mode.D:
        raise Exception("Cannot use this function with continuous laser")

    if mode in (Mode.I, Mode.R):
        return _pulsed_scale_number_ir(pulse_energy, area, repetition_rate, wavelength)

    # Mode is Mode.M
    return _pulsed_scale_number_m(
        peak_power, pulse_energy, area, repetition_rate, wavelength
    )


def _pulsed_scale_number_ir(
    pulse_energy: Union[float, int],
    area: Union[float, int],
    repetition_rate: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Compute the scale number for an I or R pulsed laser,
    done by using the pulse energy (in J), the beam area
    (in m^2), the repetition rate (in Hz) and the
    wavelength (in m).

    It computes the energy density by dividing the pulse
    energy by the area. Then if the wavelength is between
    400 nm and 1400 nm, the energy density is corrected
    with the fourth root of the number of pulses in 10 s.

    Args:
        pulse_energy (Union[float, int]): the pulse energy, in J.
        area (Union[float, int]): the beam area, in m^2.
        repetition_rate (Union[float, int]): the repetition rate, in Hz.
        wavelength (Union[float, int]): the wavelength, in m.

    Returns:
        int: the scale number for an I or R pulsed laser.
    """
    energy_density = pulse_energy / area

    # Correction if wavelength is between 400 nm and 1400 nm
    if 400e-9 <= wavelength <= 1400e-9:
        number_pulses = repetition_rate * 10
        energy_density *= number_pulses**0.25

    # Compute the scale number depending on the wavelength
    # 180nm -315 nm

    if wavelength <= 315e-9:
        # log(E/3)-1
        res = np.log10(energy_density / 3) - 1

    # > 315 nm - 1400 nm
    elif wavelength <= 1400e-9:
        # log(E/5)+3
        res = np.log10(energy_density / 5) + 3

    # 1400 nm - 1 mm
    else:
        # log(E)-2
        res = np.log10(energy_density) - 2

    return np.max((1, np.ceil(res))).astype(int)


def _pulsed_scale_number_m(
    peak_power: Union[float, int],
    pulse_energy: Union[float, int],
    area: Union[float, int],
    repetition_rate: Union[float, int],
    wavelength: Union[float, int],
) -> int:
    """Compute the scale number for an M pulsed laser,
    done by using the peak power (in W), the pulse
    energy (in J), the beam area (in m^2), the repetition
    rate (in Hz) and the wavelength (in m).

    If the wavelength is between 315 nm and 1400 nm, the
    energy, computed as the ratio of the pulse energy and
    the beam area, is used to determine the scale number.
    Additionnally, if the wavelength is between 400 nm
    and 1400 nm, the energy density is corrected by
    the fourth root of the number of pulses in 10 s.

    If the wavelength is not in this range, the peak
    power density is computed by dividing the peak
    power power by the beam area. Then the scale number
    is returned.

    Args:
        peak_power (Union[float, int]): the peak power, in W.
        pulse_energy (Union[float, int]): the pulse energy, in J.
        area (Union[float, int]): the beam area, in m^2.
        repetition_rate (Union[float, int]): the repetition rate, in Hz.
        wavelength (Union[float, int]): the wavelength, in m.

    Returns:
        int: the scale number for an M pulsed laser.
    """
    if 315e-9 < wavelength <= 1400e-9:
        energy_density = pulse_energy / area
        if 400e-9 <= wavelength:
            number_pulses = repetition_rate * 10
            energy_density *= number_pulses**0.25

        # log(E/1.5)+4
        res = np.log10(energy_density / 1.5) + 4

    else:
        peak_power_density = peak_power / area

        if wavelength <= 315e-9:
            # log(P/3) - 10
            res = np.log10(peak_power_density / 3) - 10
        else:
            # log(P)-11
            res = np.log10(peak_power_density) - 11
    return np.max((1, np.ceil(res))).astype(int)
