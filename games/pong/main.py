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
PLAYER_COLOR = [None, PLAYER_1_COLOR, PLAYER_2_COLOR]
BALL_COLOR = 0xFFF1E8

PADDLE_MOVE = 1.5

class Anim:
    def __init__(self):
        self.fnum = 0
        self.inf = None
        self.ctx = None
        self.remove = False
    def do_step(self):
        ret = self.step(self.fnum)
        self.fnum += 1
        return ret


class AnimBallPaddle(Anim):
    MAX_RADIUS = 70
    def __init__(self, ball_pos, color):
        super().__init__()
        self.center = ball_pos
        self.r = 1
        self.color = color
    def step(self, fnum):
        self.ctx.arc(self.center.x, self.center.y, self.r, 0, 2*math.pi)
        f = 0.8
        w = 1.5
        if self.r > 6:
            rf = self.r / self.MAX_RADIUS
            f -= 0.8 * rf
            w += 7 * rf*rf
        self.inf.vdraw.set_color_f(self.color, f)

        self.ctx.set_line_width(w)
        self.ctx.stroke()
        self.r += 2
        return self.r < self.MAX_RADIUS


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
        self.score_p1 = 0
        self.score_p2 = 0
        self.anims = []

    def add_anim(self, anim):
        anim.inf = self.inf
        anim.ctx = self.inf.vdraw.ctx
        self.anims.append(anim)

    def run_anims(self):
        remove_any = False
        for a in self.anims:
            a.remove = not a.do_step()
            remove_any |= a.remove
        if remove_any:
            self.anims = [a for a in self.anims if not a.remove]

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

    def draw_scores(self):
        self.inf.put_text(str(self.score_p1), 1, self.disp.width - 6)
        self.inf.put_text(str(self.score_p2), 1, 1, upside_down=True)

    def draw_board(self):
        self.disp.pixels.fill(0)
        self.run_anims()
        self.draw_player(self.p1_offset, 1, self.disp.height - 1, PLAYER_1_COLOR)
        self.draw_player(self.p2_offset, -1, 0, PLAYER_2_COLOR)
        # draw ball
        self.inf.vdraw.circle(self.ball_pos.x, self.ball_pos.y, BALL_SZ / 2, BALL_COLOR)
        self.draw_scores()
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
            self.crash(2)

        # p1 hit
        ball_bottom = self.ball_pos.y + BALL_OFFSET
        last_line = self.disp.height - 1
        p1_xdist = abs(self.ball_pos.x - self.p1_offset)
        if ball_bottom >= (last_line - PADDLE_HEIGHT) and self.ball_v.y > 0 and p1_xdist < PADDLE_H_WIDTH:
            self.ball_pos.y = last_line - BALL_OFFSET - PADDLE_HEIGHT
            self.paddle_hit(p1_xdist, 1)
        elif ball_bottom > last_line:
            self.crash(1)

        self.p1_offset = self.limit_paddle(self.p1_offset + self.joys.p1.x * PADDLE_MOVE)
        self.p2_offset = self.limit_paddle(self.p2_offset + self.joys.p2.x * PADDLE_MOVE)

    def paddle_hit(self, xdist, player):
        self.ball_v.y = -self.ball_v.y

        # the furthers it is from the center of the paddle the more random the direction can get
        off_center = (xdist / PADDLE_H_WIDTH)
        self.ball_v.x += (random.random()*2 - 1) * off_center
        self.ball_v.normalize(self.ball_abs_v)
        self.add_anim(AnimBallPaddle(self.ball_pos, PLAYER_COLOR[player]))

    def crash(self, player):
        if player == 1:
            self.score_p1 += 1
        else:
            self.score_p2 += 1
        self.reset_ball()



def main(argv):
    inf = infra.infra_init("sdl")
    disp = inf.get_display(show_fps=True, with_vector=True)
    joys = inf.get_joystick_state()

    state = State(inf, disp, joys)
    #inf.vdraw.ctx.scale(50,50)
    #inf.vdraw.test_pattern2()
    disp.refresh()

    slow = False
    while True:
        #if state.ball_pos.y < 10:
        #    slow = True
        if slow:
            time.sleep(0.5)
        if not inf.handle_events(state):
            break

        state.step()
        state.draw_board()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

