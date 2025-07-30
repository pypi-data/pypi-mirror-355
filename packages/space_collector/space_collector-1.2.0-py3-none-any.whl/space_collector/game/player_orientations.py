from dataclasses import dataclass

from space_collector.game.math import Matrix, Vector
from space_collector.game.constants import MAP_DIMENSION


@dataclass
class PlayerOrientation:
    base_position: tuple[int, int]
    angle: int
    matrix: Matrix

    def rotate_around_base(self, vector: Vector) -> Vector:
        base_vector = Vector(self.base_position)
        rotated_vector = self.matrix @ Vector([vector.x, vector.y])
        return base_vector + rotated_vector


player_orientations = [
    PlayerOrientation(
        base_position=(MAP_DIMENSION // 2, 0), angle=90, matrix=Matrix([[1, 0], [0, 1]])
    ),
    PlayerOrientation(
        base_position=(0, MAP_DIMENSION // 2), angle=0, matrix=Matrix([[0, 1], [-1, 0]])
    ),
    PlayerOrientation(
        base_position=(MAP_DIMENSION // 2, MAP_DIMENSION),
        angle=270,
        matrix=Matrix([[-1, 0], [0, -1]]),
    ),
    PlayerOrientation(
        base_position=(MAP_DIMENSION, MAP_DIMENSION // 2),
        angle=180,
        matrix=Matrix([[0, -1], [1, 0]]),
    ),
]
