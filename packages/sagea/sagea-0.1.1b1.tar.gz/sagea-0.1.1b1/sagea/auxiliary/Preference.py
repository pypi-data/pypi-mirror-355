from enum import Enum


class GeoConstants:
    density_earth = 5517  # unit[kg/m3]
    radius_earth = 6378136.3  # unit[m]
    GM = 3.9860044150E+14  # unit[m3/s2]

    """gas constant for dry air"""
    Rd = 287.00
    # Rd = 287.06

    '''gravity constant g defined by WMO'''
    g_wmo = 9.80665
    # g_wmo = 9.7

    ''' water density'''
    density_water = 1000.0
    # density_water = 1025.0


class SHNormalization(Enum):
    full = 1


class PhysicalDimensions(Enum):
    Dimensionless = 0
    EWH = 1
    Pressure = 2
    Density = 3
    Geoid = 4
    Gravity = 5
    HorizontalDisplacementEast = 6
    HorizontalDisplacementNorth = 7
    VerticalDisplacement = 8
