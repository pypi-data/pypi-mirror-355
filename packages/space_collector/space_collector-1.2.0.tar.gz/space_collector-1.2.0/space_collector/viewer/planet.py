import logging
import random
from importlib.resources import files

import arcade

from space_collector.viewer.animation import AnimatedValue, Animation
from space_collector.viewer.constants import constants
from space_collector.viewer.spaceship import SpaceShip
from space_collector.viewer.utils import (
    hue_changed_texture,
    map_coord_to_window_coord,
    find_image_files,
)


COLLECTED_SIZE = 20


class Planet:
    def __init__(
        self, x: int, y: int, id_: int, team: int, spaceships: list[SpaceShip]
    ) -> None:
        self.team = team
        self.x = AnimatedValue(x)
        self.y = AnimatedValue(y)
        self.size = AnimatedValue(COLLECTED_SIZE)
        self.id = id_
        self.saved = False
        self.collected_by = -1
        self.spaceships = spaceships
        images = find_image_files("images/planets")
        self.image_path = images[id_ % len(images)]
        logging.info("planet %d, %d", x, y)

    def setup(self) -> None:
        image_file = files("space_collector.viewer").joinpath(self.image_path)
        self.sprite = arcade.Sprite(
            path_or_texture=hue_changed_texture(
                image_file, constants.TEAM_HUES[self.team]
            )
        )
        self.sprite.width = random.randint(30, 70)
        self.sprite.height = self.sprite.width

    def animate(self) -> None:
        if self.saved:
            return
        self.sprite.position = map_coord_to_window_coord(self.x.value, self.y.value)
        self.sprite.width = self.size.value
        self.sprite.height = self.size.value

    def draw(self) -> None:
        if self.saved:
            return
        self.animate()
        arcade.draw_circle_outline(
            self.sprite.position[0],
            self.sprite.position[1],
            self.size.value // 2 + 2,
            (*constants.TEAM_COLORS[self.team], 150),
            4,
        )
        arcade.draw_sprite(self.sprite)

    def update(self, server_data: dict, duration: float) -> None:
        if self.saved:
            return
        self.collected_by = server_data["collected_by"]
        self.saved = server_data["saved"]
        if self.collected_by == -1:
            self.x.add_animation(
                Animation(
                    start_value=self.x.value,
                    end_value=server_data["x"],
                    duration=duration,
                )
            )
            self.y.add_animation(
                Animation(
                    start_value=self.y.value,
                    end_value=server_data["y"],
                    duration=duration,
                )
            )
            if self.size.value == COLLECTED_SIZE:
                self.size.add_animation(
                    Animation(
                        start_value=self.size.value,
                        end_value=server_data["size"],
                        duration=1,
                    )
                )

        else:  # collected
            spaceship = None
            for s in self.spaceships:
                if s.id == self.collected_by:
                    spaceship = s
                    break
            if spaceship is None:
                logging.error("Collector not found: %d", self.collected_by)
            else:
                position = spaceship.collected_planet_position()
                self.x.add_animation(
                    Animation(
                        start_value=self.x.value,
                        end_value=position.x,
                        duration=duration,
                    )
                )
                self.y.add_animation(
                    Animation(
                        start_value=self.y.value,
                        end_value=position.y,
                        duration=duration,
                    )
                )

            if self.size.value == server_data["size"]:
                self.size.add_animation(
                    Animation(
                        start_value=self.size.value,
                        end_value=COLLECTED_SIZE,
                        duration=0.2,
                    )
                )
