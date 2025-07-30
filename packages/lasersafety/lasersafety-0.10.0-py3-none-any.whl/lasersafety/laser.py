# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Defines a laser beam object with the important parameters to make the laser safety computations.
"""

from typing import Optional, Tuple, List

import numpy as np

from lasersafety.modes import get_test_by_pulse_duration, Mode
from lasersafety.utils import format_value
from lasersafety.en207 import continuous_scale_number, pulsed_scale_number
from lasersafety.en208 import continuous_scale_number_en208, pulsed_scale_number_en208


# pylint: disable=too-many-instance-attributes
class LaserBeam:
    """
    The LaserBeam object with the necessary parameters to make the laser safety computations.
    """

    average_power: Optional[float | int]  #: Average power of the beam, in W.
    repetition_rate: Optional[float | int]  #: Repetition rate of the laser, in Hz.
    pulse_duration: Optional[float | int]  #: Pulse duration for pulsed lasers, in s.
    pulse_energy: Optional[float | int]  #: Pulse energy for pulsed lasers, in J.
    peak_power: Optional[float | int]  #: Peak power for pulsed lasers, in W.
    wavelength: Optional[float | int]  #: Wavelength of the beam, in m.
    base_beam_diameter: Optional[float | int]  #: Base beam diameter, in m.
    beam_divergence: Optional[float | int]  #: Beam divergence, in rad.
    distance: Optional[float | int]  #: Distance to consider for divergent beam, in m.
    continuous: bool  #: True, if the laser is continuous, False if it is pulsed.

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        wavelength: float | int,
        repetition_rate: float | int,
        beam_diameter: float | int,
        average_power: Optional[float | int] = None,
        peak_power: Optional[float | int] = None,
        pulse_duration: Optional[float | int] = None,
        pulse_energy: Optional[float | int] = None,
        divergence: Optional[float | int] = 0,
        distance: float | int = 10e-2,
    ):
        """
        The init method has four optional parameters: average_power, peak_power, pulse_duration, and pulse_energy.
        These four parameters are interconnected, and usually, two of them are enough to find the other two
        (unless the average power and pulse energy are given). Creating a laser beam with two few OR too many
        arguments (or only the average power and pulse energy), will result in a raised exception.

        Args:
            wavelength (float | int): wavelength of the light, in m.
            repetition_rate (float | int): repetition rate for pulsed lasers, in Hz. Set this value to 0 for a continuous laser.
            beam_diameter (float | int): beam diameter, in m.
            average_power (Optional[float  |  int], optional): average power, in W. This parameter may be omitted if the peak_power and pulse_duration or the pulse energy are given. This parameter may not be omitted for continuous lasers. Defaults to None.
            peak_power (Optional[float  |  int], optional): peak power, in W. This parameter may be omitted if the average_power and pulse_duration or the pulse_energy and pulse_duration are given. This parameter may be omitted for pulsed lasers. Defaults to None.
            pulse_duration (Optional[float  |  int], optional): pulse duration, in s. This parameter may be omitted if the average_power or the pulse_energy and pulse_duration are given. This parameter may be omitted for pulsed lasers. Defaults to None.
            pulse_energy (Optional[float  |  int], optional): pulse energy, in J. This parameter may be omitted if the peak_power and pulse_duration or average power are given. This parameter may be omitted for pulsed lasers. Defaults to None.
            divergence (float | int, optional): divergence, in rad. Defaults to 0.
            distance (float | int, optional): distance to consider for divergent beam, in m. Defaults to 10e-2.

        Raises:
            ValueError: if the average power is omitted for a continuous laser.
        """
        self.wavelength = wavelength
        self.repetition_rate = repetition_rate

        self.base_beam_diameter = beam_diameter
        if divergence is None:
            self.beam_divergence = 0
        else:
            self.beam_divergence = divergence
        self.distance = distance

        if self.repetition_rate == 0:
            # Assume the laser is continuous
            self.peak_power = 0
            self.pulse_duration = 0
            self.pulse_energy = 0
            self.continuous = True
            if average_power is None:
                raise ValueError("For continous laser, average power is required.")
            self.average_power = average_power
        else:
            self.continuous = False
            (
                self.average_power,
                self.peak_power,
                self.pulse_duration,
                self.pulse_energy,
            ) = self._solve(
                repetition_rate, average_power, peak_power, pulse_duration, pulse_energy
            )

    # pylint:disable=too-many-branches
    def _solve(
        self,
        repetition_rate: float | int,
        average_power: Optional[float | int] = None,
        peak_power: Optional[float | int] = None,
        pulse_duration: Optional[float | int] = None,
        pulse_energy: Optional[float | int] = None,
    ) -> Tuple[float | int, float | int, float | int, float | int]:
        """Solve the laser parameters (from two parameters, find the other two).
        This first checks that exactly two parameters are given, and that this is
        not the (average_power, pulse_energy) case.

        Then, it manually goes over the 5 cases and use the formulas, to return all the
        parameters.

        Args:
            repetition_rate (float | int): repetition rate, in Hz.
            average_power (Optional[float  |  int], optional): average power, in W. Defaults to None.
            peak_power (Optional[float  |  int], optional): peak power, in W. Defaults to None.
            pulse_duration (Optional[float  |  int], optional): pulse duration, in s. Defaults to None.
            pulse_energy (Optional[float  |  int], optional): pulse energy, J. Defaults to None.

        Raises:
            ValueError: if stritcly more than 2 parameters are given.
            ValueError: if strictly less than 2 parameters are given.
            ValueError: if average_power and pulse_energy are the two given parameters.

        Returns:
            Tuple[float | int, float | int, float | int, float | int]: the average power in W, the peak power in W, the pulse duration in s, the pulse energy in J.
        """
        # Count number of parameters
        i = 0
        if pulse_energy is None:
            i += 1
        if average_power is None:
            i += 1
        if peak_power is None:
            i += 1
        if pulse_duration is None:
            i += 1

        if i > 2:
            raise ValueError(
                "Not enough parameters are given in (pulse energy, average power, peak power, pulse duration)"
            )
        if i < 2:
            raise ValueError(
                "Too many parameters are given in (pulse energy, average power, peak power, pulse duration)"
            )

        if average_power is not None and pulse_energy is not None:
            raise ValueError(
                "average power and pulse energy is not enough to find peak power and pulse duration"
            )

        if average_power is not None:
            if peak_power is not None:
                return (
                    average_power,
                    peak_power,
                    average_power / repetition_rate,
                    average_power / (peak_power * repetition_rate),
                )
            if pulse_duration is not None:
                return (
                    average_power,
                    average_power / (pulse_duration * repetition_rate),
                    pulse_duration,
                    average_power / repetition_rate,
                )
        if peak_power is not None:
            if pulse_duration is not None:
                return (
                    peak_power / pulse_duration * repetition_rate,
                    peak_power,
                    pulse_duration,
                    peak_power / pulse_duration,
                )
            if pulse_energy is not None:
                return (
                    repetition_rate * pulse_energy,
                    peak_power,
                    pulse_energy / peak_power,
                    pulse_energy,
                )

        # The only case left is (pulse_duration, pulse_energy)
        return (
            repetition_rate * pulse_energy,
            pulse_energy / pulse_duration,
            pulse_duration,
            pulse_energy,
        )

    @property
    def beam_diameter(self) -> float:
        """The beam diameter at the considered distance.
        If the divergence is 0, this is directly the beam
        diameter. Otherwise it is computed with

        :math:`D(d) = D_{base} + 2d\\tan(\\theta)`

        where :math:`D(d)` is the diameter at distance
        :math:`d`, :math:`D_{base}` the base diameter and
        :math:`\\theta` the divergence.

        Returns:
            float: the diameter, in m at the considered distance.
        """
        if self.beam_divergence == 0:
            return self.base_beam_diameter

        return self.base_beam_diameter + 2 * self.distance * np.tan(
            self.beam_divergence
        )

    @property
    def cross_section_area(self) -> float:
        """The cross section area, computed as

        :math:`\\pi \\left(\\frac{D(d)}{2}\\right)^2`

        where :math:`D(d)` is the beam diameter at
        distance :math:`d`.

        Returns:
            float: the cross section area, in m^2.
        """
        return np.pi * (self.beam_diameter / 2) ** 2

    @property
    def reference_number_pulses(self) -> float:
        """The reference number of pulses used in the
        EN207 standard, which is the number of pulses
        in 10 s.

        This is computed by multiplying the
        repetition rate in Hz by 10.

        Returns:
            float: number of pulses in 10 s.
        """
        return 10 * self.repetition_rate

    @property
    def power_density(self) -> float:
        """Power density in W per m^2.

        This is computed by dividing the average
        power by the cross section area.

        Returns:
            float: the average power density in W per m^2.
        """
        return self.average_power / self.cross_section_area

    @property
    def peak_power_density(self) -> float:
        """The peak power density, in W per m^2.

        This is computed by dividing the peak
        power by the cross section area.

        Returns:
            float: the peak power density in W per m^2.
        """
        return self.peak_power / self.cross_section_area

    @property
    def energy_density(self) -> float:
        """The energy density, in J per m^2.

        This is computed by dividing the pulse energy
        by the cross section area.

        Returns:
            float: the energy density, in J per m^2.
        """
        return self.pulse_energy / self.cross_section_area

    @property
    def corrected_energy_density(self) -> float:
        """The corrected energty density, in J per m^2.

        This is done by correcting the energy density
        byu multiplying it by the fourth root
        of the reference number of pulses.

        Warning: this does not perform any check on wavelength.

        Returns:
            float: the corrected energy density, in J per m^2.
        """
        return self.energy_density * self.reference_number_pulses**0.25

    @property
    def mode(self) -> Mode:
        """The mode of the laser, depending on the pulse duration.

        Returns:
            Mode: the mode of the laser.
        """
        return get_test_by_pulse_duration(self.pulse_duration)

    def __str__(self):
        return f"""
Continuous: {self.continuous}
Wavelength: {format_value(self.wavelength)}m
Repetition rate: {format_value(self.repetition_rate)}Hz
Average power: {format_value(self.average_power)}W
Peak power: {format_value(self.peak_power)}W
Pulse duration: {format_value(self.pulse_duration)}s
Pulse energy: {format_value(self.pulse_energy)}J
Beam diameter: {format_value(self.beam_diameter)}m
Mode: {str(self.mode)}
Cross section area: {self.cross_section_area} m^2
Power density: {self.power_density} W/m^2
Peak power density: {self.peak_power_density} W/m^2
Energy density: {self.energy_density} J/m^2
Corrected energy density: {self.corrected_energy_density} J/m^2
Number of pulses in 10s: {self.reference_number_pulses}
"""

    def en207_analysis(self) -> List[Tuple[Mode, int]]:
        """Perform the EN207 analysis.

        If the mode of the laser is M, it only performs the
        continuous scale analysis.

        If the mode of the laser is anything but M, it
        perform both the continuous scale and pulsed
        scale analysis.

        Returns:
            List[Tuple[Mode, int]]: list of mode and scale number required for the mode.
        """
        scale_number_cw = continuous_scale_number(
            self.average_power, self.cross_section_area, self.wavelength
        )
        if self.mode == Mode.D:
            # The D is the only analysis to do
            return [
                (Mode.D, scale_number_cw),
            ]

        # Perform analysis for pulsed
        scale_number_pulsed = pulsed_scale_number(
            self.peak_power,
            self.pulse_energy,
            self.cross_section_area,
            self.pulse_duration,
            self.repetition_rate,
            self.wavelength,
        )

        return [(Mode.D, scale_number_cw), (self.mode, scale_number_pulsed)]

    def en208_analysis(self) -> int:
        """Perform the EN208 analysis.

        Depending on the pulse duration, the continuous or pulsed computation used used.

        Returns:
            int: scale number for EN208.
        """
        # Continuous
        if self.continuous or self.pulse_duration >= 1e-4:
            return continuous_scale_number_en208(
                self.average_power, self.cross_section_area, self.wavelength
            )

        # Pulsed
        return pulsed_scale_number_en208(
            self.peak_power,
            self.pulse_energy,
            self.cross_section_area,
            self.pulse_duration,
            self.repetition_rate,
            self.wavelength,
        )
