import logging

from space_collector.game.spaceship import Spaceship, Collector, Attacker, Explorer
from space_collector.game.planet import Planet
from space_collector.game.math import Vector
from space_collector.game.player_orientations import player_orientations


class Player:
    def __init__(self, name: str, game) -> None:
        self.name = name
        self.blocked_counter = 0
        self.spaceships: list[Spaceship] = []
        self.planets: list[Planet] = []
        self.base_position = (0, 0)
        self.game = game
        self.team = -1
        self.score = 0

    @property
    def blocked(self):
        return self.blocked_counter > 3

    def reset_spaceships_and_planets(
        self, team: int, planets_data: list[Planet]
    ) -> None:
        self.team = team
        orientation = player_orientations[team]
        angle = orientation.angle
        self.base_position = orientation.base_position

        base_x, base_y = self.base_position
        origin_x_unit = Vector([1, 0])
        x_unit = orientation.matrix @ origin_x_unit
        self.spaceships = [
            Attacker(1, base_x, base_y, angle, self),
            Attacker(
                2, base_x + 1500 * x_unit.x, base_y + 1500 * x_unit.y, angle, self
            ),
            Attacker(
                3, base_x - 1500 * x_unit.x, base_y - 1500 * x_unit.y, angle, self
            ),
            Attacker(
                4, base_x + 3000 * x_unit.x, base_y + 3000 * x_unit.y, angle, self
            ),
            Attacker(
                5, base_x - 3000 * x_unit.x, base_y - 3000 * x_unit.y, angle, self
            ),
            Explorer(
                6, base_x + 4500 * x_unit.x, base_y + 4500 * x_unit.y, angle, self
            ),
            Explorer(
                7, base_x - 4500 * x_unit.x, base_y - 4500 * x_unit.y, angle, self
            ),
            Collector(
                8, base_x + 6000 * x_unit.x, base_y + 6000 * x_unit.y, angle, self
            ),
            Collector(
                9, base_x - 6000 * x_unit.x, base_y - 6000 * x_unit.y, angle, self
            ),
        ]

        for planet_data in planets_data:
            planet_position = Vector([planet_data.x, planet_data.y])
            rotated_planet = orientation.rotate_around_base(planet_position)
            planet = Planet(*(rotated_planet), planet_data.size, planet_data.id)
            self.planets.append(planet)

    def all_spaceships(self) -> list[list[Spaceship]]:
        """List spaceships per team, my team is always the first."""
        spaceships = []
        for player in self.game.players:
            spaceships.append(player.spaceships)
        my_spaceships = spaceships.pop(self.team)
        spaceships.insert(0, my_spaceships)
        return spaceships

    def manage_command(self, command_str: str) -> str:
        if self.blocked:
            return "BLOCKED"
        command = command_str.split()
        try:
            for command_type in ("MOVE", "FIRE", "RADAR"):
                if command[0] == command_type:
                    return getattr(self, command_type.lower())(command[1:])
            raise ValueError(f"Unknown command: {command_str}")
        except ValueError as e:
            logging.warning("Problem for %s: %s", self.name, str(e))
            self.blocked_counter += 1
            if self.blocked:
                return "BLOCKED"
            return "KO"

    def spaceship_by_id(self, id_: int) -> Spaceship:
        if id_ <= 0:
            raise ValueError(f"Wrong spaceship ID: {id_}")
        try:
            return self.spaceships[id_ - 1]
        except IndexError:
            raise ValueError(f"Wrong spaceship ID: {id_}")

    def move(self, parameters: list[str]) -> str:
        ship_id, angle, speed = (int(param) for param in parameters)
        angle %= 360
        spaceship = self.spaceship_by_id(ship_id)
        if speed > spaceship.MAX_SPEED:
            raise ValueError(f"Max speed excedeed {speed}/{spaceship.MAX_SPEED}")
        if speed < 0:
            raise ValueError("Negative speed not allowed")
        spaceship.move(angle, speed)
        return "OK"

    def fire(self, parameters: list[str]) -> str:
        ship_id, angle = (int(param) for param in parameters)
        spaceship = self.spaceship_by_id(ship_id)
        if not isinstance(spaceship, Attacker):
            raise ValueError("The spaceship that fired is not an attacker")
        spaceship.fire(angle)
        return "OK"

    def radar(self, parameters: list[str]) -> str:
        (ship_id,) = (int(param) for param in parameters)
        spaceship = self.spaceship_by_id(ship_id)
        if not isinstance(spaceship, Explorer):
            raise ValueError("The spaceship that fired is not an attacker")
        return spaceship.radar()

    def update(self, delta_time: float) -> None:
        if self.blocked:
            return
        for spaceship in self.spaceships:
            spaceship.update(delta_time)

    @property
    def all_planets_collected(self) -> bool:
        return all(planet.saved for planet in self.planets)

    def state(self) -> dict:
        return {
            "name": self.name,
            "blocked": self.blocked,
            "base_position": self.base_position,
            "spaceships": [spaceship.state() for spaceship in self.spaceships],
            "planets": [planet.state() for planet in self.planets],
            "score": self.score,
        }
