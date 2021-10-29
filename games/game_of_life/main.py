import sys, os, ctypes, random, threading, time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra

import game_of_life
# pip install Cython

BOARD_HEIGHT = 256
BOARD_WIDTH = 256


class State(infra.BaseHandler):
    def __init__(self, disp, joys):
        self.offset_x = 0
        self.offset_y = 0
        self.disp = disp
        self.joys = joys

        self.game = game_of_life.GameOfLife(BOARD_WIDTH, BOARD_HEIGHT)

    def copy_to_disp(self):
        self.disp.pixels.mblit_from(self.game.get_board(), self.offset_x, self.offset_y, 0, 0, self.disp.width, self.disp.height)
        self.disp.refresh()

    def step(self):
        self.game.step()
        self.copy_to_disp()

    def update_pos(self, joy):
        self.offset_x += joy.x
        self.offset_y += joy.y
        #if joy.x != 0 or joy.y != 0:
        #    print("offsets:", self.offset_x, self.offset_y)

    def on_joy_event(self, player, event):
        with_color = self.joys[player].btn_B
        if event == infra.JOY_BTN_A:
            if player == infra.PLAYER_1:
                self.game.pattern_board("random", 0.5, with_color)
            else:
                self.game.pattern_board("gliders", 200, with_color)


def main(argv):
    inf = infra.infra_init("sdl")
    disp = inf.get_display(show_fps=True)

    disp.test_pattern()
    disp.refresh()
    joys = inf.get_joystick_state()

    state = State(disp, joys)
    state.game.pattern_board('random', 0.5, False)
    #state.game.pattern_board("glider", 0, True)

    state.copy_to_disp()

    while True:
        #time.sleep(1)
        if not inf.handle_events(state):
            break
        state.update_pos(joys[infra.PLAYER_1])
        state.step()
        #state.copy_to_disp()

    inf.destroy()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

