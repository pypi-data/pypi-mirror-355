# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Define entrypoints.
"""

import argparse

from lasersafety import DISCLAIMER, __version__
from lasersafety.laser import LaserBeam


def _create_parsers() -> argparse.ArgumentParser:
    """Create the parsers.

    Returns:
        argparse.ArgumentParser: the main parser.
    """
    parser = argparse.ArgumentParser(prog="lasersafety")

    parser.add_argument("--version", action="version", version=__version__)

    parser.add_argument(
        "-p",
        "--avg-power",
        type=float,
        help="Average power of the laser",
    )

    parser.add_argument(
        "-s",
        "--peak-power",
        type=float,
        help="Peak power of the laser",
    )

    parser.add_argument(
        "-r",
        "--rep-rate",
        type=float,
        help="Repetition rate of the laser",
    )

    parser.add_argument(
        "-t",
        "--pulse-duration",
        type=float,
        help="Pulse duration of the laser",
    )

    parser.add_argument(
        "-e",
        "--pulse-energy",
        type=float,
        help="Pulse energy of the laser",
    )

    parser.add_argument(
        "-w",
        "--wavelength",
        type=float,
        help="Wavelength of the laser",
    )

    parser.add_argument(
        "-d",
        "--beam-diameter",
        type=float,
        help="Beam diameter of the laser",
    )

    parser.add_argument(
        "--divergence",
        type=float,
        help="Beam divergence of the laser",
    )

    subparsers = parser.add_subparsers()

    en207_parser = subparsers.add_parser(
        "en207", help="Perform the computation for the EN207 standard"
    )
    en207_parser.set_defaults(func=en207)

    en208_parser = subparsers.add_parser(
        "en208", help="Perform the computation for the EN208 standard"
    )
    en208_parser.set_defaults(func=en208)

    return parser


def en207(args: argparse.Namespace):
    """EN207 analyis entrypoint.

    Args:
        args (argparse.Namespace): arguments passed to the command line.
    """
    laser = LaserBeam(
        wavelength=args.wavelength,
        repetition_rate=args.rep_rate,
        beam_diameter=args.beam_diameter,
        average_power=args.avg_power,
        pulse_duration=args.pulse_duration,
        pulse_energy=args.pulse_energy,
        divergence=args.divergence,
    )

    print(40 * "-")

    print("Laser information")
    print(laser)

    print(40 * "-")

    print("EN207 analysis\n")

    for mode, level in laser.en207_analysis():
        print(f"{laser.wavelength*1e9} nm", mode.value, f"LB{str(level)}")


def en208(args: argparse.Namespace):
    """EN208 analyis entrypoint.

    Args:
        args (argparse.Namespace): arguments passed to the command line.
    """
    laser = LaserBeam(
        wavelength=args.wavelength,
        repetition_rate=args.rep_rate,
        beam_diameter=args.beam_diameter,
        average_power=args.avg_power,
        pulse_duration=args.pulse_duration,
        pulse_energy=args.pulse_energy,
        divergence=args.divergence,
    )

    print(40 * "-")

    print("Laser information")
    print(laser)

    print(40 * "-")

    print("EN208 analysis\n")

    print(f"{laser.wavelength*1e9} nm", f"RB{str(laser.en208_analysis())}")


def main():
    """
    Main entrypoint.
    """
    parser = _create_parsers()

    args = parser.parse_args()

    print(DISCLAIMER)

    if hasattr(args, "func"):
        args.func(args)
    else:
        print("No command specified. Run with -h|--help to see the possible commands.")


if __name__ == "__main__":
    main()
