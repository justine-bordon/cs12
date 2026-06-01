from model import GameModel
from view import GameView

from defaults import *


class GameController:
    def __init__(self, model: GameModel, view: GameView) -> None:
        self._model = model
        self._view = view

    def start(self) -> None:
        self._view.start(self, self)

    def update(self) -> None:
        model = self._model
        view = self._view

        if model.round_ongoing:
            model.aim(view.cursor_pos(), view.input_wasd())
            if view.input_leftclick():
                model.shoot()
        else:
            if not model.game_over:
                model.round_start(view.input_leftclick())

        model.update()

    def draw(self) -> None:
        model = self._model
        view = self._view

        view.reset_screen()
        view.draw_path(model.grid)
        view.draw_border()
        view.draw_player(model.x_pos, model.y_pos)
        view.draw_aim(model.x_pos, model.y_pos, model.aim_x, model.aim_y, model.aim_dist, model.projectile_color)
        view.draw_lives(model.lives)
        view.draw_rounds(model.current_round + 1, model.total_rounds)
        view.draw_exp(model.exp)

        if model.round_ongoing:
            for projectile in model.projectile_list:
                view.draw_projectile(projectile)
        else:
            if model.game_over:
                if model.winner:
                    view.draw_winner()
                else:
                    view.draw_gameover()
            else:
                view.draw_press_to_start()

        view.draw_cursor()
