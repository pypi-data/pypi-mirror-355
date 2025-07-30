import random
from importlib.resources import files
from time import perf_counter

import arcade

from space_collector.viewer.animation import AnimatedValue, Animation, Step
from space_collector.viewer.constants import constants
from space_collector.viewer.utils import random_sprite


class Comet:
    FADE_IN_DURATION = 0.3

    def __init__(self) -> None:
        self.sprite = arcade.Sprite(
            files("space_collector.viewer").joinpath("images/comet.png")
        )
        self.x = AnimatedValue(
            random.randint(constants.SCORE_WIDTH, constants.SCREEN_WIDTH)
        )
        self.y = AnimatedValue(random.randint(0, constants.SCREEN_HEIGHT))
        self.alpha = AnimatedValue(0)
        self.new_trajectory()

    def new_trajectory(self) -> None:
        self.duration = random.random() * 2 + 2 * self.FADE_IN_DURATION
        self.start_time = perf_counter()

        self.x.add_animation(
            Animation(
                start_value=self.x.value,
                end_value=random.randint(constants.SCORE_WIDTH, constants.SCREEN_WIDTH),
                duration=self.duration,
            )
        )
        self.y.add_animation(
            Animation(
                start_value=self.y.value,
                end_value=random.randint(0, constants.SCREEN_HEIGHT),
                duration=self.duration,
            )
        )
        self.alpha.add_animations(
            initial_value=self.alpha.value,
            steps=[
                Step(value=255, duration=self.FADE_IN_DURATION),
                Step(value=255, duration=self.duration - 2 * self.FADE_IN_DURATION),
                Step(value=0, duration=self.FADE_IN_DURATION),
            ],
        )

    def animate(self) -> None:
        if perf_counter() - self.start_time > 2 * self.duration:
            self.new_trajectory()
        self.sprite.position = (self.x.value, self.y.value)
        self.sprite.alpha = self.alpha.value


class SpaceBackground:
    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self.starfield_alpha1 = AnimatedValue(0)
        self.starfield_alpha2 = AnimatedValue(0)

    def setup(self) -> None:
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(random_sprite("images/backgrounds"))
        self.starfield1 = random_sprite("images/starfields")
        self.sprite_list.append(self.starfield1)
        self.starfield2 = random_sprite("images/starfields")
        self.sprite_list.append(self.starfield2)
        self.comet1 = Comet()
        self.sprite_list.append(self.comet1.sprite)
        self.comet2 = Comet()
        self.sprite_list.append(self.comet2.sprite)

    def animate(self):
        self.comet1.animate()
        self.comet2.animate()

        if not self.starfield_alpha1:
            self.starfield_alpha1.add_animations(
                initial_value=0,
                steps=[Step(value=50, duration=3), Step(value=0, duration=3)],
            )
        if not self.starfield_alpha2:
            self.starfield_alpha2.add_animations(
                initial_value=0,
                steps=[Step(value=70, duration=4.1), Step(value=0, duration=4)],
            )

    def draw(self) -> None:
        self.animate()
        self.starfield1.alpha = self.starfield_alpha1.value
        self.starfield2.alpha = self.starfield_alpha2.value
        self.sprite_list.draw()
