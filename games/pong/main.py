import sys, os, random, math, time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra, cairo

this_path = os.path.dirname(os.path.abspath(__file__))

# P1 is at the bottom, P2 is at the top

class Vec2f:
    def __init__(self, x: float, y:float):
        self.x = x
        self.y = y
    def normalize(self, abs_len):
        l = math.sqrt(self.x*self.x + self.y*self.y)
        self.x *= abs_len / l
        self.y *= abs_len / l
    def copy(self):
        return Vec2f(self.x, self.y)

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

def star_path(ctx, x, y, r1, r2, np):
    dnp = math.pi / np

    ctx.move_to(x, y + r1)
    ang2 = dnp
    ctx.line_to(x + r2 * math.sin(ang2), y + r2 * math.cos(ang2))

    for i in range(1, np):
        di = i * 2
        ang1 = di * dnp
        ctx.line_to(x + r1 * math.sin(ang1), y + r1 * math.cos(ang1))
        ang2 = (di + 1) * dnp
        ctx.line_to(x + r2 * math.sin(ang2), y + r2 * math.cos(ang2))


class AnimBallOut_Fail(Anim):
    def __init__(self, ball_pos, state):
        super().__init__()
        self.center = ball_pos
        self.r = 1
        self.state = state
        self.phase = 0
        self.color_f = 1.0
        self.grad = None

    def step(self, fnum):
        r2 = min(self.r * 2, self.r + 30)
        if self.phase == 0:
            self.grad = cairo.RadialGradient(self.center.x, self.center.y, 5, self.center.x, self.center.y, 5 + math.sqrt(self.r)*3 )
            self.grad.add_color_stop_rgb(0, 1, 0.92, 0.15)
            self.grad.add_color_stop_rgb(0.8, 1, 0.63, 0)
            self.grad.set_extend(cairo.Extend.REFLECT)

            self.inf.vdraw.ctx.set_source(self.grad)
            star_path(self.ctx, self.center.x, self.center.y, self.r, r2, 20)
            self.inf.vdraw.ctx.fill()
            self.r += 7
            if self.r > 150:
                self.phase = 2
        else:
            self.inf.vdraw.set_color_f(0xFFEC27, self.color_f)
            star_path(self.ctx, self.center.x, self.center.y, self.r, r2, 20)
            self.inf.vdraw.ctx.fill()

            self.color_f -= 0.1

            if self.color_f <= 0:
                self.state.ball_paused = False
                self.state.ball_visible = True
                return False
        return True

BONUS_WIDTH = 10
BONUS_H_WIDTH = BONUS_WIDTH // 2

# an icon that appears in the line of the player, when take has some effect
# object is alive for as long as the effect is alive, if it's not a mementary effect
class Bonus:
    def __init__(self, player, x_pos):
        self.inf = None
        self.remove = False
        self.state = None

        self.sprite = None
        self.timeout = None

        self.player = player
        self.x_pos = x_pos
        self.time_created = time.time()

    def init(self):
        self.y_pos = BONUS_H_WIDTH if self.player == 2 else self.state.disp.height - BONUS_H_WIDTH

    def do_step(self):
        now = time.time()
        elapsed = now - self.time_created
        self.sprite.step_blit_to(self.state.disp.pixels, self.x_pos, self.y_pos)
        hit = self.state.p[self.player].hit_test(self.x_pos)
        if hit is not None:
            self.activate()
            return False
        if elapsed > self.timeout:
            return False
        return True


class Bonus3Balls(Bonus):
    def init(self):
        super().init()
        self.sprite = self.state.res.balls_bonus_anim
        self.timeout = 30

    def activate(self):
        print("Activated!")


class Player:
    def __init__(self, wh):
        self.offset = wh
        self.score = 0

    def hit_test(self, ball_pos_x):
        p2_xdist = abs(ball_pos_x - self.offset)
        if p2_xdist <= PADDLE_H_WIDTH:
            return p2_xdist
        return None

class Resources:
    def __init__(self):
        self.balls_bonus_anim = infra.AnimSprite(os.path.join(this_path, "balls_anim3/all.png"))


class State(infra.BaseHandler):
    def __init__(self, inf, disp, joys):
        self.disp = disp
        self.joys = joys
        self.inf = inf
        wh = disp.width // 2
        self.p1 = Player(wh)
        self.p2 = Player(wh)
        self.p = [None, self.p1, self.p2]
        self.ball_abs_v = 1.0
        self.reset_ball()
        self.ball_paused = True  # waiting for any input at first
        self.ball_visible = True
        self.anims = []
        self.res = Resources()
        self.bonuses = []

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

    def add_bonus(self, bonus):
        bonus.inf = self.inf
        bonus.state = self
        bonus.init()
        self.bonuses.append(bonus)

    def run_bonuses(self):
        self.rand_bonus()
        remove_any = False
        for b in self.bonuses:
            b.remove = not b.do_step()
            remove_any |= b.remove
        if remove_any:
            self.bonuses = [b for b in self.bonuses if not b.remove]

    def rand_bonus(self):
        if len(self.bonuses) > 0:
            return
        player = 1 if random.random() > 0.5 else 2
        p = self.p[player]
        pos_min = p.offset - PADDLE_WIDTH
        pos_max = p.offset + PADDLE_WIDTH
        sel_pos = None
        for i in range(0,10):
            pos = random.random() * (self.disp.width - BONUS_WIDTH) + BONUS_H_WIDTH
            if pos > pos_max or pos < pos_min:
                sel_pos = pos
                break
        if sel_pos is None:  # failed to find a spot
            return

        self.add_bonus(Bonus3Balls(player, sel_pos))

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
        self.inf.put_text(str(self.p1.score), 1, self.disp.width - 6)
        self.inf.put_text(str(self.p2.score), 1, 1, upside_down=True)

    def draw_board(self):
        self.disp.pixels.fill(0)

        self.run_anims()
        self.run_bonuses()
        self.draw_player(self.p1.offset, 1, self.disp.height - 1, PLAYER_1_COLOR)
        self.draw_player(self.p2.offset, -1, 0, PLAYER_2_COLOR)
        # draw ball
        if self.ball_visible:
            self.inf.vdraw.circle(self.ball_pos.x, self.ball_pos.y, BALL_SZ / 2, BALL_COLOR)
        self.draw_scores()
        self.disp.refresh()

    def limit_paddle(self, v):
        return min(max(v, PADDLE_WIDTH/2), self.disp.width-PADDLE_WIDTH/2)

    def step(self):
        if not self.ball_paused:
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
        p2_hit_xdist = self.p2.hit_test(self.ball_pos.x)
        if ball_top <= PADDLE_HEIGHT and self.ball_v.y < 0 and p2_hit_xdist is not None:
            self.ball_pos.y = BALL_OFFSET + PADDLE_HEIGHT
            self.paddle_hit(p2_hit_xdist, 2)
        elif ball_top < 0:
            self.crash(2)

        # p1 hit
        ball_bottom = self.ball_pos.y + BALL_OFFSET
        last_line = self.disp.height - 1
        p1_hit_xdist = self.p1.hit_test(self.ball_pos.x)
        if ball_bottom >= (last_line - PADDLE_HEIGHT) and self.ball_v.y > 0 and p1_hit_xdist is not None:
            self.ball_pos.y = last_line - BALL_OFFSET - PADDLE_HEIGHT
            self.paddle_hit(p1_hit_xdist, 1)
        elif ball_bottom > last_line:
            self.crash(1)

        self.p1.offset = self.limit_paddle(self.p1.offset + self.joys.p1.x * PADDLE_MOVE)
        self.p2.offset = self.limit_paddle(self.p2.offset + self.joys.p2.x * PADDLE_MOVE)

    def paddle_hit(self, xdist, player):
        self.ball_v.y = -self.ball_v.y

        # the furthers it is from the center of the paddle the more random the direction can get
        off_center = (xdist / PADDLE_H_WIDTH)
        self.ball_v.x += (random.random()*2 - 1) * off_center
        self.ball_v.normalize(self.ball_abs_v)
        self.add_anim(AnimBallPaddle(self.ball_pos, PLAYER_COLOR[player]))

    def crash(self, player):
        if player == 1:
            self.p1.score += 1
        else:
            self.p2.score += 1
        self.add_anim(AnimBallOut_Fail(self.ball_pos.copy(), self))
        self.ball_paused = True
        self.ball_visible = False
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

