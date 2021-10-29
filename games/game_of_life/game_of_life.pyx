import random, time


cimport infra_c


cdef int[8*2] AROUND_OFFSETS = [-1,-1, 0,-1, 1,-1,
                                -1,0,        1,0,
                                -1,1,  0,1,  1,1]

cdef list GLIDER_RD = [1,0, 2,1, 0,2, 1,2, 2,2]
cdef list GLIDER_LD = [1,0, 0,1, 0,2, 1,2, 2,2]

cdef dict PATTERNS = {
    "glider": GLIDER_RD
}

cdef unsigned int rand_color():
    cdef float r,g,b
    r,g,b = infra_c.hsv_to_rgb(random.random(), 1, 1)
    return int(r * 255) | (int(g * 255) << 8) | (int(b * 255) << 16)


cdef class GameOfLife:
    cdef infra_c.IntMatrix board
    cdef infra_c.IntMatrix next
    cdef int width, height, step_count
    cdef double last_time

    def __init__(self, w, h):
        self.board = infra_c.IntMatrix(w, h)
        self.next = infra_c.IntMatrix(w, h)
        self.width = w
        self.height = h
        self.step_count = 0
        self.last_time = time.time()

    def put_pattern(self, list p, int x, int y, color):
        for i in range(0, len(p), 2):
            self.board.mset(p[i] + x, p[i + 1] + y, color)

    def pattern_board(self, str name, float n, int do_color):
        cdef int x, y, i
        self.board.fill(0)
        if name == "random":
            for y in range(0, self.height):
                for x in range(0, self.width):
                    if random.random() > n:
                        self.board.set(x, y, rand_color() if do_color else 0xffffffff )
        elif name == "gliders":
            for i in range(0, int(n)):
                p = GLIDER_RD if random.random() > 0.5 else GLIDER_LD
                color = rand_color() if do_color else 0xffffffff
                self.put_pattern(p, random.random() * self.width, random.random() * self.height, color)
        else:
            self.put_pattern(PATTERNS[name], 0, 0)


    cdef process(self):
        cdef int x, y, c, nei, off_i, xoff, yoff
        cdef unsigned int nei_col
        cdef infra_c.Color new_col = infra_c.Color()
        cdef int alive
        self.next.fill(0)
        for y in range(0, self.width):
            for x in range(0, self.height):
                c = self.board.get(x, y)
                nei = 0
                new_col.reset()
                for off_i in range(0, 16, 2):
                    xoff = AROUND_OFFSETS[off_i]
                    yoff = AROUND_OFFSETS[off_i+1]
                    nei_col = self.board.mget(x + xoff, y + yoff)
                    if nei_col != 0:
                        nei += 1
                        new_col.add(nei_col)
                        #print("~~", new_col.r, new_col.g, new_col.g)

                alive = (c != 0 and (nei == 2 or nei == 3)) or (c == 0 and nei == 3)
                if alive:
                    new_col.div(nei)
                    #print("~~~~~~", new_col.r, new_col.g, new_col.g, hex(new_col.as_uint()))
                    new_col.hsv_stretch()

                    self.next.set(x, y, new_col.as_uint())

    def step(self):
        now = time.time()
        self.step_count += 1
        #print("step:", self.step_count, now - self.last_time)
        self.last_time = now
        self.process()
        self.board, self.next = self.next, self.board

    def get(self, x, y):
        return self.board.get(x, y)

    def get_board(self):
        return self.board