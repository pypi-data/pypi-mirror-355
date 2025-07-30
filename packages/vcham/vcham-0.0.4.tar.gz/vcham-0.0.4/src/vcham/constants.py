"""
This module contains physical constants and conversion factors.

.. data:: H

   Planck's constant (J·s)

.. data:: C

   Speed of light in vacuum (m/s)

.. data:: AU_TO_J

   Hartree to Joule conversion factor (J)

.. data:: CM1_TO_AU

   Conversion factor from wavenumbers (cm^-1) to atomic units

.. data:: AU_TO_EV

   Conversion factor from atomic units to electron volts (eV)
"""

# Planck's constant in Joule seconds (J·s)
H = 6.62607015e-34

# Speed of light in vacuum in meters per second (m/s)
C = 299792458.0

# Hartree to Joule conversion factor (J)
AU_TO_J = 4.3597447222071e-18

# Conversion factor from wavenumbers (cm^-1) to atomic units
CM1_TO_AU = (H * C * 100.0) / AU_TO_J

# Conversion factor from atomic units to electron volts (eV)
AU_TO_EV = 27.211386245988

# Conversion factor from bohr to angstrom
BOHR_TO_ANGSTROM = 0.52917721067
# Conversion factor from angstrom to bohr
ANGSTROM_TO_BOHR = 1.0 / BOHR_TO_ANGSTROM