import threading, time, queue, array

from libc.string cimport memset
from libc.stdint cimport uintptr_t


cdef extern from "SDL2/include/SDL_events.h":
    ctypedef unsigned int Uint32
    ctypedef int Sint32
    ctypedef unsigned short Uint16
    ctypedef unsigned char Uint8

    cdef struct SDL_Keysym:
        int scancode
        int sym
        Uint16 mod

    cdef struct SDL_KeyboardEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        Uint8 state
        Uint8 repeat
        SDL_Keysym keysym

    cdef struct SDL_TextInputEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        char text[32]

    cdef struct SDL_WindowEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        Uint8 event
        Sint32 data1
        Sint32 data2

    cdef struct SDL_CommonEvent:
        Uint32 type
        Uint32 timestamp

    cdef union SDL_Event:
        Uint32 type
        SDL_CommonEvent common
        SDL_KeyboardEvent key
        SDL_TextInputEvent text
        SDL_WindowEvent window

    int SDL_PollEvent(SDL_Event* event)


class CommonEvent:
    def __init__(self, etype):
        self.type = etype

class KeyboardEvent:
    def __init__(self, etype, scancode, sym):
        self.type = etype
        self.scancode = scancode
        self.sym = sym

class DictObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TextInputEvent:
    def __init__(self, etype, text):
        self.type = etype
        self.text = text

class WindowEvent:
    def __init__(self, etype, event, data1, data2):
        self.type = etype
        self.event = event
        self.data1 = data1
        self.data2 = data2

def call_poll_events():
    cdef int ret
    cdef SDL_Event event
    cdef list lst = list()

    while SDL_PollEvent(&event) != 0:
        if event.type == 0x100:
            lst.append(CommonEvent(event.type))
        elif event.type == 0x200:
            lst.append(WindowEvent(event.type, event.window.event, event.window.data1, event.window.data2))
        elif event.type == 0x300 or event.type == 0x301:
            lst.append(KeyboardEvent(event.type, event.key.keysym.scancode, event.key.keysym.sym))
        elif event.type == 0x303:
            lst.append(TextInputEvent(event.type, event.text.text))

    return lst


cdef class IntMatrix:
    #cdef int w
    #cdef int h
    #cdef array.array d_mem
    #cdef unsigned int[:] d
    def __init__(self, int w, int h):
        self.w = w
        self.h = h
        self.reset()

    cpdef reset(self):
        #self.MatType = ctypes.c_uint32 * (self.w * self.h)
        self.d_mem = array.array('I', [0]*(self.w*self.h))
        self.d = self.d_mem

    cpdef set(self, int x, int y, unsigned int c):
        assert x >= 0 and x < self.w, f"width out of bounds {x}"
        assert y >= 0 and y < self.h, f"width out of bounds {y}"
        self.d[y * self.w + x] = c
    cpdef unsigned int get(self, int x, int y):
        return self.d[y * self.w + x]
    cpdef unsigned int mget(self, int x, int y):
        return self.d[(y % self.h) * self.w + (x % self.w)]
    cpdef fill(self, unsigned int v):
        memset(self.d_mem.data.as_voidptr, v, len(self.d_mem) * sizeof(int))

    cpdef scale_to_screen(self, uintptr_t scr_ptr_i, int scr_width, int scr_height):
        cdef int scale, fill_width, sides_margin, side_margin, fill_height, top_margin
        cdef int p, px, py, yi, xi
        cdef unsigned int* scr_ptr = <unsigned int*>scr_ptr_i

        if scr_width > scr_height:
            scale = scr_height // self.h
        else:
            scale = scr_width // self.w
        fill_width = self.w * scale
        sides_margin = (scr_width - fill_width)
        side_margin = (scr_width - fill_width) // 2
        fill_height = self.h * scale
        top_margin = (scr_height - fill_height) // 2

        p = top_margin * scr_width + side_margin

        for py in range(0, self.h):
            for yi in range(0, scale):
                for px in range(0, self.w):
                    c = self.d[py * self.w + px]
                    for xi in range(0, scale):
                        scr_ptr[p] = c
                        p += 1
                p += sides_margin

    cpdef blit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh):
        cdef int x, y
        for y in range(0, mh):
            for x in range(0, mw):
                self.set(dst_x + x, dst_y + y, src.get(x + src_x, y + src_y))
