import math
from importlib.resources import files


import arcade

from space_collector.game.constants import RADAR_RADIUS
from space_collector.game.math import Matrix, Vector
from space_collector.viewer.animation import AnimatedValue, Animation, Step
from space_collector.viewer.utils import (
    map_coord_to_window_coord,
    hue_changed_texture,
    map_value_to_window,
)
from space_collector.viewer.constants import constants


class SpaceShip:
    image_path = ""

    def __init__(self, x: int, y: int, angle: int, team: int) -> None:
        self.team = team
        self.x = AnimatedValue(x)
        self.y = AnimatedValue(y)
        self.angle = AnimatedValue(angle)
        self.width = 100
        self.height = 100
        self.fire = False
        self.fire_angle = 0
        self.id = -1
        self.broken = False

    def setup(self) -> None:
        image_file = files("space_collector.viewer").joinpath(self.image_path)
        self.sprite = arcade.Sprite(
            path_or_texture=hue_changed_texture(
                image_file, constants.TEAM_HUES[self.team]
            )
        )
        self.sprite.width = self.width
        self.sprite.height = self.height

    def animate(self) -> None:
        self.sprite.angle = -int(self.angle.value - 90)
        self.sprite.position = map_coord_to_window_coord(self.x.value, self.y.value)

    def draw(self) -> None:
        self.animate()
        arcade.draw_sprite(self.sprite)

    def update(self, server_data: dict, duration: float) -> None:
        # logging.info(server_data)
        self.id = server_data["id"]
        self.broken = server_data["broken"]
        self.x.add_animation(
            Animation(
                start_value=self.x.value, end_value=server_data["x"], duration=duration
            )
        )
        self.y.add_animation(
            Animation(
                start_value=self.y.value, end_value=server_data["y"], duration=duration
            )
        )
        target_angle = server_data["angle"]
        best_start_angle = 0
        best_angle_diff = 1000
        for angle_offset in (-360, 0, 360):
            start_angle = self.angle.value + angle_offset
            angle_diff = abs(target_angle - start_angle)
            if angle_diff < best_angle_diff:
                best_angle_diff = angle_diff
                best_start_angle = start_angle
        self.angle.add_animation(
            Animation(
                start_value=best_start_angle, end_value=target_angle, duration=0.2
            )
        )
        if self.broken:
            self.sprite.width = self.width / 2
            self.sprite.height = self.height / 2
        else:
            self.sprite.width = self.width
            self.sprite.height = self.height


class Attacker(SpaceShip):
    image_path = "images/spaceships/attacker.png"

    def __init__(self, x: int, y: int, angle: int, team: int) -> None:
        super().__init__(x, y, angle, team)
        self.width = 30
        self.height = 30

    def setup(self) -> None:
        super().setup()
        self.lightning_length = AnimatedValue(0)
        self.lightning_alpha = AnimatedValue(0)
        image_file = files("space_collector.viewer").joinpath("images/high_energy.png")
        self.lightning_sprite = arcade.Sprite(
            path_or_texture=hue_changed_texture(
                image_file, constants.TEAM_HUES[self.team]
            )
        )
        self.lightning_sprite.width = 20
        self.lightning_sprite.height = 1

    def update(self, server_data: dict, duration: float) -> None:
        super().update(server_data, duration)
        self.fire = server_data["fire"]
        if self.fire:
            self.lightning_alpha.add_animations(
                initial_value=self.lightning_alpha.value,
                steps=[
                    Step(value=255, duration=0.05),
                    Step(value=255, duration=0.4),
                    Step(value=0, duration=0.05),
                ],
            )
            self.lightning_length.add_animations(
                initial_value=self.lightning_length.value,
                steps=[
                    Step(value=constants.HIGH_ENERGY_SPRITE_LENGTH, duration=0.25),
                    Step(value=0, duration=0.25),
                ],
            )
            self.fire_angle = server_data["fire_angle"]

    def animate(self) -> None:
        super().animate()
        self.lightning_sprite.angle = -int(self.fire_angle - 90)
        self.lightning_sprite.height = self.lightning_length.value + 1
        fire_angle = math.radians(self.fire_angle)
        radius = self.lightning_sprite.height // 2
        center_x, center_y = map_coord_to_window_coord(self.x.value, self.y.value)
        self.lightning_sprite.position = (
            center_x + radius * math.cos(fire_angle),
            center_y + radius * math.sin(fire_angle),
        )

    def draw(self) -> None:
        super().draw()
        arcade.draw_sprite(self.lightning_sprite)


class Collector(SpaceShip):
    image_path = "images/spaceships/collector.png"

    def __init__(self, x: int, y: int, angle: int, team: int) -> None:
        super().__init__(x, y, angle, team)
        self.width = 50
        self.height = 50

    def collected_planet_position(self) -> Vector:
        angle = math.radians(self.angle.value)
        offset = Vector([600, 0])
        rotation_matrix = Matrix(
            [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]]
        )
        rotated_offset = rotation_matrix @ offset
        return Vector([self.x.value, self.y.value]) + rotated_offset


class Explorator(SpaceShip):
    image_path = "images/spaceships/explorator.png"

    def __init__(self, x: int, y: int, angle: int, team: int) -> None:
        super().__init__(x, y, angle, team)
        self.width = 40
        self.height = 40
        self.max_radar_radius = map_value_to_window(RADAR_RADIUS)
        self.radar_color = list(constants.TEAM_COLORS[self.team])
        self.radar_color.append(15)

    def setup(self) -> None:
        super().setup()
        self.radar_radius = AnimatedValue(0)

    def update(self, server_data: dict, duration: float) -> None:
        super().update(server_data, duration)
        self.radar = server_data["radar"]
        if self.radar and not self.broken:
            self.radar_radius.add_animations(
                initial_value=self.max_radar_radius,
                steps=[
                    Step(value=self.max_radar_radius, duration=0.25),
                    Step(value=0, duration=0.001),
                ],
            )

    def draw(self) -> None:
        center = map_coord_to_window_coord(self.x.value, self.y.value)
        arcade.draw_circle_filled(*center, self.radar_radius.value, self.radar_color)
        super().draw()
