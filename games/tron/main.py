import sys, os, random, collections

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra
import infra_c

this_path = os.path.dirname(os.path.abspath(__file__))

TAIL_LEN = 256

TYPE_MASK = 0xF0
TYPE_SIDE = 0x20
TYPE_REAL = 0x10
INDEX_MASK = 0xffff0000

class Player:
    def __init__(self, state, disp, player):
        self.state = state
        self.player = player  # 1 or 2
        self.pos = infra.Vec2f(int(disp.width/2), (disp.height*(0.9 if player == 1 else 0.1)))
        self.base_speed = 0.25
        self.v = infra.Vec2f(0, self.base_speed * (-1 if player == 1 else 1))
        self.color = infra.COLOR_BLUE if player == 1 else infra.COLOR_RED
        self.side_color = infra.color_mult(self.color, 0.5)

        self.tail = collections.deque()  # list of (x, y, step_index) ...
        self.last_posi = infra.Vec2i(-1, -1)
       # self.last_v = infra.Vec2f(0, 0)

        self.dist_in_v = 0  # distance traversed since last distance change - for avoiding sub-pixel turn arounds
        self.step_count = 0

    def set_v(self, vx, vy):
        if self.dist_in_v < 1:
            return
        self.v.x = vx
        self.v.y = vy
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



    def step(self):
        self.pos.x = (self.pos.x + self.v.x) % self.state.bwidth
        self.pos.y = (self.pos.y + self.v.y) % self.state.bheight

        self.dist_in_v += self.base_speed

        ix = int(self.pos.x)
        iy = int(self.pos.y)

        if ix == self.last_posi.x and iy == self.last_posi.y:
            return

        ex = self.state.board.get(ix, iy)

        self.tail.append((ix, iy, self.step_count))
        if len(self.tail) > TAIL_LEN:
            self.tail.popleft()
        self.step_count += 1

        self.last_posi.x, self.last_posi.y = ix, iy





class State(infra.BaseHandler):
    def __init__(self, inf, disp):
        self.disp = disp
        self.joys = inf.get_joystick_state()
        self.inf = inf
        # used for collision detection, side pixels
        # 0x11,0x01, 12,02 : players (center, side)
        self.board = infra_c.IntMatrix(self.disp.width, self.disp.height)
        self.p1 = Player(self, self.disp, 1)
        self.p2 = Player(self, self.disp, 2)
        self.p = [None, self.p1, self.p2]

        self.bwidth = disp.width
        self.bheight = disp.height

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


    def draw(self):
        self.disp.pixels.fill(0)
        self.draw_board()
        self.disp.refresh()

    def step(self):
        self.p1.step()
        self.p2.step()

    def on_joy_event(self, eventObj):
        p = self.p[eventObj.player]
        if eventObj.event == infra.JOY_UP:
            if p.v.y == 0:
                p.set_v(0, -p.base_speed)
        elif eventObj.event == infra.JOY_DOWN:
            if p.v.y == 0:
                p.set_v(0, p.base_speed)
        elif eventObj.event == infra.JOY_LEFT:
            if p.v.x == 0:
                p.set_v(-p.base_speed, 0)
        elif eventObj.event == infra.JOY_RIGHT:
            if p.v.x == 0:
                p.set_v(p.base_speed, 0)


def main(argv):
    inf = infra.infra_init()
    disp = inf.get_display()

    state = State(inf, disp)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()


if __name__ == "__main__":
    sys.exit(main(sys.argv))