import ctypes
import sdl2.ext
from sdl2 import *

DISP_WIDTH = 128
DISP_HEIGHT = 128

def check(ret):
    if ret != 0:
        print("Failed,", SDL_GetError())

class DisplaySDL:
    def __init__(self):
        self.window = SDL_CreateWindow(b"Hello World",
                                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                  640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE)
        self.surface = SDL_GetWindowSurface(self.window)
        PixelsType = ctypes.c_uint32 * (DISP_HEIGHT * DISP_WIDTH)
        self.pixels = PixelsType()
        self.scr_width = 640
        self.scr_height = 480
        self.width = DISP_WIDTH
        self.height = DISP_HEIGHT

    def resized(self, w, h):
        self.surface = SDL_GetWindowSurface(self.window)
        self.scr_width = w
        self.scr_height = h

    def set_pixel(self, x, y, c):
        self.pixels[y * self.width + x] = c
        #self.pixels[y][x] = c

    def destroy(self):
        SDL_DestroyWindow(self.window)
        self.window = None
        self.surface = None

    def refresh(self):
        check(SDL_LockSurface(self.surface))

        if self.scr_width > self.scr_height:
            scale = self.scr_height // self.height
        else:
            scale = self.scr_width // self.width
        fill_width = DISP_WIDTH * scale
        sides_margin = (self.scr_width - fill_width)
        side_margin = (self.scr_width - fill_width) // 2
        fill_height = DISP_HEIGHT * scale
        top_margin = (self.scr_height - fill_height) // 2

        ptr = ctypes.cast(self.surface.contents.pixels, ctypes.POINTER(ctypes.c_uint32))

        p = top_margin * self.scr_width + side_margin

        for py in range(0, self.height):
            for yi in range(0, scale):
                for px in range(0, self.width):
                    c = self.pixels[py * self.width + px]
                    for xi in range(0, scale):
                        ptr[p] = c
                        p += 1
                p += sides_margin

        SDL_UnlockSurface(self.surface)
        check(SDL_UpdateWindowSurface(self.window))

class InfraSDL:
    def __init__(self):
        SDL_Init(SDL_INIT_VIDEO)
        self.display = None

    def get_display(self):
        if self.display is None:
            self.display = DisplaySDL()
        return self.display

    def destroy(self):
        SDL_Quit()
        if self.display is not None:
            self.display.destroy()

    def handle_events(self):
        event = SDL_Event()
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                return False
            if self.display is not None:
                if event.type == SDL_WINDOWEVENT:
                    if event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED:
                        self.display.resized(event.window.data1, event.window.data2)
                self.display.refresh()
        return True

def infra_init(name):
    if name == "sdl":
        return InfraSDL()
    raise Exception("unknown infra " + name)