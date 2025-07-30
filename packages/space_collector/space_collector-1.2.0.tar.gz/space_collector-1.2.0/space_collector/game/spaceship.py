import logging
import math
from time import time

from space_collector.game.constants import (
    DISTANCE_PLANET_COLLECTION,
    MAP_DIMENSION,
    HIGH_ENERGY_LENGTH,
    FIRE_RATE,
    RADAR_RADIUS,
    SCORE_PLANET_COLLECTED,
    SCORE_ATTACKER_BROKEN,
    SCORE_EXPLORER_BROKEN,
    SCORE_COLLECTOR_BROKEN,
)
from space_collector.game.math import Vector, distance_point_to_segment
from space_collector.game.planet import Planet


def distance(item, other) -> float:
    return math.hypot(other.x - item.x, other.y - item.y)


class Spaceship:
    MAX_SPEED = 1000
    TYPE = "spaceship"

    def __init__(
        self, id_: int, x: float, y: float, angle: int, player: "Player"
    ) -> None:
        self.id = id_
        self.x = x
        self.y = y
        self.angle = angle
        self.speed: int = 0
        self.broken: bool = False
        self.player = player

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, x={self.x}, y={self.y})"

    @property
    def base(self) -> Vector:
        return Vector(self.player.base_position)

    def update(self, delta_time: float) -> None:
        self.x += delta_time * self.speed * math.cos(math.radians(self.angle))
        self.x = max(0, min(self.x, MAP_DIMENSION))
        self.y += delta_time * self.speed * math.sin(math.radians(self.angle))
        self.y = max(0, min(self.y, MAP_DIMENSION))
        if distance(self, self.base) < 200:
            self.broken = False

    def move(self, angle: int, speed: int) -> None:
        self.angle = angle
        self.speed = speed

    def radar_result(self, team: int) -> str:
        return f"S {team} {self.id} {int(self.x)} {int(self.y)} {int(self.broken)}"

    def state(self) -> dict:
        state = {
            "id": self.id,
            "x": int(self.x),
            "y": int(self.y),
            "angle": self.angle,
            "speed": self.speed,
            "broken": self.broken,
            "type": self.TYPE,
        }
        return state


class Collector(Spaceship):
    MAX_SPEED = 1000
    TYPE = "collector"

    def __init__(self, id_: int, x: int, y: int, angle: int, player: "Player") -> None:
        super().__init__(id_, x, y, angle, player)
        self.collected: int = -1
        self.planets = self.player.planets

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        if self.broken:
            if self.collected_planet is not None:
                self.uncollect_planet()
            return
        if self.collected == -1:
            not_collected_planets = [
                planet for planet in self.planets if planet.collected_by == -1
            ]
            if not_collected_planets:
                nearest_planet = min(
                    not_collected_planets, key=lambda p: distance(self, p)
                )
                if distance(self, nearest_planet) < DISTANCE_PLANET_COLLECTION:
                    self.collected = nearest_planet.id
        if self.collected != -1:
            planet = self.collected_planet
            if planet is None:
                logging.error("Collected planet not found: %d", self.collected)
            elif planet.saved:
                self.uncollect_planet()
            else:
                planet.x = self.x
                planet.y = self.y
                planet.collected_by = self.id
                if distance(self, self.base) < DISTANCE_PLANET_COLLECTION:
                    planet.saved = True
                    self.uncollect_planet()
                    logging.error("PLANET AT HOME")
                    self.player.score += SCORE_PLANET_COLLECTED

    @property
    def collected_planet(self) -> Planet | None:
        for planet in self.planets:
            if planet.id == self.collected:
                return planet
        return None

    def uncollect_planet(self):
        planet = self.collected_planet
        if planet is not None:
            planet.collected_by = -1
            self.collected = -1

    def state(self) -> dict:
        state = super().state()
        state["collected"] = self.collected
        return state


class Attacker(Spaceship):
    MAX_SPEED = 3000
    TYPE = "attacker"

    def __init__(self, id_: int, x: int, y: int, angle: int, player: "Player") -> None:
        super().__init__(id_, x, y, angle, player)
        self.fire_started: bool = False
        self.fire_angle: int = 0
        self.last_fire_start = time() - FIRE_RATE

    def fire(self, angle: int) -> None:
        if self.broken:
            return
        fire_start = time()
        if fire_start - self.last_fire_start < FIRE_RATE:
            logging.info(
                "too fast fire, slow down! %f", fire_start - self.last_fire_start
            )
            return
        self.last_fire_start = fire_start
        self.fire_started = True
        self.fire_angle = angle
        angle_radians = math.radians(angle)
        start = Vector([self.x, self.y])
        end = Vector(
            [
                self.x + math.cos(angle_radians) * HIGH_ENERGY_LENGTH,
                self.y + math.sin(angle_radians) * HIGH_ENERGY_LENGTH,
            ]
        )
        for team in self.player.all_spaceships()[1:]:
            for spaceship in team:
                if distance(self, spaceship) > HIGH_ENERGY_LENGTH:
                    continue
                distance_to_high_energy = distance_point_to_segment(
                    start, end, Vector([spaceship.x, spaceship.y])
                )
                if distance_to_high_energy < 200:
                    if not spaceship.broken:
                        if isinstance(spaceship, Attacker):
                            self.player.score += SCORE_ATTACKER_BROKEN
                        elif isinstance(spaceship, Explorer):
                            self.player.score += SCORE_EXPLORER_BROKEN
                        elif isinstance(spaceship, Collector):
                            self.player.score += SCORE_COLLECTOR_BROKEN
                    spaceship.broken = True

    def state(self) -> dict:
        state = super().state()
        state["fire"] = self.fire_started
        state["fire_angle"] = self.fire_angle
        self.fire_started = False  # TODO fix ugly hack
        return state


class Explorer(Spaceship):
    MAX_SPEED = 2000
    TYPE = "explorer"

    def __init__(self, id_: int, x: int, y: int, angle: int, player: "Player") -> None:
        super().__init__(id_, x, y, angle, player)
        self.radar_started: bool = False

    def radar(self) -> str:
        self.radar_started = True
        ret = []
        for planet in self.player.planets:
            ret.append(planet.radar_result())
        for spaceship in self.player.all_spaceships()[0]:
            ret.append(spaceship.radar_result(0))
        ret.append(f"B {self.base.x} {self.base.y}")
        if not self.broken:
            for team_id, team in enumerate(self.player.all_spaceships()):
                if team_id == 0:  # always present, managed earlier
                    continue
                for spaceship in team:
                    if distance(self, spaceship) < RADAR_RADIUS:
                        ret.append(spaceship.radar_result(team_id))
        return ",".join(ret)

    def state(self) -> dict:
        state = super().state()
        state["radar"] = self.radar_started
        self.radar_started = False  # TODO fix ugly hack
        return state
