"""All functions used for loading DYM files."""

from __future__ import annotations

import itertools
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from dymfile.core import dymfile_tools
from dymfile.core.dymfile_tools import LabelsCoordinates

if TYPE_CHECKING:
    import io
    from collections.abc import Iterable

__all__ = ["loading", "format_data"]

DYM_INVALID_VALUE = -999
NB_DAY_MONTHLY = 30


@dataclass
class HeaderData:
    """
    Represents header data for a file.

    Attributes
    ----------
    nlon : int
        The number of longitude points.
    nlat : int
        The number of latitude points.
    nlevel : int
        The number of vertical levels.
    t0_file : float
        The initial time of the file.
    tfin_file : float
        The final time of the file.
    """

    nlon: int
    nlat: int
    nlevel: int
    t0_file: float
    tfin_file: float


def read_header(
    file: io.BufferedReader | io.BytesIO,
) -> tuple[HeaderData, np.ndarray, np.ndarray]:
    """
    Read informations in the Dymfile header.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        The file to read header information from.

    Returns
    -------
    tuple[HeaderData, np.ndarray, np.ndarray]
        A tuple containing header data, xlon, and ylat.
    """
    file.read(4)
    struct.unpack("i", file.read(4))
    struct.unpack("f", file.read(4))
    struct.unpack("f", file.read(4))

    nlon = struct.unpack("i", file.read(4))[0]
    nlat = struct.unpack("i", file.read(4))[0]
    nlevel = struct.unpack("i", file.read(4))[0]
    t0_file = struct.unpack("f", file.read(4))[0]
    tfin_file = struct.unpack("f", file.read(4))[0]

    header_data = HeaderData(nlon, nlat, nlevel, t0_file, tfin_file)
    xlon = np.zeros((header_data.nlat, header_data.nlon), dtype=np.float32)
    ylat = np.zeros((header_data.nlat, header_data.nlon), dtype=np.float32)

    return header_data, xlon, ylat


def init_data(
    file: io.BufferedReader | io.BytesIO,
    header_data: HeaderData,
    xlon: np.ndarray,
    ylat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Initialize coordinates and mask.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        The file to read data from.
    header_data : HeaderData
        Header data containing information about the data.
    xlon : np.ndarray
        Array to store longitude data.
    ylat : np.ndarray
        Array to store latitude data.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        A tuple containing xlon, ylat, time_vect, and mask arrays.
    """
    for i in range(header_data.nlat):
        xlon[i, :] = dymfile_tools.iter_unpack_numbers(
            "f", file.read(4 * header_data.nlon)
        )
    for i in range(header_data.nlat):
        ylat[i, :] = dymfile_tools.iter_unpack_numbers(
            "f", file.read(4 * header_data.nlon)
        )
    time_vect = dymfile_tools.iter_unpack_numbers(
        "f", file.read(4 * header_data.nlevel)
    )
    mask = np.zeros((header_data.nlat, header_data.nlon), dtype=np.int32)
    for i in range(header_data.nlat):
        mask[i, :] = dymfile_tools.iter_unpack_numbers(
            "i", file.read(4 * header_data.nlon)
        )
    return xlon, ylat, time_vect, mask


def fill_data(
    file: io.BufferedReader | io.BytesIO,
    header_data: HeaderData,
) -> np.ndarray:
    """
    Fill the data array.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        The file to read data from.
    header_data : HeaderData
        Header data containing information about the data.

    Returns
    -------
    np.ndarray
        The filled data array.
    """
    data = np.zeros(
        (header_data.nlevel, header_data.nlat, header_data.nlon),
        dtype=np.float32,
    )
    iterator = itertools.product(range(header_data.nlevel), range(header_data.nlat))
    for time, lat in iterator:
        result = struct.iter_unpack("f", file.read(4 * header_data.nlon))
        data[time, lat, :] = np.array([x[0] for x in result])
    data[data == DYM_INVALID_VALUE] = np.nan
    return data


def format_date(delta_time: int, header_data: HeaderData) -> np.ndarray:
    """
    Transform the date (float) into datetime format.

    Parameters
    ----------
    delta_time : int
        The time delta.
    header_data : HeaderData
        Header data containing information about the data.

    Returns
    -------
    np.ndarray
        An array of formatted dates.
    """
    if delta_time == NB_DAY_MONTHLY:
        dates = dymfile_tools.gen_monthly_dates(
            dymfile_tools.year_month_sea(header_data.t0_file),
            dymfile_tools.year_month_sea(header_data.tfin_file),
        )
    else:
        dates = dymfile_tools.get_date_sea(header_data.t0_file) + np.arange(
            0, header_data.nlevel * delta_time, delta_time
        )
    return np.array(dates, dtype="datetime64")


def loading(
    file: io.BufferedReader | io.BytesIO,
    *,
    date_formating: bool = True,
    delta_time: int = 30,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Wrapper function. Load all the data into numpy format.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        The file to read data from.
    date_formating : bool, optional
        Whether to format dates, by default True.
    delta_time : int, optional
        The time delta, by default 30.

    Returns
    -------
    tuple
        A tuple containing data, mask, time_vector, xlon, and ylat.
    """
    header_data, xlon, ylat = read_header(file)
    xlon, ylat, time_vector, mask = init_data(file, header_data, xlon, ylat)
    if date_formating:
        time_vector = format_date(delta_time, header_data)
    data = fill_data(file, header_data)

    return data, mask, time_vector, xlon, ylat


def format_data(
    data: np.ndarray,
    mask: np.ndarray,
    time_vector: Iterable,
    xlon: Iterable,
    ylat: Iterable,
    name: str,
    units: str,
) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Transform the numpy data into Xarray format.

    Parameters
    ----------
    data : np.ndarray
        The data array.
    mask : np.ndarray
        The mask array.
    time_vector : np.ndarray
        The time vector.
    xlon : np.ndarray
        The xlon array.
    ylat : np.ndarray
        The ylat array.
    name : str
        The name of the data.
    units : str
        The units of the data.

    Returns
    -------
    xr.DataArray
        The formatted data as an Xarray DataArray.
    xr.DataArray
        The formatted mask as an Xarray DataArray.
    """
    ylat = ylat[:, 0]
    xlon = xlon[0, :]
    time_vector = np.array(time_vector, dtype="datetime64[ns]")

    mask = xr.DataArray(
        mask,
        dims=(LabelsCoordinates.latitude, LabelsCoordinates.longitude),
        coords={LabelsCoordinates.latitude: ylat, LabelsCoordinates.longitude: xlon},
        name="mask",
    )
    data = xr.DataArray(
        data,
        dims=("time", LabelsCoordinates.latitude, LabelsCoordinates.longitude),
        coords={
            "time": time_vector,
            LabelsCoordinates.latitude: ylat,
            LabelsCoordinates.longitude: xlon,
        },
    )
    data: xr.DataArray = xr.where(mask == 0, np.nan, data)
    data = data.transpose(
        "time", LabelsCoordinates.latitude, LabelsCoordinates.longitude
    )
    data = data.sortby(
        ["time", LabelsCoordinates.latitude, LabelsCoordinates.longitude]
    )
    mask = mask.sortby([LabelsCoordinates.latitude, LabelsCoordinates.longitude])

    data = dymfile_tools.generate_coordinates_attrs(data)
    data = dymfile_tools.generate_name(data, name, units)
    mask = dymfile_tools.generate_coordinates_attrs(mask)
    mask = dymfile_tools.generate_name(
        mask,
        name="mask",
        units="0 : land, 1 : 1st layer, 2 : 2nd layer, 3 : 3rd layer",
    )

    return data, mask
