import sys, os, ctypes, random, threading, time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
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
        self.disp.pixels.blit_from(self.game.get_board(), self.offset_x, self.offset_y, 0, 0, self.disp.width, self.disp.height)



    def step(self):
        self.game.step()
        self.copy_to_disp()


class FpsShow:
    def __init__(self):
        self.count = 0
        self.last_count = 0
        self.do_stop = False
        self.t = threading.Thread(target=self.fps_thread)
        self.t.start()

    def inc(self):
        self.count += 1
    def stop(self):
        self.do_stop = True
    def fps_thread(self):
        while not self.do_stop:
            time.sleep(1)
            c = self.count
            print("fps:", c - self.last_count)
            self.last_count = c


def main(argv):
    inf = infra.infra_init("sdl")
    fps = FpsShow()

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
        fps.inc()
        disp.refresh()

    fps.stop()
    inf.destroy()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

