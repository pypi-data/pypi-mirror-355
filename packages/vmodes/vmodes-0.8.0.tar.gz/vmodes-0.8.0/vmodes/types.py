#
# VModeS - vectorized decoding of Mode S and ADS-B data
#
# Copyright (C) 2020-2025 by Artur Wroblewski <wrobell@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import dataclasses as dtc
import numpy as np
import numpy.typing as npt
import typing as tp
from numpy.ma import MaskedArray

from .decoder._data import PosDecoderCtx

T = tp.TypeVar('T', bound=np.generic)

# define aliases for basic types to support static type analysis; these are
# for a convenience
# NOTE: waiting for shape support i.e. np.ndarray[shape, dtype]

# should be type alias, but MaskedArray not annotated yet
# type MArray[T] = MaskedArray[tp.Any, np.dtype[T]]
class MArray(MaskedArray[tp.Any, np.dtype[T]]):
    def compressed(self) -> npt.NDArray[T]:
        return super().compressed()

UInt8: tp.TypeAlias = npt.NDArray[np.uint8]
UInt24: tp.TypeAlias = npt.NDArray[np.uint32]
UInt32: tp.TypeAlias = npt.NDArray[np.uint32]
UInt64: tp.TypeAlias = npt.NDArray[np.uint64]
Int32: tp.TypeAlias = npt.NDArray[np.int32]
Int64: tp.TypeAlias = npt.NDArray[np.int64]
BIndex: tp.TypeAlias = npt.NDArray[np.bool_]

MaUInt8: tp.TypeAlias = MArray[np.uint8]
MaUInt24: tp.TypeAlias = MArray[np.uint32]
MaUInt32: tp.TypeAlias = MArray[np.uint32]
String: tp.TypeAlias = MArray[np.str_]

# scalar types
SCprNl: tp.TypeAlias = np.int32
SCoordinate: tp.TypeAlias = np.float64
SCprCoordinate: tp.TypeAlias = np.float64
SAltitude: tp.TypeAlias = np.float32
SCategory: tp.TypeAlias = np.uint8

# vector types
Time: tp.TypeAlias = npt.NDArray[np.float64]
Message: tp.TypeAlias = UInt8
DownlinkFormat: tp.TypeAlias = UInt8
TypeCode: tp.TypeAlias = MaUInt8
Icao: tp.TypeAlias = MaUInt24
Category: tp.TypeAlias = MArray[SCategory]  # TODO: 2 dimensions
Altitude: tp.TypeAlias = MArray[SAltitude]
CprFormat: tp.TypeAlias = UInt8
CprCoordinate: tp.TypeAlias = npt.NDArray[SCprCoordinate]
CprNl: tp.TypeAlias = npt.NDArray[SCprNl]
Coordinate: tp.TypeAlias = npt.NDArray[SCoordinate]
Position: tp.TypeAlias = MArray[SCoordinate]  # TODO: 2 dimensions

@dtc.dataclass(frozen=True, slots=True)
class PositionData:
    """
    Result of decoding of aircraft position.

    :var ctx: Position decoding context.
    :var position: Aircraft position coordinates.
    :var all_position: Aircraft position coordinates, including carried
        over data.
    """
    ctx: PosDecoderCtx
    position: Position
    prev_position: Position

class CPosition(tp.TypedDict):
    # used on Cython level and in unit tests
    longitude: float
    latitude: float
    is_valid: bool

# vim: sw=4:et:ai
