import threading, time, queue, array

from libc.string cimport memset
from libc.stdint cimport uintptr_t


cdef extern from "SDL2/include/SDL_events.h":
    ctypedef unsigned int Uint32
    ctypedef int Sint32
    ctypedef unsigned short Uint16
    ctypedef short Sint16
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

    ctypedef Sint32 SDL_JoystickID

    cdef struct SDL_JoyAxisEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 axis
        Sint16 value

    cdef struct SDL_JoyButtonEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 button
        Uint8 state

    cdef struct SDL_CommonEvent:
        Uint32 type
        Uint32 timestamp

    cdef union SDL_Event:
        Uint32 type
        SDL_CommonEvent common
        SDL_KeyboardEvent key
        SDL_TextInputEvent text
        SDL_WindowEvent window
        SDL_JoyAxisEvent jaxis
        SDL_JoyButtonEvent jbutton;

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

class JoyAxisEvent:
    def __init__(self, etype, jid, axis, value):
        self.type = etype
        self.jid = jid
        self.axis = axis
        self.value = value

class JoyButtonEvent:
    def __init__(self, etype, jid, button):
        self.type = etype
        self.jid = jid
        self.button = button

def call_poll_events():
    cdef int ret
    cdef SDL_Event event
    cdef list lst = list()

    while SDL_PollEvent(&event) != 0:
        if event.type == 0x100:
            e = CommonEvent(event.type)
        elif event.type == 0x200:
            e = WindowEvent(event.type, event.window.event, event.window.data1, event.window.data2)
        elif event.type == 0x300 or event.type == 0x301:
            e = KeyboardEvent(event.type, event.key.keysym.scancode, event.key.keysym.sym)
        elif event.type == 0x303:
            e = TextInputEvent(event.type, event.text.text)
        elif event.type == 0x600: # SDL_JOYAXISMOTION
            e = JoyAxisEvent(event.type, event.jaxis.which, event.jaxis.axis, event.jaxis.value)
        elif event.type == 0x603 or event.type == 0x604:  # SDL_JOYBUTTONDOWN, SDL_JOYBUTTONUP
            e = JoyButtonEvent(event.type, event.jbutton.which, event.jbutton.button)
        else:
            e = CommonEvent(event.type)
        lst.append(e)

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
    cpdef mset(self, int x, int y, unsigned int c):
        self.d[(y % self.h) * self.w + (x % self.w)] = c

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

    cpdef mblit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh):
        cdef int x, y
        for y in range(0, mh):
            for x in range(0, mw):
                self.set(dst_x + x, dst_y + y, src.mget(x + src_x, y + src_y))



# from Lib
cdef float rgb_to_h(float r, float g, float b):
    cdef float maxc, minc, v, s, rc, gc, bc, h
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h

cdef (float, float, float) hsv_to_rgb(float h, float s, float v):
    cdef float f, p, q, t
    cdef int i
    if s == 0.0:
        return v, v, v
    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    # Cannot get here

cdef class Color:
    #cdef int r, g, b
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0
    cdef reset(self):
        self.r = 0
        self.g = 0
        self.b = 0
    cdef add(self, unsigned int c):
        self.r += c & 0xff
        self.g += (c >> 8) & 0xff
        self.b += (c >> 16) & 0xff
    cdef div(self, int n):
        self.r /= n
        self.g /= n
        self.b /= n

    cdef hsv_stretch(self):
        cdef float h, s, v, r, g, b
        if self.r == 255 and self.g == 255 and self.b == 255:
            return
        h = rgb_to_h(float(self.r) / 255.0, float(self.g) / 255.0, float(self.b) / 255.0)
        r,g,b = hsv_to_rgb(h, 1.0, 1.0)
        self.r = int(r * 255)
        self.g = int(g * 255)
        self.b = int(b * 255)

    cdef unsigned int as_uint(self):
        return self.r | (self.g << 8) | (self.b << 16) | 0xff000000

    cdef unsigned int as_uint_max(self):
        return min(self.r,255) | (min(self.g,255) << 8) | (min(self.b,255) << 16) | 0xff000000




