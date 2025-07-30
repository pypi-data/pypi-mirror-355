# LaserSafety

<a href='https://lasersafety.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/lasersafety/badge/?version=latest' alt='Documentation Status' />
</a>
<a href="https://github.com/qosst/lasersafety/blob/main/LICENSE"><img alt="Github - License" src="https://img.shields.io/github/license/qosst/lasersafety"/></a>
<a href="https://github.com/qosst/lasersafety/releases/latest"><img alt="Github - Release" src="https://img.shields.io/github/v/release/qosst/lasersafety"/></a>
<a href="https://pypi.org/project/lasersafety/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/lasersafety"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/pylint-dev/pylint"><img alt="Linting with pylint" src="https://img.shields.io/badge/linting-pylint-yellowgreen"/></a>
<a href="https://mypy-lang.org/"><img alt="Checked with mypy" src="https://www.mypy-lang.org/static/mypy_badge.svg"></a>
<a href="https://img.shields.io/pypi/pyversions/lasersafety">
    <img alt="Python Version" src="https://img.shields.io/pypi/pyversions/qosst-core">
</a>
<img alt="Coverage coverage" src=".coverage_badge.svg" />
<img alt="Docstr coverage" src=".docs_badge.svg" />
</center>
<hr/>


The goal of this project is to perform the computations related to the EN207 and EN208 standards to choose eyewear. For instance, if you have a 3 W 1550 nm laser, producing 50 picosecond pulses at a rate of 80 MHz. The accessible beam diameter is 2 mm. This library makes it as simple as 

```
lasersafety -p 3 -r 80e6 -t 50e-12 -w 1550e-9 -d 2e-3 en207
This code is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

In particular, you should ALWAYS check the results provided by this code before using them for
actual laser safety.

----------------------------------------
Laser information

Continuous: False
Wavelength: 1.55 μm
Repetition rate: 80.0 MHz
Average power: 3.0 W
Peak power: 750.0 W
Pulse duration: 50.0 ps
Pulse energy: 37.5 nJ
Beam diameter: 2.0 mm
Mode: M
Cross section area: 3.141592653589793e-06 m^2
Power density: 954929.6585513721 W/m^2
Peak power density: 238732414.63784304 W/m^2
Energy density: 0.011936620731892151 J/m^2
Corrected energy density: 2.007492316738256 J/m^2
Number of pulses in 10s: 800000000.0

----------------------------------------
EN207 analysis

1550.0 nm D LB3
1550.0 nm M LB1
```

Meaning that we require D LB3 + M LB1 at 1550 nm.

## Disclaimer

This work results from my own understanding of these standards. While I believe that I have understood the principles of the computation, I may be wrong and errors may have been introduced in transcripting this understanding into code.

All the results from this package should be checked by trained and competent personal, and used at your own risk. I decline any responsibility and provide no warranty on my program.

## Documentation

The documentation of this package is available at [https://lasersafety.readthedocs.io](https://lasersafety.readthedocs.io).