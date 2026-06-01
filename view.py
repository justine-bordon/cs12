import pyxel

from typing import Protocol

from defaults import *
from classes import *


class UpdateHandler(Protocol):
    def update(self): ...

class DrawHandler(Protocol):
    def draw(self): ...


class GameView:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def start(self, update_handler: UpdateHandler, draw_handler: DrawHandler) -> None:
        self.update_handler = update_handler
        self.draw_handler = draw_handler

        pyxel.init(self.width, self.height, title='Zuma: Tower Defense', fps=30)
        pyxel.run(update_handler.update, draw_handler.draw)

    def stop(self) -> None:
        pyxel.stop()

    def cursor_pos(self) -> tuple[int, int]: return pyxel.mouse_x, pyxel.mouse_y
    def input_leftclick(self) -> bool: return True if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT, 1, 1) else False
    def input_space(self) -> bool: return True if pyxel.btnp(pyxel.KEY_SPACE) else False
    def input_wasd(self) -> Direction | None:
        if pyxel.btnp(pyxel.KEY_W):
            return Direction.UP
        if pyxel.btnp(pyxel.KEY_D):
            return Direction.RIGHT
        if pyxel.btnp(pyxel.KEY_A):
            return Direction.LEFT
        if pyxel.btnp(pyxel.KEY_S):
            return Direction.DOWN
        return None

    def reset_screen(self) -> None:
        pyxel.cls(BACKGROUND_COLOR)

    def draw_border(self) -> None:
        pyxel.line(BORDER_WIDTH, BORDER_WIDTH, self.width - BORDER_WIDTH, BORDER_WIDTH, TEXT_COLOR)  # north
        pyxel.line(BORDER_WIDTH, self.height - BORDER_WIDTH, self.width - BORDER_WIDTH, self.height - BORDER_WIDTH, TEXT_COLOR)  # south
        pyxel.line(self.width - BORDER_WIDTH, BORDER_WIDTH, self.width - BORDER_WIDTH, self.height - BORDER_WIDTH, TEXT_COLOR)  # east
        pyxel.line(BORDER_WIDTH, BORDER_WIDTH, BORDER_WIDTH, self.height - BORDER_WIDTH, TEXT_COLOR)  # west

    def draw_path(self, grid: list[list[Tile]]) -> None:
        for i, row in enumerate(grid):
            for j, tile in enumerate(row):
                if isinstance(tile, GridTile):
                    continue
                x = BORDER_WIDTH + (j * TILE_SIZE)
                y = BORDER_WIDTH + (i * TILE_SIZE)
                tile_color = (COLOR_EMPTY if tile.color is None else tile.color)
                pyxel.rect(x, y, TILE_SIZE, TILE_SIZE, tile_color)
                if isinstance(tile, DefaultEnemy):
                    for k in range(tile.current_hp):
                        x1 = x + (k * 5)
                        y1 = y + (k * 5)
                        s = TILE_SIZE - (k * 10)
                        pyxel.rectb(x1, y1, s, s, 1)

    def draw_cursor(self) -> None:
        pyxel.mouse(True)

    def draw_player(self, x: float, y: float) -> None:
        pyxel.circ(x, y, PLAYER_RADIUS, PLAYER_COLOR)

    def draw_aim(self, x: int, y: int, aim_x: int, aim_y: int, aim_dist: int, color: int) -> None:
        aim_len = aim_dist / (((aim_x ** 2) + (aim_y ** 2)) ** 0.5)
        pyxel.circ(x + (aim_x * aim_len), y + (aim_y * aim_len), BULLET_SIZE, color)

    def draw_projectile(self, projectile: Projectile) -> None:
        pyxel.circ(projectile.pos_x, projectile.pos_y, projectile.bullet.size, projectile.color)

    def draw_press_to_start(self) -> None:
        pyxel.text((self.width / 2) - 43, self.height - (BORDER_WIDTH / 2) - 3, "Press [SPACE] to Start", TEXT_COLOR)

    def draw_lives(self, amt: int) -> None:
        pyxel.text(BORDER_WIDTH / 2, (BORDER_WIDTH / 2) + 5, f"Lives: {amt}", TEXT_COLOR)

    def draw_rounds(self, current: int, total: int) -> None:
        pyxel.text(BORDER_WIDTH / 2, (BORDER_WIDTH / 2) - 8, f"Round: {current} / {total}", TEXT_COLOR)

    def draw_exp(self, amt: int) -> None:
        pyxel.text(self.width - BORDER_WIDTH + 1, (BORDER_WIDTH / 2) - 8, f"EXP: {amt}", TEXT_COLOR)

    def draw_winner(self) -> None:
        width = 50
        height = 50
        pyxel.rect((self.width - width) / 2, (self.height - height) / 2, width, height, BACKGROUND_COLOR)
        pyxel.text((self.width / 2) - 15, (self.height / 2) - 2, "YOU WIN!", TEXT_COLOR)

    def draw_gameover(self) -> None:
        width = 50
        height = 50
        pyxel.rect((self.width - width) / 2, (self.height - height) / 2, width, height, BACKGROUND_COLOR)
        pyxel.text((self.width / 2) - 17, (self.height / 2) - 2, "GAME OVER", TEXT_COLOR)

    def draw_test(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) - 8, txt, TEXT_COLOR)
    def draw_test2(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) - 2, txt, TEXT_COLOR)
    def draw_test3(self, txt: str) -> None:
        pyxel.text((self.width / 2) - 43, (BORDER_WIDTH / 2) + 5, txt, TEXT_COLOR)
