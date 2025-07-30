# sourcery skip: require-return-annotation
"""Tool functions."""

from __future__ import annotations

import datetime
import itertools
import struct
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import io
    import xarray as xr


class LabelsCoordinates:
    """Names used by the Dymfile format for coordinates."""

    latitude = "latitude"
    longitude = "longitude"
    time = "time"


def get_date_sea(ndat: float) -> datetime.date:
    """
    Calculate the date in Seapodym format. Integer part is year and floating part is day
    of the year.

    Parameters
    ----------
    ndat : float
        The input date in Seapodym format.

    Returns
    -------
    datetime.date
        The calculated date in datetime.date format.
    """
    year = int(ndat)
    days = int((ndat - year) * 365)
    return datetime.date(year, 1, 1) + datetime.timedelta(days=days - 1)


def year_month_sea(ndat: float) -> list[int]:
    """
    Calculate the date in Seapodym format. Return year and month in a list.

    Parameters
    ----------
    ndat : float
        The input date in Seapodym format.

    Returns
    -------
    list[int]
        A list containing the year and month.
    """
    year = int(ndat)
    days = int((ndat - year) * 365)
    date = datetime.date(year, 1, 1) + datetime.timedelta(days=days - 1)
    month = date.month
    return [year, month]


def gen_monthly_dates(t0: list[int], tfin: list[int]) -> np.ndarray:
    """
    Generate monthly dates between t0 and tfin.

    Parameters
    ----------
    t0 : list[int]
        The start date [year, month].
    tfin : list[int]
        The end date [year, month].

    Returns
    -------
    np.ndarray
        An array of monthly dates.
    """
    dates = [
        datetime.date(year, month, 15)
        for year, month in itertools.product(
            range(t0[0], tfin[0] + 1), range(t0[1], tfin[1] + 1)
        )
    ]
    return np.array(dates, dtype="datetime64")


def iter_unpack_numbers(
    buf_format: str, buffer: io.BufferedReader | io.BytesIO
) -> np.ndarray:
    """
    Unpack numbers from a binary buffer using the specified format.

    Parameters
    ----------
    buf_format : str
        The format string.
    buffer : io.BufferedReader | io.BytesIO
        The binary buffer to unpack from.

    Returns
    -------
    np.ndarray
        An array of unpacked numbers.
    """
    result = struct.iter_unpack(buf_format, buffer)
    return np.array([x[0] for x in result])


def normalize_longitude(data: xr.DataArray) -> xr.DataArray:
    """
    Normalizes the longitude values in the given DataArray.
    Longitude will be inside [-180, 180] degrees.

    Parameters
    ----------
    data : xr.DataArray
        The DataArray containing longitude values.

    Returns
    -------
    xr.DataArray
        The DataArray with normalized longitude values.
    """
    data = data.assign_coords(
        {
            LabelsCoordinates.longitude: (
                ((data[LabelsCoordinates.longitude] + 180) % 360) - 180
            )
        }
    )
    return data.sortby(list(data.coords.keys()))


def generate_coordinates_attrs(data: xr.DataArray) -> xr.DataArray:
    """Generate the coordinates attributes for the data array."""
    data.coords[LabelsCoordinates.longitude] = data[
        LabelsCoordinates.longitude
    ].assign_attrs(
        standard_name="longitude",
        long_name="longitude",
        units="degrees_east",
    )
    data.coords[LabelsCoordinates.latitude] = data[
        LabelsCoordinates.latitude
    ].assign_attrs(
        standard_name="latitude",
        long_name="latitude",
        units="degrees_north",
    )
    return data


def generate_name(
    data: xr.DataArray, name: str, units: str | None = None
) -> xr.DataArray:
    """Generate the name attributes for the data array."""
    data.name = name
    attrs = {
        "standard_name": name,
        "long_name": name,
    }
    if units is not None:
        attrs["units"] = units
    data.attrs.update(attrs)
    return data
