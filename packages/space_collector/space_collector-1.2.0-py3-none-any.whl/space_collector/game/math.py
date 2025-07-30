from __future__ import annotations

from math import hypot
from collections.abc import Iterable


class Vector:
    def __init__(self, data: Iterable) -> None:
        self.data = list(data)

    def __repr__(self) -> str:
        return "Vector(" + ", ".join(str(item) for item in self.data) + ")"

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __add__(self, other: Vector) -> Vector:
        if isinstance(other, Vector):
            return Vector(s + o for s, o in zip(self, other))
        raise NotImplementedError

    def __sub__(self, other: Vector) -> Vector:
        if isinstance(other, Vector):
            return Vector(s - o for s, o in zip(self, other))
        raise NotImplementedError

    def __mul__(self, other: int | float) -> Vector:
        if isinstance(other, (int, float)):
            return Vector(s * other for s in self)
        raise NotImplementedError

    def __truediv__(self, other: int | float) -> Vector:
        if isinstance(other, (int, float)):
            return Vector(s / other for s in self)
        raise NotImplementedError

    def length(self) -> float:
        return hypot(*self.data)

    def dot(self, other: Vector) -> float:
        if isinstance(other, Vector):
            return sum(s * o for s, o in zip(self, other))
        raise NotImplementedError

    @property
    def x(self):
        return self.data[0]

    @property
    def y(self):
        return self.data[1]

    @property
    def z(self):
        return self.data[2]


class Matrix:
    def __init__(self, data: list) -> None:
        """First dimension in data is rows: [[a,b],[c,d]] => [a,b] is first row."""
        self.data = data

    def __getitem__(self, indices_tuple: tuple[int]):
        data = self.data
        indices = list(indices_tuple)
        while indices:
            data = data[indices.pop(0)]
        return data

    def __matmul__(self, other: Vector | Matrix) -> Vector | Matrix:
        assert isinstance(other, Vector)  # Matrix @ Matrix not implemented yet
        result = Vector([])
        for index in range(len(other)):
            result.data.append(
                sum(mat * vec for mat, vec in zip(self.data[index], other))
            )
        return result


def distance_point_to_segment(start: Vector, end: Vector, point: Vector) -> float:
    """Distance between point and segment [start end]."""
    start_to_end = end - start
    start_to_point = point - start
    segment_length = start_to_end.length()
    unit_start_to_end = start_to_end / segment_length
    unit_start_to_point = start_to_point / segment_length
    t = unit_start_to_end.dot(unit_start_to_point)
    # clamp orthogonal projection to segment boundaries
    if t < 0:
        t = 0
    elif t > 1:
        t = 1
    nearest_point_from_point = start_to_end * t + start
    return (nearest_point_from_point - point).length()
