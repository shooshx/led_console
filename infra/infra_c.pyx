# cython: boundscheck=False, wraparound=False, initializedcheck=False, always_allow_keywords=False

import threading, time, queue, array, os, ctypes
import PIL.Image

from libc.string cimport memset
from libc.stdint cimport uintptr_t



cdef extern from "SDL_events.h":
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
        SDL_JoyButtonEvent jbutton

    int SDL_PollEvent(SDL_Event* event)

cdef extern from "SDL_rect.h":
    cdef struct SDL_Rect:
        int x
        int y
        int w
        int h

cdef extern from "SDL_render.h":
    ctypedef int SDL_Renderer
    int SDL_SetRenderDrawColor(SDL_Renderer* renderer, Uint8 r, Uint8 g, Uint8 b, Uint8 a)
    int SDL_RenderFillRect(SDL_Renderer* renderer, const SDL_Rect * rect)


class CommonEvent:
    def __init__(self, etype):
        self.type = etype

class KeyboardEvent:
    def __init__(self, etype, scancode, sym):
        self.type = etype
        self.scancode = scancode
        self.sym = sym

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


# same logic as scale_to_screen
def render_matrix(IntMatrix m, rend_ptr, int scr_width, int scr_height):
    cdef int scale, fill_width, side_margin, fill_height, top_margin
    cdef int px, py, r, g, b
    cdef SDL_Rect rect
    cdef SDL_Renderer* rend = <SDL_Renderer*><uintptr_t>ctypes.addressof(rend_ptr.contents)

    # memset(scr_ptr, 0x20, scr_width*scr_height*4)

    if scr_width > scr_height:
        scale = scr_height // m.h
    else:
        scale = scr_width // m.w
    fill_width = m.w * scale
    side_margin = (scr_width - fill_width) // 2
    fill_height = m.h * scale
    top_margin = (scr_height - fill_height) // 2

    rect.w = scale
    rect.h = scale
    rect.y = top_margin

    for py in range(0, m.h):
        rect.y += scale
        rect.x = side_margin
        for px in range(0, m.w):
            c = m.d[py * m.w + px]
            b = c & 0xff
            g = (c >> 8) & 0xff
            r = (c >> 16) & 0xff
            SDL_SetRenderDrawColor(rend, r, g, b, 255)
            rect.x += scale

            SDL_RenderFillRect(rend, &rect);



include "base_types.pyx"

IF UNAME_SYSNAME == "Linux":
    include "rgbmatrix_core.pxi"