import sys, os, random, collections, math
import cairo

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra
import infra_c

WIDTH = None
HEIGHT = None
MAX_SPEED = 5

# modify: colors, shapes, rotation, movement, line? letters?

class Shape:
    def __init__(self):
        self.c = None
        self.t = cairo.Matrix()
        self.speed = random.random() * MAX_SPEED


class Square(Shape):
    def __init__(self):
        super().__init__()
        x1 = random.random() * WIDTH
        y1 = random.random() * HEIGHT
        x2 = random.random() * WIDTH
        y2 = random.random() * HEIGHT
        self.tx = int(min(x1, x2))
        self.w = int(abs(x1 - x2))
        self.ty = int(min(y1, y2))
        self.h = int(abs(y1 - y2))
        self.x = self.tx + self.w * 0.5
        self.y = self.ty + self.h * 0.5

    def draw(self, ctx):
        ctx.rectangle(self.tx, self.ty, self.w, self.h)

class Circle(Shape):
    def __init__(self):
        super().__init__()
        self.r = random.random() * WIDTH * 0.3
        self.x = random.random() * WIDTH
        self.y = random.random() * HEIGHT

    def draw(self, ctx):
        ctx.arc(self.x, self.y, self.r, 0., 2 * math.pi)

class Star(Shape):
    def __init__(self):
        super().__init__()
        self.x = random.random() * WIDTH
        self.y = random.random() * HEIGHT
        self.r1 = random.random() * WIDTH * 0.3
        self.r2 = random.random() * WIDTH * 0.3
        self.np = random.randrange(5, 10)

    def draw(self, ctx):
        infra.star_path(ctx, self.x, self.y, self.r1, self.r2, self.np)

class Letter(Shape):
    def __init__(self):
        super().__init__()
        self.tx = random.random() * WIDTH
        self.ty = random.random() * HEIGHT
        self.g = chr(random.randint(ord('A'), ord('Z')))
        self.sz = random.randrange(8, 49)
        self.y = self.ty - self.sz*0.5
        self.x = self.tx + self.sz*0.4

    def draw(self, ctx):
        ctx.move_to(self.tx, self.ty)
        ctx.select_font_face("Purisa")
        ctx.set_font_size(self.sz)
        try:
            ctx.show_text(self.g)
        except:
            pass

MAX_ACTIVE_SHAPES = 60

class ColorRange:
    def __init__(self, start_h, end_h, start_v, end_v=None):
        self.start_h = start_h
        self.end_h = end_h
        self.start_v = start_v
        self.end_v = end_v

    def rand(self):
        h = random.uniform(self.start_h, self.end_h)
        if h > 1.0:
            h -= 1.0
        if self.end_v is None:
            v = self.start_v
        else:
            v = random.uniform(self.start_v, self.end_v)
        return infra_c.hsv_to_rgb(h, 1, v)

ALL_BRIGHT = ColorRange(0,1, 1)

class State(infra.BaseState):
    def __init__(self, inf):
        super().__init__(inf)
        self.enable_players_menu = False
        self.shapes = collections.deque()
        self.sel_shapes = [Square]
        self.sel_colors = [ALL_BRIGHT]
        self.fnum = 0

    def draw(self):
        ctx = self.inf.vdraw.ctx
        for s in self.shapes:
            ctx.set_source_rgb(s.c[0], s.c[1], s.c[2])
            ctx.set_matrix(s.t)
            s.draw(ctx)
            ctx.fill()
        self.disp.refresh()

    def update_sel_col(self):
        cols = []
        a = self.joys.p1.btn_A
        b = self.joys.p1.btn_B
        c = self.joys.p1.btn_C
        d = self.joys.p1.btn_D
        #print("col:", a, b, c, d)
        if a and b and c and d:
            cols = [ ALL_BRIGHT ]
        elif not a and not b and not c and not d:
            return  # unchanged
        else:
            if a:  # blue
                cols.append( ColorRange(0.55, 0.77, 0.6, 1) )
            if b:  # red
                cols.append( ColorRange(0.77, 1.05, 0.6, 1) )
            if c:  # yellow
                cols.append( ColorRange(0.05, 0.2, 0.7, 1) )
            if d:  # green
                cols.append( ColorRange(0.2, 0.55, 0.6, 1) )

        self.sel_colors = cols

    def update_sel_shape(self):
        shapes = []
        a = self.joys.p2.btn_A
        b = self.joys.p2.btn_B
        c = self.joys.p2.btn_C
        d = self.joys.p2.btn_D
        if not a and not b and not c and not d:
            return  # unchanged
        if a:
            shapes.append(Square)
        if b:
            shapes.append(Circle)
        if c:
            shapes.append(Star)
        if d:
            shapes.append(Letter)
        self.sel_shapes = shapes

    def update_move(self):
        x = self.joys.p1.x
        y = self.joys.p1.y
        if x == 0 and y == 0:
            return

        for s in self.shapes:
            s.t.translate(x * s.speed, y * s.speed)

    def update_rot_scale(self):
        x = self.joys.p2.x
        y = self.joys.p2.y
        if x != 0:
            for s in self.shapes:
                s.t.translate(s.x, s.y)
                s.t.rotate(x * s.speed*0.1)
                s.t.translate(-s.x, -s.y)
        if y > 0:
            for s in self.shapes:
                s.t.translate(s.x, s.y)
                s.t.scale(1+y*s.speed*0.02, 1)
                s.t.translate(-s.x, -s.y)
        if y < 0:
            for s in self.shapes:
                s.t.translate(s.x, s.y)
                s.t.scale(1, 1-y*s.speed*0.02)
                s.t.translate(-s.x, -s.y)

    def step(self):
        # add shape
        self.fnum += 1
        if self.fnum % 30 == 0:
            self.update_sel_col()
            self.update_sel_shape()

        self.update_move()
        self.update_rot_scale()

        #if self.fnum % 60 != 0:
        #    return

        shape_sel = random.randrange(0, len(self.sel_shapes))
        ctor = self.sel_shapes[shape_sel]
        shape = ctor()
        col_sel = random.randrange(0, len(self.sel_colors))
        shape.c = self.sel_colors[col_sel].rand()
        self.shapes.append(shape)
        if len(self.shapes) > MAX_ACTIVE_SHAPES:
            self.shapes.popleft()



def main(argv):
    inf = infra.infra_init()
    global WIDTH, HEIGHT

    state = State(inf)
    WIDTH = state.disp.width
    HEIGHT = state.disp.height

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()


if __name__ == "__main__":
    sys.exit(main(sys.argv))