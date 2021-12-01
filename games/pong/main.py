import sys, os, random, math, time
import cairo
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra

this_path = os.path.dirname(os.path.abspath(__file__))

# P1 is at the bottom, P2 is at the top




# game hardness params
PADDLE_MOVE = 1.5
BALL_START_SPEED = 1.0
PADDLE_WIDTH = 20

# constants
PADDLE_H_WIDTH = PADDLE_WIDTH // 2
PADDLE_HEIGHT = 3
BALL_SZ = 4
BALL_OFFSET = 2

PLAYER_1_COLOR = 0x29ADFF
PLAYER_2_COLOR = 0xFF004D
PLAYER_COLOR = [None, PLAYER_1_COLOR, PLAYER_2_COLOR]
BALL_COLOR = 0xFFF1E8

BONUS_WIDTH = 10
BONUS_H_WIDTH = BONUS_WIDTH // 2
MAX_BALL_SLOPE = 3

# vars
g_now = 0

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
                self.state.state_on_start()
                return False
        return True



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
        self.time_created = g_now
        self.elapsed = 0
        self.active = True
        self.color_f = 1.0
        self.bad_bonus = False

    def init(self):
        self.y_pos = BONUS_H_WIDTH if self.player == 2 else self.state.disp.height - BONUS_H_WIDTH

    def do_step(self):
        if self.active:
            self.elapsed = infra.time_scaled(g_now - self.time_created)
            self.sprite.step_blit_to(self.state.disp.pixels, self.x_pos, self.y_pos)
            hit = self.state.p[self.player].hit_test(self.x_pos)
            if hit is not None:
                self.activate()
                self.active = False
            if self.elapsed > self.timeout:
                self.active = False
            return True
        else:
            self.color_f -= 0.1
            if self.color_f < 0:
                return False
            self.sprite.step_blit_to(self.state.disp.pixels, self.x_pos, self.y_pos, self.color_f)
            return True

class Bonus3Balls(Bonus):
    def init(self):
        super().init()
        self.sprite = self.state.res.balls_bonus_anim
        self.timeout = infra.time_scaled(2.5)

    def activate(self):
        print("Activated!")
        self.state.res.bonus_sound[self.player].play()
        #self.state.res.bonus_sound.play()
        self.state.split_balls()


class AI:
    def __init__(self, p, state):
        self.p = p  # player object
        self.dest_x_offset = None  # where I want to go
        self.step_num = 0
        self.state = state

    def step(self):
        self.step_num += 1
        # twice a second reevaluate your choices
        if (self.step_num % 30) == 0:
            # if we don't have a ball or if the the ball we were tracking is gone, choose a new one
            self.dest_x_offset = self.predict_next_ball_hit()
            #print("player", self.p.player, "predict", self.dest_x_offset)
            if self.dest_x_offset is None:  # nothing to do
                self.dest_x_offset = self.go_to_bonus()
            # randomize the hit point so that not all hits are the same and add a chance of failure
            if self.dest_x_offset is not None:
                self.dest_x_offset += infra.rand_unit() * PADDLE_H_WIDTH

        if self.dest_x_offset is None:
            return

        d = self.dest_x_offset - self.p.offset_x
        if abs(d) < 4:
            return
        if d < 0:
            self.p.move(-1)
        else:
            self.p.move(1)

    def go_to_bonus(self):
        bonus = self.state.get_player_bonus(self.p.player)
        if bonus is None or bonus.bad_bonus or bonus.elapsed < 1:  # don't go to it immediately
            return None
        return bonus.x_pos

    def predict_next_ball_hit(self):
        to_me_sign = 1 if self.p.player == 1 else -1
        min_steps = 9999
        min_s_pos = None
        for b in self.state.balls:
            if infra.sign(b.v.y) != to_me_sign:
                continue
            pos, num_steps = self.predict_ball_hit(b.copy())
            if pos is None:
                continue
            if num_steps < min_steps:
                min_steps = num_steps
                min_s_pos = pos
        return min_s_pos

    def predict_ball_hit(self, ball):
        for i in range(0, 100):
            self.state.ball_advance(ball)

            if self.p.player == 2:
                ball_top = ball.pos.y - BALL_OFFSET
                if ball_top <= PADDLE_HEIGHT:
                    return ball.pos.x, i
            elif self.p.player == 1:
                ball_bottom = ball.pos.y + BALL_OFFSET
                last_line = self.state.disp.height - 1
                if ball_bottom >= (last_line - PADDLE_HEIGHT):
                    return ball.pos.x, i
        return None, None


class Player:
    def __init__(self, wh, state, player, plid):
        self.offset_x = wh
        self.score = 0
        self.state = state
        self.player = player  # 1 or 2
        self.paddle_y = PADDLE_HEIGHT if player == 2 else (self.state.disp.height - 1 - PADDLE_HEIGHT)
        self.plid = plid
        if plid == PLID_AI:
            self.ai = AI(self, state)
        else:
            self.ai = None

    def hit_test(self, ball_pos_x):
        dist = ball_pos_x - self.offset_x
        adist = abs(dist)
        if adist <= PADDLE_H_WIDTH:
            return dist
        return None

    def move(self, sign):
        self.offset_x = self.limit_paddle(self.offset_x + sign * PADDLE_MOVE)

    def step(self):
        if self.state.user_input_enabled:
            self.move(self.state.joys.p(self.player).x)  # joy.x is either 0,1,-1
        if self.ai is not None and not self.state.ball_paused:  # would be suspicious if ai moved when the ball is paused since it's the start of the game
            self.ai.step()

    def limit_paddle(self, v):
        return min(max(v, PADDLE_WIDTH/2), self.state.disp.width-PADDLE_WIDTH/2)


class Ball:
    def __init__(self, x, y, vx, vy, speed):
        self.pos = infra.Vec2f(x, y)
        self.base_speed = speed
        self.v = infra.Vec2f(vx, vy)
        self.v.normalize(self.base_speed)
        self.remove = False

    def copy(self):
        return Ball(self.pos.x, self.pos.y, self.v.x, self.v.y, self.base_speed)



class Resources:
    def __init__(self):
        self.balls_bonus_anim = infra.AnimSprite(os.path.join(this_path, "balls_anim3/all.png"))
        self.menu_girl = infra.Sprite(os.path.join(infra.imgs_path, "girl_user.png"))
        self.menu_robot = infra.Sprite(os.path.join(infra.imgs_path, "robot_user.png"))

        self.bonus_sound = infra.by_player_audio(os.path.join(this_path, "audio/bonus_collect_PPP.ogg"))
        self.pops = infra.AudioDualGroup(os.path.join(this_path, f"audio/pop/_popIII_PPP.ogg"), 12)
        self.hits = infra.AudioDualGroup(os.path.join(this_path, f"audio/hit/_hitIII_PPP.ogg"), 5)
        self.crashes = infra.AudioDualGroup(os.path.join(this_path, f"audio/crash/_crashIII_PPP.ogg"), 7)

PLID_AI = 0
PLID_GIRL = 1

class PlayersMenu:
    def __init__(self, state):
        self.state = state
        self.p_sel = [None, state.p[1].plid, state.p[2].plid]
        self.sprites = [ self.state.res.menu_robot, self.state.res.menu_girl ]

    def draw(self):
        xmargin = 40
        ymargin = 25
        dw = self.state.disp.width
        dh = self.state.disp.height
        hdw = dw // 2
        hdh = dh // 2
        w = dw - xmargin*2
        h = dh - ymargin*2

        self.state.inf.draw.rect_a(xmargin + 1, ymargin + 1, w-1, h-1, 0xcc008751)
        self.state.inf.draw.round_rect(xmargin, ymargin, w, h, 0xffffff)

        self.sprites[self.p_sel[2]].blit_to_center(self.state.disp.pixels, hdw, hdh - 20)
        self.sprites[self.p_sel[1]].blit_to_center(self.state.disp.pixels, hdw, hdh + 20)

    def on_joy_event(self, eventObj):
        if eventObj.event in infra.JOY_ANY_ARROW:
            self.p_sel[eventObj.player] = (self.p_sel[eventObj.player] + 1) % 2
        if eventObj.event == infra.JOY_BTN_A or eventObj.event == infra.JOY_BTN_START:
            self.state.hide_players_menu()
            self.state.start_new_game(self.p_sel[1], self.p_sel[2])



class State(infra.BaseHandler):
    def __init__(self, inf, disp, joys):
        self.disp = disp
        self.joys = joys
        self.inf = inf
        self.res = Resources()
        self.start_new_game(PLID_AI, PLID_AI)  # let it play in the back of the menu
        self.show_players_menu()

    def show_players_menu(self):
        self.user_input_enabled = False
        self.menu = PlayersMenu(self)

    def hide_players_menu(self):
        self.user_input_enabled = True
        self.menu = None

    def on_joy_event(self, eventObj):
        if self.menu is not None:
            self.menu.on_joy_event(eventObj)
            return

        if eventObj.event == infra.JOY_BTN_START:
            self.show_players_menu()

    def start_new_game(self, p1_id, p2_id):
        print("new game:", p1_id, p2_id)
        wh = self.disp.width // 2
        self.p1 = Player(wh, self, 1, p1_id)
        self.p2 = Player(wh, self, 2, p2_id)
        self.p = [None, self.p1, self.p2]
        self.balls = []
        self.reset_ball()
        self.state_on_start()

        self.anims = []
        self.bonuses = []
        self.bonus_last_create_time = g_now

    def state_on_start(self):
        # waiting for any input at first, unless both are AI
        self.ball_paused = not (self.p1.plid == PLID_AI and self.p2.plid == PLID_AI)
        self.ball_visible = True
        self.input_enabled = True  # for both user and AI
        self.user_input_enabled = True

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
        self.bonus_last_create_time = g_now
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

        # after 5 seconds, good chance there's going to be a bonus in the next 3 second (this is called 60 times a second)
        if g_now - self.bonus_last_create_time < infra.time_scaled(7):
            return
        if int(random.random() * 7 * infra.PRINCIPLE_FPS) != 1:
            return
        print("creating bonus, time since last: ", g_now - self.bonus_last_create_time)

        player = 1 if random.random() > 0.5 else 2
        p = self.p[player]
        pos_min = p.offset_x - PADDLE_WIDTH
        pos_max = p.offset_x + PADDLE_WIDTH
        sel_pos = None
        for i in range(0, 10):
            pos = random.random() * (self.disp.width - BONUS_WIDTH) + BONUS_H_WIDTH
            if pos > pos_max or pos < pos_min:
                sel_pos = pos
                break
        if sel_pos is None:  # failed to find a spot
            return

        self.add_bonus(Bonus3Balls(player, sel_pos))

    def get_player_bonus(self, player):
        for b in self.bonuses:
            if b.player == player:
                return b
        return None

    def reset_ball(self):
        start_dir = 1 if random.random() > 0.5 else -1
        start_sidev = infra.rand_unit()
        ball = Ball(self.disp.width // 2, self.disp.height // 2, start_sidev, start_dir, BALL_START_SPEED)
        self.balls.append(ball)

    def split_balls(self):
        to_add = []
        for ball in self.balls:
            for b in range(0, 2):
                for i in range(0, 10):
                    vx = infra.rand_unit()
                    vy = infra.rand_unit()
                    # try again slope to not be too shallow
                    if abs(vx / vy) < MAX_BALL_SLOPE:
                        break

                to_add.append(Ball(ball.pos.x, ball.pos.y, vx, vy, ball.base_speed))

        for b in to_add:
            self.balls.append(b)
        print("number of balls:", len(self.balls))

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
        self.draw_player(self.p1.offset_x, 1, self.disp.height, PLAYER_1_COLOR)
        self.draw_player(self.p2.offset_x, -1, 0, PLAYER_2_COLOR)
        # draw ball
        if self.ball_visible:
            for ball in self.balls:
                self.inf.vdraw.circle(ball.pos.x, ball.pos.y, BALL_SZ / 2, BALL_COLOR)
        self.draw_scores()
        if self.menu is not None:
            self.menu.draw()
        self.disp.refresh()


    def ball_advance(self, ball):
        ball.pos.x += ball.v.x
        ball.pos.y += ball.v.y

        # side walls
        if ball.pos.x <= BALL_OFFSET:
            ball.pos.x = BALL_OFFSET
            ball.v.x = -ball.v.x
        if ball.pos.x >= self.disp.width - 1 - BALL_OFFSET:
            ball.pos.x = self.disp.width - 1 - BALL_OFFSET
            ball.v.x = -ball.v.x

    def ball_step(self, ball):
        self.ball_advance(ball)

        # top bottom walls
        # area where paddle can hit
        ball_top = ball.pos.y - BALL_OFFSET
        p2_hit_xdist = self.p2.hit_test(ball.pos.x)
        if ball_top <= PADDLE_HEIGHT and ball.v.y < 0 and p2_hit_xdist is not None:
            ball.pos.y = BALL_OFFSET + PADDLE_HEIGHT
            self.paddle_hit(p2_hit_xdist, 2, ball)
        elif ball_top < 0:
            self.crash(2, ball)

        # p1 hit
        ball_bottom = ball.pos.y + BALL_OFFSET
        last_line = self.disp.height - 1
        p1_hit_xdist = self.p1.hit_test(ball.pos.x)
        if ball_bottom >= (last_line - PADDLE_HEIGHT) and ball.v.y > 0 and p1_hit_xdist is not None:
            ball.pos.y = last_line - BALL_OFFSET - PADDLE_HEIGHT
            self.paddle_hit(p1_hit_xdist, 1, ball)
        elif ball_bottom > last_line:
            self.crash(1, ball)

    def paddle_hit(self, xdist, player, ball):
        ball.v.y = infra.sign(-ball.v.y)

        # the furthers it is from the center of the paddle the more random the direction can get
        off_center = (xdist / PADDLE_H_WIDTH)
        ball.v.x = 2 * off_center  # can be positive or negative
        ball.v.normalize(ball.base_speed)
        self.add_anim(AnimBallPaddle(ball.pos.copy(), PLAYER_COLOR[player]))

        self.res.pops.play(player)

    def crash(self, player, ball):
        ball.remove = True
        self.balls = [b for b in self.balls if not b.remove]
        if len(self.balls) > 0:
            self.res.hits.play(player)
            return

        if player == 1:
            self.p1.score += 1
        else:
            self.p2.score += 1
        self.res.crashes.play(player)
        self.add_anim(AnimBallOut_Fail(ball.pos.copy(), self))
        self.ball_paused = True
        self.ball_visible = False
        self.input_enabled = False
        self.reset_ball()

    def step(self):
        if not self.ball_paused:
            for ball in self.balls:
                self.ball_step(ball)
        elif self.input_enabled and self.user_input_enabled:
            self.ball_paused = self.joys.p1.x == 0 and self.joys.p2.x == 0

        if self.input_enabled:
            self.p1.step()
            self.p2.step()





def main(argv):
    global g_now
    g_now = time.time()
    inf = infra.infra_init()
    disp = inf.get_display()
    joys = inf.get_joystick_state()

    state = State(inf, disp, joys)

    disp.refresh()

    slow = False
    while True:
        if slow:
            time.sleep(0.5)
        if not inf.handle_events(state):
            break
        g_now = time.time()
        state.step()
        state.draw_board()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

