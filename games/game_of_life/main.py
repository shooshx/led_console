import sys, os, ctypes, random, threading, time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra, infra_c

import game_of_life

# controls:
# - joysticks: move view
# - A - reset pattern, P1:random, P2:gliders
# - B - hold while pressing A for colored version
# - C,P1 and D,P1 - fade (state)
# - C,P2 - pause (state)

BOARD_HEIGHT = 256
BOARD_WIDTH = 256


class State(infra.BaseHandler):
    def __init__(self, disp, joys):
        self.offset_x = 0
        self.offset_y = 0
        self.disp = disp
        self.joys = joys
        self.pause = False
        self.fade = 0.0

        self.game = game_of_life.GameOfLife(BOARD_WIDTH, BOARD_HEIGHT)
        gboard = self.game.get_board()
        self.board_adapter = infra_c.IntMatrix(gboard.width(), gboard.height())
        self.board_adapter.reset_raw_ptr(gboard.get_raw_ptr())

    def copy_to_disp(self):
        self.disp.pixels.mblit_from(self.board_adapter, self.offset_x, self.offset_y, 0, 0, self.disp.width, self.disp.height)
        self.disp.refresh()

    def step(self):
        self.game.step(self.fade)
        self.copy_to_disp()

    def update_pos(self, joy):
        self.offset_x += joy.x
        self.offset_y += joy.y
        #if joy.x != 0 or joy.y != 0:
        #    print("offsets:", self.offset_x, self.offset_y)

    def on_joy_event(self, ev):
        with_color = self.joys.p(ev.player).btn_B
        if ev.event == infra.JOY_BTN_A:
            if ev.player == infra.PLAYER_1:
                self.game.pattern_board("random", 0.5, do_color=with_color)
            else:
                self.game.pattern_board("gliders", 200, do_color=with_color)
            self.copy_to_disp()
        if ev.event == infra.JOY_BTN_C and ev.player == infra.PLAYER_2:
            self.pause = not self.pause
        if ev.player == infra.PLAYER_1:
            if ev.event == infra.JOY_BTN_C or ev.event == infra.JOY_BTN_D:
                if self.fade == 0:
                    self.fade = 0.9 if ev.event == infra.JOY_BTN_C else 0.999
                else:
                    self.fade = 0


def main(argv):
    inf = infra.infra_init()
    disp = inf.get_display(show_fps=True)

    disp.test_pattern()
    disp.refresh()
    joys = inf.get_joystick_state()

    state = State(disp, joys)
    state.game.pattern_board('random', 0.5, False)
    #state.game.pattern_board("glider", 0, False)

    while True:
        #time.sleep(1)
        if not inf.handle_events(state):
            break
        state.update_pos(joys.p(infra.PLAYER_1))
        if state.pause:
            state.copy_to_disp()  # can still move
            continue
        state.step()
        #state.copy_to_disp()

    inf.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

