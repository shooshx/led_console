# cython: boundscheck=False, wraparound=False, initializedcheck=False, always_allow_keywords=False

import random, time
import cython

#cimport infra_c

# this is done so that IntMatrix and Color could be inlined
include "../../infra/base_types.pyx"


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
    r,g,b = hsv_to_rgb(random.random(), 1, 1)
    return int(r * 255) | (int(g * 255) << 8) | (int(b * 255) << 16) | 0xff000000

cdef int cell_alive(unsigned int c):
    #return c != 0
    # this produces better C code than with 0xff, and we only need 1 bit anyway
    return (c & 0x7f000000) != 0

cdef class GameOfLife:
    cdef IntMatrix board
    cdef IntMatrix next
    cdef int width, height
    cdef double last_time

    def __init__(self, w, h):
        self.board = IntMatrix(w, h)
        self.next = IntMatrix(w, h) 
        self.width = w
        self.height = h
        self.last_time = time.time()

    def put_pattern(self, list p, int x, int y, color):
        for i in range(0, len(p), 2):
            self.next.c_mset(p[i] + x, p[i + 1] + y, color)

    def pattern_board(self, str name, float n, int do_color):
        cdef int x, y, i
        self.next.fill(0)
        if name == "random":
            for y in range(0, self.height):
                for x in range(0, self.width):
                    if random.random() > n:
                        self.next.c_set(x, y, rand_color() if do_color else 0xffffffff )
        elif name == "gliders":
            for i in range(0, int(n)):
                p = GLIDER_RD if random.random() > 0.5 else GLIDER_LD
                color = rand_color() if do_color else 0xffffffff
                self.put_pattern(p, random.random() * self.width, random.random() * self.height, color)
        else:
            color = rand_color() if do_color else 0xffffffff
            self.put_pattern(PATTERNS[name], 0, 0, color)
        self.flip()

    cdef process(self, float fade):
        cdef int x, y, nei, off_i, xoff, yoff, c_alive
        cdef unsigned int nei_col, c, nc
        cdef Color new_col = Color()
        cdef int keep_alive, do_fade = fade != 0
        self.next.fill(0)
        for y in range(0, self.width):
            for x in range(0, self.height):
                c = self.board.c_get(x, y)
                c_alive = cell_alive(c)
                nei = 0
                new_col.reset()
                for off_i in range(0, 16, 2):
                    xoff = AROUND_OFFSETS[off_i]
                    yoff = AROUND_OFFSETS[off_i+1]
                    nei_col = self.board.c_mget(x + xoff, y + yoff)
                    if cell_alive(nei_col):
                        nei += 1
                        new_col.add(nei_col)

                keep_alive = (c_alive and (nei == 2 or nei == 3)) or ((not c_alive) and nei == 3)
                if keep_alive:
                    new_col.div(nei)
                    new_col.hsv_stretch()

                    self.next.c_uset(x, y, new_col.as_uint() | 0x7f000000)
                elif do_fade:
                    new_col.set(c)
                    new_col.mult(fade)
                    nc = new_col.as_uint() & 0xffffff
                    self.next.c_uset(x, y, nc)
        #print("~~~~~~")


    def step(self, fade):
        now = time.time()
        #print("step:", self.step_count, now - self.last_time)
        self.last_time = now
        self.process(fade)
        self.flip()

    def flip(self):
        self.board, self.next = self.next, self.board

    def get(self, x, y):
        return self.board.c_get(x, y)

    def get_board(self):
        return self.board