import sys, os, random, math
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra


# P1 is at the bottom, P2 is at the top

class Vec2f:
    def __init__(self, x: float, y:float):
        self.x = x
        self.y = y
    def normalize(self):
        l = math.sqrt(self.x*self.x + self.y*self.y)
        self.x /= l
        self.y /= l

PADDLE_WIDTH = 12
PADDLE_HEIGHT = 3
BALL_SZ = 4
BALL_OFFSET = 1

PLAYER_1_COLOR = 0x29ADFF
PLAYER_2_COLOR = 0xFF004D
BALL_COLOR = 0xFFF1E8

class State(infra.BaseHandler):
    def __init__(self, inf, disp, joys):
        self.disp = disp
        self.joys = joys
        self.inf = inf
        wh = disp.width // 2
        self.p1_offset = wh
        self.p2_offset = wh
        self.ball_pos = Vec2f(wh, wh)

        start_dir = 1 if random.random() > 0.5 else -1
        start_sidev = random.random()*2 - 1
        self.ball_v = Vec2f(start_sidev, start_dir)
        self.ball_v.normalize()

    def draw_player(self, xpos, ypos, color):
        self.inf.vdraw.set_color(color)
        self.inf.vdraw.ctx.rectangle(xpos - PADDLE_WIDTH // 2, ypos - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.inf.vdraw.ctx.fill()

    def draw_board(self):
        self.disp.pixels.fill(0)
        self.draw_player(self.p1_offset, self.disp.height - 1 - PADDLE_HEIGHT // 2, PLAYER_1_COLOR)
        self.draw_player(self.p2_offset, PADDLE_HEIGHT // 2, PLAYER_2_COLOR)
        # draw ball
        self.inf.vdraw.circle(self.ball_pos.x, self.ball_pos.y, BALL_SZ / 2, BALL_COLOR)
        #self.inf.draw.rect(int(self.ball_pos.x) - BALL_OFFSET, int(self.ball_pos.y) - BALL_OFFSET, BALL_SZ, BALL_SZ, BALL_COLOR)
        self.disp.refresh()

    def step(self):
        self.ball_pos.x += self.ball_v.x
        self.ball_pos.y += self.ball_v.y
        # side walls
        if self.ball_pos.x <= BALL_OFFSET:
            self.ball_pos.x = BALL_OFFSET
            self.ball_v.x = -self.ball_v.x
        if self.ball_pos.x >= self.disp.width - 1 - BALL_OFFSET:
            self.ball_pos.x = self.disp.width - 1 - BALL_OFFSET
            self.ball_v.x = -self.ball_v.x

        # top bottom walls
        if self.ball_pos.y <= BALL_OFFSET:
            self.ball_pos.y = BALL_OFFSET
            self.ball_v.y = -self.ball_v.y
        if self.ball_pos.y >= self.disp.height - 1 - BALL_OFFSET:
            self.ball_pos.y = self.disp.height - 1 - BALL_OFFSET
            self.ball_v.y = -self.ball_v.y


def main(argv):
    inf = infra.infra_init("sdl")
    disp = inf.get_display(show_fps=True, with_vector=True)
    joys = inf.get_joystick_state()

    state = State(inf, disp, joys)
    #inf.vdraw.ctx.scale(50,50)
    #inf.vdraw.test_pattern2()
    disp.refresh()

    while True:
        #time.sleep(1)
        if not inf.handle_events(state):
            break

        state.step()
        state.draw_board()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

