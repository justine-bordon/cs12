from __future__ import annotations

from enum import StrEnum, IntEnum, Enum
from dataclasses import dataclass
from typing import Protocol

from random import Random

from defaults import *


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class Color(IntEnum):
    _value_: int
    RED = COLOR_RED
    ORANGE = COLOR_ORANGE
    YELLOW = COLOR_YELLOW
    GREEN = COLOR_GREEN
    BLUE = COLOR_BLUE
    PURPLE = COLOR_PURPLE

class ShooterDirection(StrEnum):
    UPWARD = 'upward'
    WASD = 'wasd'
    CURSOR = 'cursor'


class Tile(Protocol):
    @property
    def color(self) -> Color | None: ...

class GridTile:
    @property
    def color(self) -> Color | None:
        return None

class PathTile:
    @property
    def color(self) -> Color | None:
        return None


class DefaultEnemy:
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = 0) -> None:
        self.initialize(color_options, base_hp, exp_yield, rng)
        self._special_rate = special_rate

    @property
    def color(self) -> Color | None:
        return self._color

    @property
    def current_hp(self) -> int:
        return self._current_hp

    def initialize(self, color_options: list[Color], base_hp: int, exp_yield: int, rng: Random) -> None:
        self._rng = rng

        self._current_hp = base_hp
        self._exp_yield = exp_yield

        self._lifetime = 0  # in ticks (30 FPS)
        self._tiles_traveled = 0
        self._color_options = color_options
        self.randomize_color()

    def randomize_color(self) -> None:
        if self._color_options:
            self._color = self._rng.choice(self._color_options)
        else:
            self._color = None

    def travel(self) -> None:
        self._tiles_traveled += 1

    def wait(self) -> None:
        self._lifetime += 1

    def modify_hp(self, amt: int) -> int:
        if self._color is None:
            return 0

        self._current_hp += amt
        if self._current_hp <= 0:
            self.die()
            return self._exp_yield
        return 0

    def die(self) -> None:
        self._color = None

class RegeneratorEnemy(DefaultEnemy):
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = REGENERATOR_TILES) -> None:
        super().__init__(color_options, base_hp, exp_yield, rng, special_rate)

    def travel(self) -> None:
        self._tiles_traveled += 1
        if (self._tiles_traveled > 0) & (self._tiles_traveled % self._special_rate == 0):
            self.modify_hp(1)
            self._tiles_traveled = 0

class ChameleonEnemy(DefaultEnemy):
    def __init__(self, color_options: list[Color] = [], base_hp: int = 0, exp_yield: int = 0, rng: Random = Random(), special_rate: int = CHAMELEON_CHANCE) -> None:
        super().__init__(color_options, base_hp, exp_yield, rng, special_rate)

    def wait(self) -> None:
        self._lifetime += 1
        if self._rng.randint(0, 3000) < self._special_rate:
            old = self._color
            while self._color == old:
                self.randomize_color()
            self._lifetime = 0


@dataclass
class Bullet:
    damage: int
    size: int
    speed: int  # in pixels per game tick
    hits: int
    range: int

    @classmethod
    def copy(cls, bullet: Bullet) -> Bullet:
        return cls(damage = bullet.damage, size = bullet.size, speed = bullet.speed, hits = bullet.hits, range = bullet.range)

@dataclass
class Projectile:
    pos_x: int
    pos_y: int
    vec_x: int
    vec_y: int
    bullet: Bullet
    color: Color

@dataclass
class Shooter:
    fire_rate: float   # per game tick (30 FPS)
    bullet: Bullet
    direction: ShooterDirection

    @classmethod
    def base_player(cls, direction: ShooterDirection) -> Shooter:
        return cls(
            fire_rate = PLAYER_FIRERATE,
            bullet = Bullet(BULLET_DAMAGE, BULLET_SIZE, BULLET_SPEED, BULLET_HITS, BULLET_RANGE),
            direction = direction
        )

    @classmethod
    def base_tower(cls, direction: ShooterDirection) -> Shooter:
        return cls(
            fire_rate = TOWER_FIRERATE,
            bullet = Bullet(BULLET_DAMAGE, BULLET_SIZE, BULLET_SPEED, BULLET_HITS, BULLET_RANGE),
            direction = direction
        )


@dataclass
class Tunnel:
    start_idx: int
    length: int

@dataclass
class Path:
    start_r: int
    start_c: int
    flow: list[Direction]
    tunnels: list[Tunnel]
    contents: list[Tile]

@dataclass
class Stage:
    lives: int
    player_x: int
    player_y: int
    paths: list[Path]
    rounds: list[Round]

@dataclass
class Round:
    enemy_hitpoints: int
    enemy_exp: int
    enemy_colors: list[Color]
    enemy_move_delay: int
    enemy_list: list[DefaultEnemy]
