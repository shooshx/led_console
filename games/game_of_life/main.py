import sys, os, ctypes, random
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import infra

import game_of_life
# pip install Cython

BOARD_HEIGHT = 256
BOARD_WIDTH = 256



class State:
    def __init__(self, disp):
        self.offset_x = 0
        self.offset_y = 0
        self.disp = disp

        self.game = game_of_life.GameOfLife(BOARD_WIDTH, BOARD_HEIGHT)

    def copy_to_disp(self):
        for y in range(0, self.disp.height):
            for x in range(0, self.disp.width):
                self.disp.set_pixel(x, y, self.game.get(x + self.offset_x, y + self.offset_y))

    def step(self):
        self.game.step()
        self.copy_to_disp()


def main(argv):
    inf = infra.infra_init("sdl")

    disp = inf.get_display()

    disp.set_pixel(30, 30, 0xffffffff)
    for i in range(0,127):
        disp.set_pixel(i, i, 0xff00ffff)
    disp.refresh()

    state = State(disp)
    state.game.rand_board()

    while True:
        if not inf.handle_events():
            break
        state.step()
        disp.refresh()


    inf.destroy()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

