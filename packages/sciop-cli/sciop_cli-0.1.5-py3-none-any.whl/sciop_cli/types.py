from typing import Annotated

import humanize
from pydantic import AfterValidator


def _divisible_by_16kib(size: int) -> bool:
    if size < 0:
        return False
    return size % (16 * (2**10)) == 0


def _validate_size(size: int) -> int:
    assert _divisible_by_16kib(size), "Piece size must be divisible by 16kib and positive"
    return size


PieceSize = Annotated[int, AfterValidator(_validate_size)]


class Size(int):
    def __str__(self) -> str:
        return humanize.naturalsize(int(self), binary=True)

    def __rmul__(self, factor: int) -> "Size":
        return Size(int(self) * factor)

    def __mul__(self, other: int) -> "Size":
        return Size(int(self) * other)
