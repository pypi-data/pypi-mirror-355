"""Main class used to manage DYM files."""

from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path

import xarray as xr

from dymfile.core import dymfile_loading, dymfile_tools


__all__ = ["Dymfile"]


@dataclass
class Dymfile:
    """
    Represents a Dymfile object.

    This class provides methods for initializing a Dymfile object, loading data from
    different sources, and plotting the data and mask.

    Attributes
    ----------
    data : xr.DataArray
        An xarray DataArray representing the data.
    mask : xr.DataArray
        An xarray DataArray representing the mask.

    Methods
    -------
    from_filepath(filepath: str, delta_time: int = 30, name: str | None = None,
                  units: str | None = None, normalize_longitude: bool = False,
                  date_formating: bool = True) -> Dymfile
        Load a Dymfile from a filepath.
    from_buffer(buffer: bytes, delta_time: int = 30, name: str | None = None,
                  units: str | None = None, normalize_longitude: bool = False,
                  date_formating: bool = True) -> Dymfile
        Load a Dymfile from a buffer of bytes.

    Parameters
    ----------
    data : xr.DataArray
        An xarray DataArray representing the data.
    mask : xr.DataArray
        An xarray DataArray representing the mask.
    normalize_longitude : bool, optional
        Whether to normalize the longitude. Defaults to False.

    Examples
    --------
    >>> import xarray as xr
    >>> from dymfile import Dymfile

    >>> # Create data and mask xarray DataArrays
    >>> data = xr.DataArray(...)
    >>> mask = xr.DataArray(...)

    >>> # Create a Dymfile object
    >>> dymfile = Dymfile(data, mask, normalize_longitude=True)

    >>> # Load a Dymfile from a filepath
    >>> filepath = "/path/to/dymfile.nc"
    >>> dymfile_from_file = Dymfile.from_filepath(filepath, normalize_longitude=True)
    """

    data: xr.DataArray
    mask: xr.DataArray
    normalize_longitude: bool = False

    def __post_init__(self: Dymfile) -> None:
        """
        Post-initialization method to ensure that the data and mask are xarray DataArrays.

        Raises
        ------
        TypeError
            If `data` or `mask` is not an instance of xarray.DataArray.
        """
        if not isinstance(self.data, xr.DataArray):
            raise TypeError("data must be an instance of xarray.DataArray")
        if not isinstance(self.mask, xr.DataArray):
            raise TypeError("mask must be an instance of xarray.DataArray")

        if self.normalize_longitude:
            with xr.set_options(keep_attrs=True):
                self.data = dymfile_tools.normalize_longitude(self.data)
                self.mask = dymfile_tools.normalize_longitude(self.mask)

    @classmethod
    def from_filepath(
        cls: Dymfile,
        filepath: str,
        delta_time: int = 30,
        *,
        name: str | None = None,
        units: str | None = None,
        normalize_longitude: bool = False,
        date_formating: bool = True,
    ) -> Dymfile:
        """
        Load a Dymfile from a filepath.

        This method is a classmethod that registers the `_from_filepath` implementation
        as a handler for loading a Dymfile from a filepath. It reads the data, mask,
        time vector, longitude, and latitude from the file using the
        `dymfile_loading.loading()` function. Then, it formats the data and mask using
        the `dymfile_loading.format_data()` function. Finally, it creates and returns a
        Dymfile object with the loaded data and mask.
        """
        file = Path(filepath)
        if name is None:
            name = file.stem
        with file.open("rb") as file:
            data, mask, time_vector, xlon, ylat = dymfile_loading.loading(
                file, delta_time=delta_time, date_formating=date_formating
            )
        data, mask = dymfile_loading.format_data(
            data, mask, time_vector, xlon, ylat, name, units
        )
        return Dymfile(data, mask, normalize_longitude=normalize_longitude)

    @classmethod
    def from_buffer(
        cls: Dymfile,
        buffer: bytes,
        delta_time: int = 30,
        *,
        name: str | None = None,
        units: str | None = None,
        normalize_longitude: bool = False,
        date_formating: bool = True,
    ) -> Dymfile:
        """
        Load a Dymfile from a buffer of bytes.

        This method is a classmethod that registers the `_from_buffer` implementation as
        a handler for loading a Dymfile from a buffer of bytes. It reads the data, mask,
        time vector, longitude, and latitude from the buffer using the
        `dymfile_loading.loading()` function. Then, it formats the data and mask using
        the `dymfile_loading.format_data()` function. Finally, it creates and returns a
        Dymfile object with the loaded data and mask.

        """
        if name is None:
            name = "Dymfile"
        with io.BytesIO(buffer) as buffer:
            data, mask, time_vector, xlon, ylat = dymfile_loading.loading(
                buffer, delta_time=delta_time, date_formating=date_formating
            )
        data, mask = dymfile_loading.format_data(
            data, mask, time_vector, xlon, ylat, name, units
        )
        return Dymfile(data, mask, normalize_longitude=normalize_longitude)
