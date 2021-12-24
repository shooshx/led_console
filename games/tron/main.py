import sys, os, random, collections, math, time
import cairo

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra
import infra_c

this_path = os.path.dirname(os.path.abspath(__file__))

TAIL_LEN = 256

TYPE_MASK = 0xF0
TYPE_SIDE = 0x20
TYPE_REAL = 0x10
INDEX_MASK = 0xffff0000

ARROW_LEN = 5
ARROW_WIDTH = 2.5


class CrashAnim(infra.Anim):
    def __init__(self, state, pos, player):
        super().__init__()
        self.pos = pos
        self.player = player
        self.state = state
        self.phase = 0
        self.r_in = 3
        self.p_color = infra.color_hex2f(self.player.color)
        self.p_color2 = infra.color_hex2f(self.player.side_color)
        self.color_f = 1.0

    def step(self, fnum):
        r_out = min(self.r_in * 2, self.r_in + 30)

        grad = cairo.RadialGradient(self.pos.x, self.pos.y, 5, self.pos.x, self.pos.y, 5 + math.sqrt(self.r_in) * 3)
        grad.add_color_stop_rgba(0,   self.p_color[0],  self.p_color[1],  self.p_color[2], self.color_f)
        grad.add_color_stop_rgba(0.8, self.p_color2[0], self.p_color2[1], self.p_color2[2], self.color_f)
        grad.set_extend(cairo.Extend.REFLECT)

        self.ctx.set_source(grad)
        infra.star_path(self.ctx, self.pos.x, self.pos.y, r_out, self.r_in, 20)
        self.ctx.fill_preserve()

        self.inf.vdraw.set_color(0xFFEC27)
        self.ctx.set_line_width(4.0)
        self.ctx.stroke()

        if self.phase == 0:
            self.r_in += 7
            if self.r_in > 150:
                self.phase = 1
        else:
            self.color_f -= 0.1
            if self.color_f <= 0:
                #self.state.state_on_start()
                return False

        return True

# absolute directions relative to player 1
DIR_UP = 0
DIR_DOWN = 1
DIR_LEFT = 2
DIR_RIGHT = 3

def rel_right_of(d):
    if d == DIR_UP:
        return DIR_RIGHT
    if d == DIR_DOWN:
        return DIR_LEFT
    if d == DIR_LEFT:
        return DIR_UP
    if d == DIR_RIGHT:
        return DIR_DOWN

def rel_left_of(d):
    if d == DIR_UP:
        return DIR_LEFT
    if d == DIR_DOWN:
        return DIR_RIGHT
    if d == DIR_LEFT:
        return DIR_DOWN
    if d == DIR_RIGHT:
        return DIR_UP

def v_for_d(d, s):
    if d == DIR_UP:
        return 0, -s
    elif d == DIR_DOWN:
        return 0, s
    elif d == DIR_LEFT:
        return -s, 0
    elif d == DIR_RIGHT:
        return s, 0

class AI:
    def __init__(self, player, state):
        self.player = player
        self.state = state

    def is_wall(self, ix, iy):
        ex = self.state.board.get(ix, iy)
        return ex & TYPE_MASK == TYPE_REAL

    def step(self):
        ix, iy = int(self.player.pos.x), int(self.player.pos.y)
        next_pos = self.player.pos.copy()
        self.player.advance_pos(next_pos, self.player.v)
        nix, niy = int(next_pos.x), int(next_pos.y)
        # chance for a random turn once in 5 seconds
        do_rand_turn = (int(random.random() * 60 * 5) == 1)

        if not do_rand_turn and ix == nix and iy == niy:  # not going to advance
            return

        # front is blocked?
        if not self.is_wall(nix, niy):
            if not do_rand_turn:
                return

        # left is blocked?
        d_rel_left = rel_left_of(self.player.cur_dir)
        v_left = v_for_d(d_rel_left, 1)
        lix, liy = ix + v_left[0], iy + v_left[1]
        left_blocked = self.is_wall(lix, liy)

        d_rel_right = rel_right_of(self.player.cur_dir)
        v_right = v_for_d(d_rel_right, 1)
        rix, riy = ix + v_right[0], iy + v_right[1]
        right_blocked = self.is_wall(rix, riy)

        if left_blocked and not right_blocked:
            self.player.set_v(d_rel_right)
        elif not left_blocked and right_blocked:
            self.player.set_v(d_rel_left)
        elif not left_blocked and not right_blocked:
            # if we're hitting a perpendicular line, check it's progress direction and go to the opposite, useful heuristic
            v_fwd = v_for_d(self.player.cur_dir, 1)
            flix, fliy = ix + v_left[0] + v_fwd[0], iy + v_left[1] + v_fwd[1]
            frix, friy = ix + v_right[0] + v_fwd[0], iy + v_right[1] + v_fwd[1]
            flex = self.state.board.get(flix, fliy)
            frex = self.state.board.get(frix, friy)

            if flex & TYPE_MASK == TYPE_REAL and frex & TYPE_MASK == TYPE_REAL:
                index_diff = ((flex & INDEX_MASK) >> 16) - ((frex & INDEX_MASK) >> 16)
                sel_dir = d_rel_right if (index_diff > 0) else d_rel_left
            else:
                sel_dir = d_rel_right if (random.random() > 0.5) else d_rel_left
            self.player.set_v(sel_dir)

        # if both are blocked nothing to do




class Player:
    def __init__(self, state, disp, player, plid):
        self.state = state
        self.player = player  # 1 or 2
        self.pos = infra.Vec2f(int(disp.width/2), (disp.height*(0.9 if player == 1 else 0.1)))
        self.base_speed = 0.25
        self.v = infra.Vec2f(0, self.base_speed * (-1 if player == 1 else 1))
        self.cur_dir = DIR_UP if player == 1 else DIR_DOWN
        self.color = infra.COLOR_BLUE if player == 1 else infra.COLOR_RED
        self.side_color = infra.color_mult(self.color, 0.5)

        self.tail = collections.deque()  # list of (x, y, step_index) ...
        self.last_posi = infra.Vec2i(-1, -1)
       # self.last_v = infra.Vec2f(0, 0)

        self.dist_in_v = 0  # distance traversed since last distance change - for avoiding sub-pixel turn arounds
        self.step_count = 0

        if plid == infra.PLID_AI:
            self.ai = AI(self, state)
        else:
            self.ai = None

    def set_v(self, dr):
        if self.dist_in_v < 1:
            return  # prevent very short Z turns
        vx, vy = v_for_d(dr, self.base_speed)
        self.v.x = vx
        self.v.y = vy
        self.cur_dir = dr
        self.dist_in_v = 0

    # don't want sides to erase real line
    def set_dpc(self, x, y, c):
        # write side pixels only if were not overwriting a real step
        ex = self.state.board.mget(x, y)
        typ = ex & TYPE_MASK
        if typ == TYPE_REAL:
            return
        if typ == TYPE_SIDE and c & INDEX_MASK < ex & INDEX_MASK:
            # side overrides only if it's a newer step
            return
        self.state.board.mset(x, y, c)

    def draw_tail(self):
        if len(self.tail) < 2:
            return
        t0 = self.tail[0]
        t1 = self.tail[1]
        v = infra.Vec2i(t0[0] - t1[0], t0[1] - t1[1])
        last_v = infra.Vec2i(0,0)
        last_pos = t0

        for pos in self.tail:
            ix, iy, step_idx = pos
            last_v.x, last_v.y = v.x, v.y
            v.x, v.y = pos[0] - last_pos[0], pos[1] - last_pos[1]

            idx_add = step_idx << 16
            self.state.board.set(ix, iy, TYPE_REAL | self.player | idx_add)

            if step_idx < self.step_count - 3:  # don't add the sides where the arrow comes
                dpc = TYPE_SIDE | self.player | idx_add
                if v.x == 0:
                    self.set_dpc(ix - 1, iy, dpc)
                    self.set_dpc(ix + 1, iy, dpc)
                if v.y == 0:
                    self.set_dpc(ix, iy - 1, dpc)
                    self.set_dpc(ix, iy + 1, dpc)

                # corners
                if v.x != last_v.x:  # enough to check this
                    add = []
                    if v.y == 0:  # turn left or right
                        yd = infra.sign(last_v.y)
                        xd = infra.sign(v.x)
                        add = [(-xd, yd), (-2 * xd, yd)]
                    elif v.x == 0:  # turn up or down
                        yd = infra.sign(last_v.x)
                        xd = infra.sign(v.y)
                        add = [(yd, -xd), (yd, -2 * xd)]

                    for axi, ayi in add:
                        self.set_dpc(ix + axi, iy + ayi, dpc)

            last_pos = pos


    def draw_bike(self):
        if len(self.tail) < 2:
            return
        ctx = self.state.inf.vdraw.ctx
        px, py, _ = self.tail[-1]
        bx, by, _ = self.tail[-(min(3, len(self.tail)))]

        d = infra.Vec2f(px - bx, py - by)
        if d.x > 10:  # over the edge
            d.x -= 128
        elif d.x < -10:
            d.x += 128
        if d.y > 10:
            d.y -= 128
        elif d.y < -10:
            d.y += 128

        d.normalize(1)
        r = infra.Vec2f(d.y, -d.x)

        px, py = px + 0.5 + d.x, py + 0.5 + d.y

        lpx, lpy = px - d.x*ARROW_LEN + r.x*ARROW_WIDTH, py - d.y*ARROW_LEN + r.y*ARROW_WIDTH
        rpx, rpy = px - d.x*ARROW_LEN - r.x*ARROW_WIDTH, py - d.y*ARROW_LEN - r.y*ARROW_WIDTH
        ctx.move_to(px, py)
        ctx.line_to(lpx, lpy)
        ctx.line_to(rpx, rpy)
        ctx.close_path()

        self.state.inf.vdraw.set_color(self.color)
        ctx.fill_preserve()
        self.state.inf.vdraw.set_color(self.side_color)
        ctx.set_line_width(1.0)
        ctx.stroke()


    def advance_pos(self, pos, v):
        pos.x = (pos.x + v.x) % self.state.bwidth
        pos.y = (pos.y + v.y) % self.state.bheight


    def step(self):
        if self.ai is not None:
            self.ai.step()

        self.advance_pos(self.pos, self.v)

        self.dist_in_v += self.base_speed

        ix = int(self.pos.x)
        iy = int(self.pos.y)

        if ix == self.last_posi.x and iy == self.last_posi.y:
            return

        ex = self.state.board.get(ix, iy)
        if ex & TYPE_MASK == TYPE_REAL:
            self.crash()

        self.tail.append((ix, iy, self.step_count))
        if len(self.tail) > TAIL_LEN:
            self.tail.popleft()
        self.step_count += 1

        self.last_posi.x, self.last_posi.y = ix, iy

    def crash(self):
        self.v.x, self.v.y = 0, 0
        self.state.add_anim(CrashAnim(self.state, self.pos.copy(), self))



class State(infra.BaseState):
    def __init__(self, inf):
        super().__init__(inf)
        # used for collision detection, side pixels
        # 0x11,0x01, 12,02 : players (center, side)
        self.board = infra_c.IntMatrix(self.disp.width, self.disp.height)
        self.p1 = Player(self, self.disp, 1, infra.PLID_GIRL)
        self.p2 = Player(self, self.disp, 2, infra.PLID_AI)
        self.p = [None, self.p1, self.p2]

        self.bwidth = self.disp.width
        self.bheight = self.disp.height
        self.slow = False


    def draw_board(self):
        self.board.fill(0)
        self.p1.draw_tail()
        self.p2.draw_tail()

        for y in range(self.bwidth):
            for x in range(self.bheight):
                v = self.board.get(x, y)
                if v == 0:
                    continue
                p = self.p[v & 0xF]
                c = p.color if (v & TYPE_MASK == TYPE_REAL) else p.side_color
                self.disp.pixels.set(x, y, c)

        self.p1.draw_bike()
        self.p2.draw_bike()

        self.run_anims()


    def draw(self):
        self.disp.pixels.fill(0)
        self.draw_board()
        self.disp.refresh()

    def step(self):
        if self.slow:
            time.sleep(0.5)
        self.p1.step()
        self.p2.step()

    def on_joy_event(self, eventObj):
        p = self.p[eventObj.player]
        if eventObj.event == infra.JOY_UP:
            if p.v.y == 0:
                p.set_v(DIR_UP)
        elif eventObj.event == infra.JOY_DOWN:
            if p.v.y == 0:
                p.set_v(DIR_DOWN)
        elif eventObj.event == infra.JOY_LEFT:
            if p.v.x == 0:
                p.set_v(DIR_LEFT)
        elif eventObj.event == infra.JOY_RIGHT:
            if p.v.x == 0:
                p.set_v(DIR_RIGHT)

    def on_key_down_event(self, eventObj):
        if eventObj.sym == ord('o'):
            self.slow = not self.slow

def main(argv):
    inf = infra.infra_init()

    state = State(inf)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()


if __name__ == "__main__":
    sys.exit(main(sys.argv))