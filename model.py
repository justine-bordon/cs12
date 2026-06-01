from __future__ import annotations

from random import Random

from defaults import *
from classes import *


class GameModel:
    def __init__(self, rows: int, cols: int, rng: Random, shooter: Shooter, stage: Stage) -> None:
        self._rows = rows
        self._cols = cols
        self._rng = rng

        self._lives = stage.lives
        self._x_pos = stage.player_x
        self._y_pos = stage.player_y
        self._current_round = 0
        self._total_rounds = len(stage.rounds)
        self._exp = 0

        self._shooter = shooter
        self._aim_x = 0
        self._aim_y = -shooter.bullet.speed
        self._aim_dist = int(shooter.bullet.size * 3.33)

        self._grid: list[list[Tile]] = [[GridTile() for _ in range(self.cols)] for _ in range(self.rows)]
        self._paths = stage.paths

        self._rounds = stage.rounds
        self._create_round()

    @property
    def rows(self) -> int: return self._rows
    @property
    def cols(self) -> int: return self._cols
    @property
    def round_ongoing(self) -> bool: return self._round_ongoing
    @property
    def game_over(self) -> bool: return self._game_over
    @property
    def winner(self) -> bool: return self._winner
    @property
    def tick(self) -> int: return self._tick
    @property
    def grid(self) -> list[list[Tile]]: return self._grid
    @property
    def x_pos(self) -> int: return self._x_pos
    @property
    def y_pos(self) -> int: return self._y_pos
    @property
    def aim_x(self) -> int: return self._aim_x
    @property
    def aim_y(self) -> int: return self._aim_y
    @property
    def aim_dist(self) -> int: return self._aim_dist
    @property
    def projectile_color(self) -> Color: return self._projectile_color
    @property
    def projectile_list(self) -> list[Projectile]: return self._projectile_list
    @property
    def lives(self) -> int: return self._lives
    @property
    def exp(self) -> int: return self._exp
    @property
    def current_round(self) -> int: return self._current_round
    @property
    def total_rounds(self) -> int: return self._total_rounds


    def update(self) -> None:
        if self._round_ongoing:

            self._check_tiles()
            if (self._tick % self._round.enemy_move_delay) == 0:
                self._move_paths()
            self._move_projectiles()

            if self._shoot_cd > 0:
                self._shoot_cd -= 1

            if self._lives <= 0:
                self._round_ongoing = False
                self._game_over = True
                self._winner = False

            if (len(self._enemy_to_spawn) + self._enemy_in_grid) == 0:
                self._current_round += 1
                if self._current_round < self._total_rounds:
                    self._create_round()
                    return
                else:
                    self._current_round -= 1
                    self._round_ongoing = False
                    self._game_over = True
                    self._winner = True
                    return

            self._tick += 1

    def _create_round(self):
        round = self._rounds.pop(0)

        self._round = round
        self._enemy_to_spawn = round.enemy_list
        self._enemy_in_grid = 0
        self._enemy_colors = round.enemy_colors

        self._projectile_list: list[Projectile] = []
        self._projectile_color = self._rng.choice(self._enemy_colors)
        self._shoot_cd = 0

        self._round_ongoing = False
        self._game_over = False
        self._winner = False
        self._tick = 0

        self._create_paths(self._paths)

    def round_start(self, start: bool) -> None:
        if start:
            self._round_ongoing = True

    def aim(self, cursor_pos: tuple[int, int], wasd: Direction | None) -> None:
        x = cursor_pos[0]
        y = cursor_pos[1]
        shooter = self._shooter
        bullet = shooter.bullet
        match shooter.direction:
            case ShooterDirection.UPWARD:
                self._aim_x = 0
                self._aim_y = -bullet.speed
            case ShooterDirection.WASD:
                if wasd is None:
                    return
                self._aim_x = wasd.value[1] * bullet.speed
                self._aim_y = wasd.value[0] * bullet.speed
            case ShooterDirection.CURSOR:
                vec_x = x - self._x_pos
                vec_y = y - self._y_pos
                vec_len = bullet.speed / (((vec_x ** 2) + (vec_y ** 2)) ** 0.5)

                self._aim_x = vec_x * vec_len
                self._aim_y = vec_y * vec_len

    def shoot(self) -> None:
        if self._tick < 10:
            return
        if self._shoot_cd > 0:
            return

        shooter = self._shooter
        bullet = shooter.bullet

        aim_len = self._aim_dist / (((self._aim_x ** 2) + (self._aim_y ** 2)) ** 0.5)
        source_x = self._x_pos + (self._aim_x * aim_len)
        source_y = self._y_pos + (self._aim_y * aim_len)
        projectile = Projectile(source_x, source_y, self._aim_x, self._aim_y, Bullet.copy(bullet), self._projectile_color)

        self._projectile_list.append(projectile)
        self._shoot_cd = 30 // shooter.fire_rate
        self._projectile_color = self._rng.choice(self._enemy_colors)

    def _create_paths(self, paths: list[Path]) -> None:
        self._paths: list[Path] = []
        for path in paths:
            path.contents = [PathTile() for _ in range(len(path.flow) + 1)]
            self._paths.append(path)
        self._update_grid()

    def _move_paths(self) -> None:
        self._rng.shuffle(self._paths)
        for i, path in enumerate(self._paths):
            if path.contents.pop().color is not None:
                self._lives = max(0, self._lives - 1)

            for j, tile in enumerate(path.contents):
                if isinstance(tile, DefaultEnemy):
                    tile.travel()
                    path.contents[j] = tile

            if self._enemy_to_spawn:
                round = self._round
                self._rng.shuffle(self._enemy_to_spawn)
                enemy = self._enemy_to_spawn.pop()
                enemy.initialize(round.enemy_colors, round.enemy_hitpoints, round.enemy_exp, self._rng)
                path.contents.insert(0, enemy)
            else:
                path.contents.insert(0, PathTile())

            self._paths[i] = path

        self._update_grid()

    def _update_grid(self) -> None:
        for path in self._paths:
            r = path.start_r
            c = path.start_c
            self._grid[r][c] = path.contents[0]
            for i, dir in enumerate(path.flow):
                r += dir.value[0]
                c += dir.value[1]
                self._grid[r][c] = path.contents[i + 1]

    def _move_projectiles(self):
        new_projectiles: list[Projectile] = []

        for projectile in self._projectile_list:
            projectile.pos_x += projectile.vec_x
            projectile.pos_y += projectile.vec_y
            projectile.bullet.range -= ((projectile.vec_x ** 2) + (projectile.vec_y ** 2)) ** 0.5
            if projectile.bullet.range <= 0:
                continue
            new_projectiles.append(projectile)

        self._projectile_list = new_projectiles

    def _check_tiles(self) -> None:
        colors: set[Color] = set()
        self._enemy_in_grid = 0
        for k, path in enumerate(self._paths):
            r = path.start_r
            c = path.start_c

            tile = self._check_for_bullet(r, c)
            if isinstance(tile, DefaultEnemy) and (tile.color is not None):
                self._enemy_in_grid += 1
                colors.add(tile.color)
                tile.wait()
            path.contents[0] = tile

            for i, dir in enumerate(path.flow):
                r += dir.value[0]
                c += dir.value[1]

                tile = self._check_for_bullet(r, c)
                if isinstance(tile, DefaultEnemy) and (tile.color is not None):
                    self._enemy_in_grid += 1
                    colors.add(tile.color)
                    tile.wait()
                path.contents[i + 1] = tile

            self._paths[k] = path

        self._enemy_colors = list(colors)
        self._update_grid()

    def _check_for_bullet(self, row: int, col: int) -> Tile:
        tile = self._grid[row][col]
        if isinstance(tile, DefaultEnemy):
            tile_x = BORDER_WIDTH + (col * TILE_SIZE)
            tile_y = BORDER_WIDTH + (row * TILE_SIZE)
            for i, projectile in enumerate(self._projectile_list):
                if projectile.color != tile.color:
                    continue

                size = int((2 ** 0.5) * projectile.bullet.size / 2)
                x1 = tile_x - size
                x2 = tile_x + TILE_SIZE + size  + 1
                y1 = tile_y - size
                y2 = tile_y + TILE_SIZE + size  + 1

                if (int(projectile.pos_x) in range(x1, x2)) and ((int(projectile.pos_y) in range(y1, y2))):
                    self._exp += tile.modify_hp(-projectile.bullet.damage)

                    projectile.bullet.hits -= 1
                    if projectile.bullet.hits <= 0:
                        self._projectile_list.pop(i)
                    else:
                        self._projectile_list[i] = projectile

                    break

        return tile


    @classmethod
    def demo(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR)
        player.bullet.speed *= 3
        player.fire_rate *= 2

        flow1 = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.RIGHT, Direction.DOWN, Direction.RIGHT]
        path1 = Path(0, 0, flow1, [], [])

        flow2 = [Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.UP, Direction.LEFT, Direction.UP, Direction.LEFT]
        path2 = Path(5, 7, flow2, [], [])

        enemy_colors = [Color.ORANGE, Color.GREEN, Color.PURPLE]
        rounds = [Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [ChameleonEnemy() for _ in range(ENEMY_COUNT*2)]) for _ in range(5)]

        stage = Stage(5, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, [path1, path2], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)

    @classmethod
    def phase1(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.UPWARD)

        flow = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT]
        path = Path(0, 0, flow, [], [])

        enemy_colors = [rng.choice([Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE])]
        rounds = [
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(5)])
        ]

        stage = Stage(2, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, [path], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)

    @classmethod
    def phase2(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.WASD)

        flow = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT]
        path = Path(0, 0, flow, [], [])

        enemy_colors = [Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]
        rng.shuffle(enemy_colors)
        enemy_colors = enemy_colors[:2]
        rounds = [
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(5)]),
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(7)]),
        ]

        stage = Stage(5, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, [path], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)


    @classmethod
    def highway(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.CURSOR)
        player.fire_rate *= 10
        player.bullet.speed *= 4
        player.bullet.hits = 5

        flow_up = [Direction.UP, Direction.UP, Direction.UP, Direction.UP, Direction.UP]
        flow_down = [Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN]
        path1 = Path(0, 0, flow_down, [], [])
        path3 = Path(0, 2, flow_down, [], [])
        path5 = Path(0, 6, flow_down, [], [])
        path2 = Path(5, 1, flow_up, [], [])
        path4 = Path(5, 5, flow_up, [], [])
        path6 = Path(5, 7, flow_up, [], [])

        enemy_colors = [Color.ORANGE, Color.BLUE]
        rounds = [
            Round(ENEMY_HITPOINTS*2, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(ENEMY_COUNT*6)]),
            Round(ENEMY_HITPOINTS*2, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(ENEMY_COUNT*7)]),
            Round(ENEMY_HITPOINTS*2, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [RegeneratorEnemy() for _ in range(ENEMY_COUNT*6)]),
            Round(ENEMY_HITPOINTS*2, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [RegeneratorEnemy() for _ in range(ENEMY_COUNT*7)]),
            Round(ENEMY_HITPOINTS*3, ENEMY_EXP_YIELD, enemy_colors, ENEMY_MOVE_DELAY, [DefaultEnemy() for _ in range(ENEMY_COUNT*6)]),
        ]

        stage = Stage(5, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, [path1, path2, path3, path4, path5, path6], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)


    @classmethod
    def fourway(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.WASD)
        player.fire_rate *= 5
        player.bullet.speed *= 3
        player.bullet.hits = 1

        flow_up = [Direction.UP, Direction.UP, Direction.UP, Direction.UP]
        flow_down = [Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN]
        flow_right = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT]
        flow_left = [Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT] 
        path1 = Path(5, 0, flow_up, [], [])
        path2 = Path(0, 7, flow_down, [], [])
        path4 = Path(0, 1, flow_right, [], [])
        path3 = Path(5, 6, flow_left, [], [])

        enemy_colors = [Color.BLUE, Color.PURPLE]
        rounds = [
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY*2), [DefaultEnemy() for _ in range(ENEMY_COUNT*4)]),
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY*2), [DefaultEnemy() for _ in range(ENEMY_COUNT*5)]),
            Round(ENEMY_HITPOINTS*2, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY*2.5), [DefaultEnemy() for _ in range(ENEMY_COUNT*4)]),
        ]

        stage = Stage(5, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, [path1, path2, path3, path4], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)


    @classmethod
    def crossway(cls) -> GameModel:
        rng = Random()
        player = Shooter.base_player(ShooterDirection.UPWARD)
        player.fire_rate *= 5
        player.bullet.speed *= 3
        player.bullet.hits = 8

        flow_left = [Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT, Direction.LEFT] 
        flow_right = [Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT, Direction.RIGHT]
        path1 = Path(1, 7, flow_left, [], [])
        path2 = Path(2, 0, flow_right, [], [])
        path4 = Path(3, 7, flow_left, [], [])
        path3 = Path(4, 0, flow_right, [], [])

        enemy_colors = [Color.ORANGE, Color.BLUE, Color.YELLOW, Color.PURPLE]
        rounds = [
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY), [DefaultEnemy() for _ in range(ENEMY_COUNT*4)]),
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY), [DefaultEnemy() for _ in range(ENEMY_COUNT*5)]),
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY), [ChameleonEnemy() for _ in range(ENEMY_COUNT*6)]),
            Round(ENEMY_HITPOINTS, ENEMY_EXP_YIELD, enemy_colors, int(ENEMY_MOVE_DELAY*0.75), [ChameleonEnemy() for _ in range(ENEMY_COUNT*6)]),
        ]

        stage = Stage(5, SCREEN_WIDTH//2, SCREEN_HEIGHT - BORDER_WIDTH - (TILE_SIZE//2), [path1, path2, path3, path4], rounds)

        return cls(GRID_ROWS, GRID_COLS, rng, player, stage)
