# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Utility functions to validate user inputs.
"""

from typing import Union

import numpy as np


def validate_wavelength_en207(wavelength: Union[float, int]) -> None:
    """Check that the wavelength is compatible with the EN207 standard.

    Args:
        wavelength (Union[float, int]): the wavelength to validate, in m.

    Raises:
        ValueError: if the wavelength is not a float or an int.
        ValueError: if the wavelength is outside the range 180 nm - 1 mm.
    """
    # Check type
    if not isinstance(wavelength, (float, int)):
        raise ValueError("wavelength should be a float (or int)")

    # Check value per EN207 standard
    if wavelength < 180e-9 or wavelength > 1e-3:
        raise ValueError(
            f"EN207 standards is only valid for wavelengths between 180nm and 1mm (got {wavelength})"
        )


def validate_wavelength_en208(wavelength: Union[float, int]) -> None:
    """Check that the wavelength is compatible with the EN208 standard.

    Args:
        wavelength (Union[float, int]): the wavelength to validate, in m.

    Raises:
        ValueError: if the wavelength is not a float or an int.
        ValueError: if the wavelength is outside the range 400 nm - 700 nm.
    """
    # Check type
    if not isinstance(wavelength, (float, int)):
        raise ValueError("wavelength should be a float (or int)")

    # Check value per EN208 standard
    if wavelength < 400e-9 or wavelength > 700e-9:
        raise ValueError(
            f"EN208 standards is only valid for wavelengths between 400nm and 700mm (got {wavelength})"
        )


def validate_strictly_positive_number(
    number: Union[float, int], parameter_name="parameter"
) -> None:
    """Check that the input number is stritcly positive.

    Args:
        number (Union[float, int]): the number to validate.
        parameter_name (str, optional): the parameter, for raising exceptions. Defaults to "parameter".

    Raises:
        ValueError: if the number is not a float or an int.
        ValueError: if the number is lower or equal to 0.
    """
    # Check type
    if not isinstance(number, (float, int)):
        raise ValueError(f"{parameter_name} should be a float or int")

    # Check value is strictly positive
    if number <= 0:
        raise ValueError(f"{parameter_name} should be striclty positive (got {number})")


def format_value(value: float | int) -> str:
    """Format a scientific value with scientific prefixes.

    It is compatible with prefixes from femto to Giga.

    Args:
        value (float | int): the value to format.

    Raises:
        ValueError: if the input value is not a float or an int.

    Returns:
        str: the formatted scientific value.
    """
    if not isinstance(value, (float, int)):
        raise ValueError("format_value can only be applied to a float or an int")

    if value == 0:
        return "0"

    magnitude = np.log10(np.abs(value))

    magnitude_suffix = ["G", "M", "k", "", "m", "μ", "n", "p", "f"]

    for i, magnitude_threshold in enumerate([9, 6, 3, 0, -3, -6, -9, -12, -15]):
        if magnitude >= magnitude_threshold:
            return str(value * 10 ** (-magnitude_threshold)) + " " + magnitude_suffix[i]

    return str(value)
