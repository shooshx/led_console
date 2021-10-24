import ctypes, time
import sdl2.ext
from sdl2 import *

import infra_callc

DISP_WIDTH = 128
DISP_HEIGHT = 128

def check(ret):
    if ret != 0:
        print("Failed,", SDL_GetError())

class DisplaySDL:
    def __init__(self):
        self.window = SDL_CreateWindow(b"title",
                                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                  640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE)
        self.surface = SDL_GetWindowSurface(self.window)

        self.pixels = infra_callc.IntMatrix(DISP_WIDTH, DISP_HEIGHT)
        self.scr_width = 640
        self.scr_height = 480
        self.width = DISP_WIDTH
        self.height = DISP_HEIGHT

    def resized(self, w, h):
        self.surface = SDL_GetWindowSurface(self.window)
        self.scr_width = w
        self.scr_height = h

    def set_pixel(self, x, y, c):
        self.pixels.set(x, y, c)
        #self.pixels[y][x] = c

    def destroy(self):
        SDL_DestroyWindow(self.window)
        self.window = None
        self.surface = None

    def refresh(self):
        check(SDL_LockSurface(self.surface))

        ptr = self.surface.contents.pixels
        self.pixels.scale_to_screen(ptr, self.scr_width, self.scr_height)



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

    def handle_events_s(self):
        count = 0
        start = time.time()
        while True:
            event = infra_callc.get_queued_event()
            if event is None:
                break
            count += 1
            if event.type == SDL_QUIT:
                return False
            if event.type == SDL_TEXTINPUT:
                print("key:", event.text)

            elif self.display is not None:
                if event.type == SDL_WINDOWEVENT:
                    if event.event == SDL_WINDOWEVENT_SIZE_CHANGED:
                        self.display.resized(event.data1, event.data2)
                self.display.refresh()

        if count > 0:
            print("handled events:", count, time.time() - start)
        return True

    def handle_events(self):
        ev = infra_callc.call_poll_events()
        for event in ev:
            if event.type == SDL_QUIT:
                return False
            if event.type == SDL_TEXTINPUT:
                print("key:", event.text)

            elif self.display is not None:
                if event.type == SDL_WINDOWEVENT:
                    if event.event == SDL_WINDOWEVENT_SIZE_CHANGED:
                        self.display.resized(event.data1, event.data2)
            self.display.refresh()

        return True


def infra_init(name):
    if name == "sdl":
        return InfraSDL()
    raise Exception("unknown infra " + name)