import sys, os, random, math, time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra


# P1 is at the bottom, P2 is at the top

class Vec2f:
    def __init__(self, x: float, y:float):
        self.x = x
        self.y = y
    def normalize(self, abs_len):
        l = math.sqrt(self.x*self.x + self.y*self.y)
        self.x *= abs_len / l
        self.y *= abs_len / l

PADDLE_WIDTH = 20
PADDLE_H_WIDTH = PADDLE_WIDTH // 2
PADDLE_HEIGHT = 3
BALL_SZ = 4
BALL_OFFSET = 2

PLAYER_1_COLOR = 0x29ADFF
PLAYER_2_COLOR = 0xFF004D
BALL_COLOR = 0xFFF1E8

PADDLE_MOVE = 1.5

class State(infra.BaseHandler):
    def __init__(self, inf, disp, joys):
        self.disp = disp
        self.joys = joys
        self.inf = inf
        wh = disp.width // 2
        self.p1_offset = wh
        self.p2_offset = wh
        self.ball_abs_v = 1.0
        self.reset_ball()

    def reset_ball(self):
        self.ball_pos = Vec2f(self.disp.width // 2, self.disp.height // 2)

        start_dir = 1 if random.random() > 0.5 else -1
        start_sidev = random.random()*2 - 1
        self.ball_v = Vec2f(start_sidev, start_dir)
        self.ball_v.normalize(self.ball_abs_v)

    def draw_player(self, xpos, ysign, bottomy, color):
        self.inf.vdraw.set_color(color)
        startx = xpos - PADDLE_H_WIDTH
        endx = xpos + PADDLE_WIDTH // 2

        ctx = self.inf.vdraw.ctx
        ctx.move_to(startx, bottomy)
        ctx.line_to(startx, bottomy - ysign*2)
        ctx.line_to(startx + 3, bottomy - ysign*4)
        ctx.line_to(endx - 3, bottomy - ysign*4)
        ctx.line_to(endx, bottomy - ysign*2)
        ctx.line_to(endx, bottomy)

        #self.inf.vdraw.ctx.rectangle(, , PADDLE_WIDTH, PADDLE_HEIGHT)
        self.inf.vdraw.ctx.fill()


    def draw_board(self):
        self.disp.pixels.fill(0)
        self.draw_player(self.p1_offset, 1, self.disp.height - 1, PLAYER_1_COLOR)
        self.draw_player(self.p2_offset, -1, 0, PLAYER_2_COLOR)
        # draw ball
        self.inf.vdraw.circle(self.ball_pos.x, self.ball_pos.y, BALL_SZ / 2, BALL_COLOR)
        #self.inf.draw.rect(int(self.ball_pos.x) - BALL_OFFSET, int(self.ball_pos.y) - BALL_OFFSET, BALL_SZ, BALL_SZ, BALL_COLOR)
        self.disp.refresh()

    def limit_paddle(self, v):
        return min(max(v, PADDLE_WIDTH/2), self.disp.width-PADDLE_WIDTH/2)

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
        # area where paddle can hit
        ball_top = self.ball_pos.y - BALL_OFFSET
        p2_xdist = abs(self.ball_pos.x - self.p2_offset)
        if ball_top <= PADDLE_HEIGHT and self.ball_v.y < 0 and p2_xdist <= PADDLE_H_WIDTH:
            self.ball_pos.y = BALL_OFFSET + PADDLE_HEIGHT
            self.paddle_hit(p2_xdist, 2)
        elif ball_top < 0:
            self.reset_ball()

        # p1 hit
        ball_bottom = self.ball_pos.y + BALL_OFFSET
        last_line = self.disp.height - 1
        p1_xdist = abs(self.ball_pos.x - self.p1_offset)
        if ball_bottom >= (last_line - PADDLE_HEIGHT) and self.ball_v.y > 0 and p1_xdist < PADDLE_H_WIDTH:
            self.ball_pos.y = last_line - BALL_OFFSET - PADDLE_HEIGHT
            self.paddle_hit(p1_xdist, 1)
        elif ball_bottom > last_line:
            self.reset_ball()

        self.p1_offset = self.limit_paddle(self.p1_offset + self.joys.p1.x * PADDLE_MOVE)
        self.p2_offset = self.limit_paddle(self.p2_offset + self.joys.p2.x * PADDLE_MOVE)

    def paddle_hit(self, xdist, player):
        self.ball_v.y = -self.ball_v.y

        # the furthers it is from the center of the paddle the more random the direction can get
        off_center = (xdist / PADDLE_H_WIDTH)
        self.ball_v.x += (random.random()*2 - 1) * off_center
        self.ball_v.normalize(self.ball_abs_v)


def main(argv):
    inf = infra.infra_init("sdl")
    disp = inf.get_display(show_fps=True, with_vector=True)
    joys = inf.get_joystick_state()

    state = State(inf, disp, joys)
    #inf.vdraw.ctx.scale(50,50)
    #inf.vdraw.test_pattern2()
    disp.refresh()

    while True:
        #if state.ball_pos.y < 10:
        #    time.sleep(1)
        if not inf.handle_events(state):
            break

        state.step()
        state.draw_board()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

