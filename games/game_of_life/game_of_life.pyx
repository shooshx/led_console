import ctypes, random, time

from cpython cimport array
import array
from libc.string cimport memset

cdef class IntMatrix:
    cdef int w
    cdef int h
    cdef array.array d_mem
    cdef int[:] d
    def __init__(self, int w, int h):
        self.w = w
        self.h = h
        self.reset()
    cdef reset(self):
        #self.MatType = ctypes.c_uint32 * (self.w * self.h)
        self.d_mem = array.array('i', [0]*(self.w*self.h))
        self.d = self.d_mem
    cdef set(self, int x, int y, int c):
        self.d[y * self.w + x] = c
    cdef int get(self, int x, int y):
        return self.d[y * self.w + x]
    cdef mget(self, int x, int y):
        return self.d[(y % self.h) * self.w + (x % self.w)]
    cdef fill(self, int v):
        memset(self.d_mem.data.as_voidptr, v, len(self.d_mem) * sizeof(int))


cdef int[8*2] AROUND_OFFSETS = [-1,-1, 0,-1, 1,-1,
                                -1,0,        1,0,
                                -1,1,  0,1,  1,1]


cdef class GameOfLife:
    cdef IntMatrix board
    cdef IntMatrix next
    cdef int width, height, step_count
    cdef double last_time

    def __init__(self, w, h):
        self.board = IntMatrix(w, h)
        self.next = IntMatrix(w, h)
        self.width = w
        self.height = h
        self.step_count = 0
        self.last_time = time.time()

    def rand_board(self):
        self.board.reset()
        for y in range(0, self.height):
            for x in range(0, self.width):
                if random.random() > 0.5:
                    self.board.set(x, y, 0xffffffff)

    cdef process(self):
        cdef int x, y, c, nei, off_i, xoff, yoff
        cdef int alive
        self.next.fill(0)
        for y in range(0, self.width):
            for x in range(0, self.height):
                c = self.board.get(x, y)
                nei = 0
                for off_i in range(0, 16, 2):
                    xoff = AROUND_OFFSETS[off_i]
                    yoff = AROUND_OFFSETS[off_i+1]
                    if self.board.mget(x + xoff, y + yoff) != 0:
                        nei += 1
                alive = (c != 0 and (nei == 2 or nei == 3)) or (c == 0 and nei == 3)
                if alive:
                    self.next.set(x, y, 0xffffffff)

    def step(self):
        now = time.time()
        self.step_count += 1
        print("step:", self.step_count, now - self.last_time)
        self.last_time = now
        self.process()
        self.board, self.next = self.next, self.board

    def get(self, x, y):
        return self.board.get(x, y)