import ctypes, time, threading
import sdl2.ext
from sdl2 import *

import infra_c

DISP_WIDTH = 128
DISP_HEIGHT = 128

def check(ret):
    if ret != 0:
        print("Failed,", SDL_GetError())

class DictObj:
    def __init__(self, *pargs, **kwargs):
        if len(pargs) > 0:
            self.__dict__.update(pargs[0])
        self.__dict__.update(kwargs)
    def add(self, k, v):
        self.__dict__[k] = v
    def p(self, pi):
        return self.__dict__[pi]


class DisplaySDL:
    def __init__(self, show_fps=False):
        self.window = SDL_CreateWindow(b"title",
                                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                  640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE)
        self.surface = SDL_GetWindowSurface(self.window)

        self.pixels = infra_c.IntMatrix(DISP_WIDTH, DISP_HEIGHT)
        self.scr_width = 640
        self.scr_height = 480
        self.width = DISP_WIDTH
        self.height = DISP_HEIGHT
        if show_fps:
            self.fps = FpsShow()
        else:
            self.fps = NullFpsShow()

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
        self.fps.stop()

    def refresh(self):
        check(SDL_LockSurface(self.surface))

        ptr = self.surface.contents.pixels
        self.pixels.scale_to_screen(ptr, self.scr_width, self.scr_height)

        SDL_UnlockSurface(self.surface)
        check(SDL_UpdateWindowSurface(self.window))
        self.fps.inc()

    def test_pattern(self):
        self.set_pixel(30, 30, 0xffffffff)
        for i in range(0, 127):
            self.set_pixel(i, i, 0xff00ffff)

class BaseHandler:
    def on_key_event(self, key_code):
        pass
    def on_joy_event(self, eventObj):
        pass

JOY_UP = 1
JOY_DOWN = 2
JOY_LEFT = 3
JOY_RIGHT = 4
JOY_X_CENTER = 5
JOY_Y_CENTER = 6

JOY_BTN_A = 10
JOY_BTN_B = 11
JOY_BTN_C = 12
JOY_BTN_D = 13

PLAYER_1 = 1
PLAYER_2 = 2



class JoystickInf:
    def __init__(self, j, player):
        self.j = j
        self.player = player # PLAYER_1 or PLAYER_2
        self.y = 0
        self.x = 0
        self.btn_A = False
        self.btn_B = False
        self.btn_C = False
        self.btn_D = False

    def got_axis_event(self, event):
        if event.axis == 0:
            if event.value > 1000:
                ev = JOY_UP
                self.y = -1
            elif event.value < -1000:
                ev = JOY_DOWN
                self.y = 1
            else:
                ev = JOY_Y_CENTER
                self.y = 0
        elif event.axis == 1:
            if event.value > 1000:
                ev = JOY_RIGHT
                self.x = 1
            elif event.value < -1000:
                ev = JOY_LEFT
                self.x = -1
            else:
                ev = JOY_X_CENTER
                self.x = 0
        else:
            ev = None
        return ev

    def got_axis_keydown(self, ev):
        if ev == JOY_UP:
            self.y = -1
        elif ev == JOY_DOWN:
            self.y = 1
        elif ev == JOY_RIGHT:
            self.x = 1
        elif ev == JOY_LEFT:
            self.x = -1

    def got_axis_keyup(self, ev):
        if ev == JOY_UP or ev == JOY_DOWN:
            self.y = 0
        elif ev == JOY_RIGHT or ev == JOY_LEFT:
            self.x = 0

    def got_btn_down(self, b):
        if b == JOY_BTN_A:
            self.btn_A = True
        elif b == JOY_BTN_B:
            self.btn_B = True
        elif b == JOY_BTN_C:
            self.btn_C = True
        elif b == JOY_BTN_D:
            self.btn_D = True

    def got_btn_up(self, b):
        if b == JOY_BTN_A:
            self.btn_A = False
        elif b == JOY_BTN_B:
            self.btn_B = False
        elif b == JOY_BTN_C:
            self.btn_C = False
        elif b == JOY_BTN_D:
            self.btn_D = False


# target for when a joystick disconnects
g_null_joystick = JoystickInf(None, 0)

keyboard_joy = {SDLK_UP: (PLAYER_1, JOY_UP),
                SDLK_LEFT: (PLAYER_1, JOY_LEFT),
                SDLK_RIGHT: (PLAYER_1, JOY_RIGHT),
                SDLK_DOWN: (PLAYER_1, JOY_DOWN),
                ord(']'): (PLAYER_1, JOY_BTN_A),
                ord('['): (PLAYER_1, JOY_BTN_B),
                ord('p'): (PLAYER_1, JOY_BTN_C),
                ord('o'): (PLAYER_1, JOY_BTN_D),

                ord('w'): (PLAYER_2, JOY_UP),
                ord('a'): (PLAYER_2, JOY_LEFT),
                ord('d'): (PLAYER_2, JOY_RIGHT),
                ord('s'): (PLAYER_2, JOY_DOWN),
                ord('z'): (PLAYER_2, JOY_BTN_A),
                ord('x'): (PLAYER_2, JOY_BTN_B),
                ord('c'): (PLAYER_2, JOY_BTN_C),
                ord('v'): (PLAYER_2, JOY_BTN_D),
                }
NonePair = (None,None)

class InfraSDL:
    def __init__(self):
        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_JOYSTICK)
        self.display = None
        self.joysticks = {}
        self.joy_by_player = {}
        self.last_events_tick = time.time()


        self.init_joysticks()

    def get_display(self, show_fps=False):
        if self.display is None:
            self.display = DisplaySDL(show_fps)
        return self.display

    def destroy(self):
        SDL_Quit()
        if self.display is not None:
            self.display.destroy()

    # https://www.libsdl.org/release/SDL-1.2.15/docs/html/guideinput.html
    def init_joysticks(self):
        count = SDL_NumJoysticks()
        print(f"Found {count} joysticks")

        for pl in [PLAYER_1, PLAYER_2]:
            j = JoystickInf(None, pl)
            self.joy_by_player[pl] = j
            self.joy_by_player[f"p{pl}"] = j

        if count == 0:
            return
        SDL_JoystickEventState(SDL_ENABLE)
        for i in range(0, count):
            j = SDL_JoystickOpen(i)
            jid = SDL_JoystickInstanceID(j)
            print(i, ":", SDL_JoystickName(j), jid)
            p = PLAYER_1 + i
            ji = self.joy_by_player[p]
            self.joysticks[jid] = ji
            ji.j = j


    def get_joystick_state(self):
        return DictObj(self.joy_by_player)


    def handle_events(self, handler):
        ev = infra_c.call_poll_events()
        for event in ev:
            #print("~event:", hex(event.type))
            if event.type == SDL_QUIT:
                return False
            if event.type == SDL_TEXTINPUT:
                handler.on_key_event(event.text)
                #print("key:", event.text)

            elif event.type == SDL_JOYAXISMOTION:
                j = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick axis:", j.player, event.axis, event.value)
                event.player = j.player
                event.event = j.got_axis_event(event)
                handler.on_joy_event(event)

            elif event.type == SDL_JOYBUTTONDOWN:
                j = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick button:", j.player, event.button)
                event.player = j.player
                event.event = JOY_BTN_A + event.button
                j.got_btn_down(b)
                handler.on_joy_event(event)
            elif event.type == SDL_JOYBUTTONUP:
                j = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick button:", j.player, event.button)
                b = JOY_BTN_A + event.button
                j.got_btn_up(b)

            elif event.type == SDL_KEYDOWN:
                pl, ev = keyboard_joy.get(event.sym, NonePair)
                if pl is not None:
                    ji = self.joy_by_player[pl]
                    if ev < JOY_BTN_A:
                        ji.got_axis_keydown(ev)
                    else:
                        ji.got_btn_down(ev)
                        event.event = ev
                        event.player = pl
                        handler.on_joy_event(event)
            elif event.type == SDL_KEYUP:
                pl, ev = keyboard_joy.get(event.sym, NonePair)
                if pl is not None:
                    ji = self.joy_by_player[pl]
                    if ev < JOY_BTN_A:
                        ji.got_axis_keyup(ev)
                    else:
                        ji.got_btn_up(ev)

            elif event.type == SDL_WINDOWEVENT:
                if self.display is not None:
                    if event.event == SDL_WINDOWEVENT_SIZE_CHANGED:
                        self.display.resized(event.data1, event.data2)


        ticks_now = time.time()
        passed = ticks_now - self.last_events_tick
        wait = TARGET_FRAME_TIME - passed
        #print("~~~", passed, wait)
        if wait > 0:
            time.sleep(wait)
        self.last_events_tick = ticks_now + wait
        self.display.fps.rec_wait(wait)


        return True


def infra_init(name):
    if name == "sdl":
        return InfraSDL()
    raise Exception("unknown infra " + name)

TARGET_FRAME_TIME = 1.0 / 60.0

class FpsShow:
    def __init__(self):
        self.count = 0
        self.wait_sum = 0
        self.wait_count = 0

        self.last_count = 0
        self.do_stop = False
        self.t = threading.Thread(target=self.fps_thread)
        self.t.daemon = True # don't keep the program running
        self.t.start()

    def inc(self):
        self.count += 1
    def rec_wait(self, v):
        self.wait_sum += v
        self.wait_count += 1
    def stop(self):
        self.do_stop = True
    def fps_thread(self):
        while not self.do_stop:
            time.sleep(1)
            c = self.count
            avg_wait = (self.wait_sum/self.wait_count * 1000) if self.wait_count > 0 else 0
            print(f"fps: {c - self.last_count} ({avg_wait:.1f})")
            self.last_count = c
            self.wait_sum = 0
            self.wait_count = 0


class NullFpsShow:
    def inc(self):
        pass
    def stop(self):
        pass
    def rec_wait(self, v):
        pass

