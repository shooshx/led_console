import sys, time, threading, os, math, ctypes, random, argparse
import sdl2.ext
from sdl2 import *
from sdl2.sdlmixer import *
import PIL.Image
import cairo
import scipy.io.wavfile
import numpy as np

import infra_c


DISP_WIDTH = 128
DISP_HEIGHT = 128

this_dir = os.path.dirname(os.path.abspath(__file__))
imgs_path = os.path.join(this_dir, "imgs")

COLOR_BLUE = 0x29ADFF
COLOR_RED = 0xFF004D
COLOR_YELLOW = 0xFFEC27
COLOR_GREEN = 0x00E436
BTN_COLORS = {'A':COLOR_BLUE, 'B':COLOR_RED, 'C':COLOR_YELLOW, 'D':COLOR_GREEN}


def color_hex2f(c):
    b = (c & 0xff)/255
    g = ((c >> 8) & 0xff)/255
    r = ((c >> 16) & 0xff)/255
    return r, g, b


BTN_COLORS_F = {k: color_hex2f(v) for k, v in BTN_COLORS.items()}

def color_f2hex(r, g, b):
    return min(int(b * 255), 255) | (min(int(g * 255), 255) << 8) | (min(int(r * 255), 255) << 16)

def color_mult(c, f):
    r, g, b = color_hex2f(c)
    return color_f2hex(r*f, g*f, b*f)


def check(ret):
    if ret != 0:
        raise Exception("Failed,", SDL_GetError())
        

class DictObj:
    def __init__(self, *pargs, **kwargs):
        if len(pargs) > 0:
            self.__dict__.update(pargs[0])
        self.__dict__.update(kwargs)
    def add(self, k, v):
        self.__dict__[k] = v
    def p(self, pi):
        return self.__dict__[pi]

def sign(v):
    return 1 if v >= 0 else -1

def rand_unit():
    return random.random()*2 - 1

class Vec2i:
    def __init__(self, x: float, y:float):
        self.x = x
        self.y = y

    def copy(self):
        return Vec2i(self.x, self.y)

    def equals(self, v):
        return self.x == v.x and self.y == v.y

class Vec2f:
    def __init__(self, x: float, y:float):
        self.x = x
        self.y = y
    def normalize(self, abs_len):
        l = math.sqrt(self.x*self.x + self.y*self.y)
        self.x *= abs_len / l
        self.y *= abs_len / l
    def copy(self):
        return Vec2f(self.x, self.y)
    def dist(self, v):
        dx = self.x - v.x
        dy = self.y - v.y
        return math.sqrt(dx*dx + dy*dy)

class BaseDisplay:
    def __init__(self, show_fps=False):
        if show_fps:
            self.fps = FpsShow()
        else:
            self.fps = NullFpsShow()

        self.pixels = infra_c.IntMatrix(DISP_WIDTH, DISP_HEIGHT)
        self.width = DISP_WIDTH
        self.height = DISP_HEIGHT
        self.rotate = 0

    def resized(self, w, h):
        pass

    def test_pattern(self):
        self.pixels.set(30, 30, 0xffffffff)
        for i in range(0, 127):
            self.pixels.set(i, i, 0xff00ffff)

    def destroy(self):
        self.fps.stop()

    def set_rotate(self, r):
        assert r >= 0 and r <= 3, "rotate out of range"
        self.rotate = r * 90

class DisplayBaseSDL(BaseDisplay):
    def __init__(self, show_fps=False):
        super().__init__(show_fps)          
        self.scr_width = 650
        self.scr_height = 540
        self.window = SDL_CreateWindow(b"title",
                                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                  self.scr_width, self.scr_height, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE)
        w = ctypes.c_int()
        h = ctypes.c_int()
        SDL_GetWindowSize(self.window, w, h)
        self.scr_width = w.value
        self.scr_height = h.value
        print("Created window", w.value, h.value)

        SDL_ShowCursor(SDL_DISABLE)

    def resized(self, w, h):
        self.scr_width = w
        self.scr_height = h

    def destroy(self):
        SDL_DestroyWindow(self.window)
        self.window = None
        super().destroy()


class DisplaySDL(DisplayBaseSDL):
    def __init__(self, show_fps=False):
        super().__init__(show_fps)
        self.surface = SDL_GetWindowSurface(self.window)

    def resized(self, w, h):
        super().resized(w, h)
        self.surface = SDL_GetWindowSurface(self.window)

    def destroy(self):
        self.surface = None

    def refresh(self):
        check(SDL_LockSurface(self.surface))

        ptr = self.surface.contents.pixels
        self.pixels.scale_to_screen(ptr, self.scr_width, self.scr_height)

        SDL_UnlockSurface(self.surface)
        check(SDL_UpdateWindowSurface(self.window))
        self.fps.inc()



class DisplaySDL_Render(DisplayBaseSDL):
    def __init__(self, show_fps=False):
        super().__init__(show_fps)

        count = SDL_GetNumRenderDrivers()
        for i in range(count):
            inf = SDL_RendererInfo()
            SDL_GetRenderDriverInfo(0, inf)
            print("render driver", i, inf.name)


        SDL_SetHint(b"SDL_RENDER_SCALE_QUALITY", b"nearest");
        self.rend = SDL_CreateRenderer(self.window, -1, 0) #SDL_RENDERER_ACCELERATED) SDL_RENDERER_PRESENTVSYNC
        print("renderer:", SDL_GetError())
        self.tex = SDL_CreateTexture(self.rend, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, DISP_WIDTH, DISP_HEIGHT)
        self.rect = SDL_Rect()
        self.calc_center()
        print("sdlr:", self.rend, self.tex, self.rect.w, self.rect.h)
        check(SDL_RenderClear(self.rend))


    def resized(self, w, h):
        super().resized(w, h)
        self.calc_center()

    def calc_center(self):
        if self.scr_width > self.scr_height:
            scale = self.scr_height // DISP_HEIGHT
        else:
            scale = self.scr_width // DISP_WIDTH

        fill_width = DISP_WIDTH * scale
        side_margin = (self.scr_width - fill_width) // 2
        fill_height = DISP_HEIGHT * scale
        top_margin = (self.scr_height - fill_height) // 2
        self.rect.x = side_margin
        self.rect.y = top_margin
        self.rect.w = fill_width
        self.rect.h = fill_height


    def refresh(self):
        #infra_c.render_matrix(self.pixels, self.rend, self.scr_width, self.scr_height)
        check(SDL_RenderClear(self.rend))
        check(SDL_UpdateTexture(self.tex, None, self.pixels.get_raw_ptr(), DISP_WIDTH*4))
        #check(SDL_RenderCopy(self.rend, self.tex, None, self.rect))
        check(SDL_RenderCopyEx(self.rend, self.tex, None, self.rect, self.rotate, None, False))

        SDL_RenderPresent(self.rend)
        self.fps.inc()

class DisplayNull(BaseDisplay):
    def refresh(self):
        self.fps.inc()



class BaseHandler:
    def on_key_down_event(self, eventObj):
        return None
    def on_joy_event(self, eventObj):
        return None

class Anim:
    def __init__(self):
        self.fnum = 0
        self.inf = None
        self.ctx = None
        self.remove = False
    def do_step(self):
        ret = self.step(self.fnum)
        self.fnum += 1
        return ret

class BaseState(BaseHandler):
    def __init__(self, inf):
        self.disp = inf.get_display()
        self.joys = inf.get_joystick_state()
        self.inf = inf
        self.anims = []

    def add_anim(self, anim):
        anim.inf = self.inf
        anim.ctx = self.inf.vdraw.ctx
        self.anims.append(anim)

    def run_anims(self):
        remove_any = False
        for a in self.anims:
            a.remove = not a.do_step()
            remove_any |= a.remove
        if remove_any:
            self.anims = [a for a in self.anims if not a.remove]


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
JOY_BTN_ESC = 14
JOY_BTN_START = 15

PLAYER_1 = 1
PLAYER_2 = 2

JOY_ANY_ARROW = [JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT]
JOY_ANY_LETTER = [JOY_BTN_A, JOY_BTN_B, JOY_BTN_C, JOY_BTN_D]



class JoystickInf:
    def __init__(self, j, player, infra):
        self.infra = infra
        self.j = j
        self.player = player # PLAYER_1 or PLAYER_2
        self.y = 0
        self.x = 0
        self.btn_A = False
        self.btn_B = False
        self.btn_C = False
        self.btn_D = False
        self.btn_Start = False

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
        elif b == JOY_BTN_START:
            self.btn_Start = True
        elif b == JOY_BTN_ESC:
            if self.infra is not None:
                return self.infra.modal_esc_menu()
        return None

    def got_btn_up(self, b):
        if b == JOY_BTN_A:
            self.btn_A = False
        elif b == JOY_BTN_B:
            self.btn_B = False
        elif b == JOY_BTN_C:
            self.btn_C = False
        elif b == JOY_BTN_D:
            self.btn_D = False
        elif b == JOY_BTN_START:
            self.btn_Start = False

# target for when a joystick disconnects
g_null_joystick = JoystickInf(None, 0, None)

class EvInf:
    def __init__(self, pl, ev, up_ev=None):
        self.pl = pl
        self.ev = ev
        self.up_ev = up_ev

keyboard_joy = {SDLK_UP: EvInf(PLAYER_1, JOY_UP, JOY_Y_CENTER),
                SDLK_LEFT: EvInf(PLAYER_1, JOY_LEFT, JOY_X_CENTER),
                SDLK_RIGHT: EvInf(PLAYER_1, JOY_RIGHT, JOY_X_CENTER),
                SDLK_DOWN: EvInf(PLAYER_1, JOY_DOWN, JOY_Y_CENTER),
                ord(']'): EvInf(PLAYER_1, JOY_BTN_A),
                ord('['): EvInf(PLAYER_1, JOY_BTN_B),
                ord('p'): EvInf(PLAYER_1, JOY_BTN_C),
                ord('o'): EvInf(PLAYER_1, JOY_BTN_D),
                ord('i'): EvInf(PLAYER_1, JOY_BTN_ESC),
                ord('u'): EvInf(PLAYER_1, JOY_BTN_START),

                ord('w'): EvInf(PLAYER_2, JOY_UP, JOY_Y_CENTER),
                ord('a'): EvInf(PLAYER_2, JOY_LEFT, JOY_X_CENTER),
                ord('d'): EvInf(PLAYER_2, JOY_RIGHT, JOY_X_CENTER),
                ord('s'): EvInf(PLAYER_2, JOY_DOWN, JOY_Y_CENTER),
                ord('z'): EvInf(PLAYER_2, JOY_BTN_A),
                ord('x'): EvInf(PLAYER_2, JOY_BTN_B),
                ord('c'): EvInf(PLAYER_2, JOY_BTN_C),
                ord('v'): EvInf(PLAYER_2, JOY_BTN_D),
                ord('b'): EvInf(PLAYER_2, JOY_BTN_ESC),
                ord('n'): EvInf(PLAYER_2, JOY_BTN_START),
                }

# filers out repeat
class KeyboardJoyAdapter:
    def __init__(self):
        self.down_keys = set()

    def key_down(self, sym):
        if sym in self.down_keys:  # filter repeat
            return None
        self.down_keys.add(sym)
        return keyboard_joy.get(sym, None)

    def key_up(self, sym):
        if sym not in self.down_keys:
            return  # can happen when we just start and process the up key of start up
        self.down_keys.remove(sym)
        return keyboard_joy.get(sym, None)

# add repeat for continuous joystick hold
class JoyRepeatFilter:
    def __init__(self):
        self.last_times = { JOY_LEFT: None, JOY_RIGHT: None, JOY_UP: None, JOY_DOWN: None}

    def _thresh_time(self, ev):
        if ev is None:
            return True
        now = time.time()
        if self.last_times[ev] is None:
            self.last_times[ev] = now
            return True
        elapsed = now - self.last_times[ev]
        #print("~~", elapsed)
        if elapsed > 0.250:
            self.last_times[ev] = now
            return True
        return False

    # return True if event should be taken
    def check(self, joy):
        evx = None
        if joy.x > 0:
            evx = JOY_RIGHT
        elif joy.x < 0:
            evx = JOY_LEFT
        else:  # reset
            self.last_times[JOY_RIGHT] = None
            self.last_times[JOY_LEFT] = None

        evy = None
        if joy.y > 0:
            evy = JOY_DOWN
        elif joy.y < 0:
            evy = JOY_UP
        else:
            self.last_times[JOY_UP] = None
            self.last_times[JOY_DOWN] = None

        if evx is not None:
            return self._thresh_time(evx)
        if evy is not None:
            return self._thresh_time(evy)




def parse_cmdline(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-show-fps", dest="show_fps", action="store_false", help="Show FPS")
    parser.add_argument("--disp", action="store", type=str, default="sdlr", choices=['sdl', 'sdlr', 'null', 'matrix'])
    parser.set_defaults(show_fps=True)
    opt = parser.parse_known_args(args)[0]
    return opt

class InfraSDL:
    def __init__(self, args):
        self.opt = parse_cmdline(args)
        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_JOYSTICK | SDL_INIT_AUDIO)
        self.display = None
        self.joysticks = {}
        self.joy_by_player = {}
        self.last_events_tick = time.time()
        self.text = PicoFont()
        self.got_quit = False
        self.key_joy = KeyboardJoyAdapter()

        self.init_joysticks()
        self.init_sound()

    def get_display(self):
        if self.display is None:
            if self.opt.disp == "sdl":
                self.display = DisplaySDL(self.opt.show_fps)
            elif self.opt.disp == "sdlr":
                self.display = DisplaySDL_Render(self.opt.show_fps)
            elif self.opt.disp == "null":
                self.display = DisplayNull(self.opt.show_fps)
            elif self.opt.disp == "matrix":
                import disp_rgbmatrix
                self.display = disp_rgbmatrix.DisplayMatrix(self.opt.show_fps)
            else:
                raise Exception("Unknown display kind " + self.opt.disp)
            print("display:", type(self.display))
            self.draw = ShapeDraw(self.display)
            self.vdraw = VectorDraw(self.display)
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
            j = JoystickInf(None, pl, self)
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

    def init_sound(self):
        Mix_OpenAudio(MIX_DEFAULT_FREQUENCY, MIX_DEFAULT_FORMAT, 2, 4096)
        Mix_Init(MIX_INIT_OGG)

    def get_joystick_state(self):
        return DictObj(self.joy_by_player)

    def do_joy_event(self, event, ev, ji, handler):
        if ev < JOY_BTN_A:
            ji.got_axis_keydown(ev)
        else:
            bret = ji.got_btn_down(ev)
            if bret is not None:
                return bret
        event.event = ev
        event.player = ji.player
        return handler.on_joy_event(event)

    def do_joy_up_event(self, event, ev, up_ev, ji, handler):
        if ev < JOY_BTN_A:
            ji.got_axis_keyup(ev)
        else:
            ji.got_btn_up(ev)
        event.event = up_ev
        event.player = ji.player
        handler.on_joy_event(event)

    def handle_events(self, handler):
        if self.got_quit:
            return False
        ev = infra_c.call_poll_events()
        for event in ev:
            #print("~event:", hex(event.type))
            if event.type == SDL_QUIT:
                self.got_quit = True
                return False
            if event.type == SDL_TEXTINPUT:
                pass
                #handler.on_key_event(event.text)
                #print("key:", event.text)

            elif event.type == SDL_JOYAXISMOTION:
                ji = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick axis:", j.player, event.axis, event.value)
                ev = ji.got_axis_event(event)
                bret = self.do_joy_event(event, ev, ji, handler)
                if bret is not None:
                    return bret

            elif event.type == SDL_JOYBUTTONDOWN:
                ji = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick button:", j.player, event.button)
                bret = self.do_joy_event(event, JOY_BTN_A + event.button, ji, handler)
                if bret is not None:
                    return bret

            elif event.type == SDL_JOYBUTTONUP:
                ji = self.joysticks.get(event.jid, g_null_joystick)
                #print("joystick button:", j.player, event.button)
                ji.got_btn_up(JOY_BTN_A + event.button)

            elif event.type == SDL_KEYDOWN:
                ev_inf = self.key_joy.key_down(event.sym)
                # needs to be first so that the menu handler can dismiss menu on esc
                bret = handler.on_key_down_event(event)
                if bret is not None:
                    return bret

                if ev_inf is not None:
                    ji = self.joy_by_player[ev_inf.pl]
                    bret = self.do_joy_event(event, ev_inf.ev, ji, handler)
                    if bret is not None:
                        return bret

                if event.sym == SDLK_ESCAPE:
                    bret = self.joy_by_player[PLAYER_1].got_btn_down(JOY_BTN_ESC)
                    if bret is not None:
                        return bret

            elif event.type == SDL_KEYUP:
                ev_inf = self.key_joy.key_up(event.sym)
                if ev_inf is not None:
                    ji = self.joy_by_player[ev_inf.pl]
                    self.do_joy_up_event(event, ev_inf.ev, ev_inf.up_ev, ji, handler)

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
        self.last_events_tick = ticks_now + max(wait, 0)
        if self.display is not None:
            self.display.fps.rec_wait(wait)

        return True

    def put_text(self, text, x, y, upside_down=False):
        self.text.put_text(self.display.pixels, text, x, y, upside_down)

    # returns None to do nothing, MENU_... for other things
    def modal_esc_menu(self):
        m = MenuEsc()

        while True:
            bret = self.handle_events(m)
            if bret is False:
                break
            if bret == MENU_QUIT_APP:
                return False
            self.draw.frame(20, 30, 128-40, 128-60)
            for opti, opt in enumerate(m.opt):
                x_offs = 0
                y = 40 + opti * (CHAR_HEIGHT + 3)
                if m.selected == opti:
                    self.put_text('\x17', 27, y)
                    x_offs = 1
                self.put_text(opt[0], 35 + x_offs, y)
            self.display.refresh()
        return True

MENU_QUIT_APP = 1001
MENU_CONT = 1002

class MenuBase(BaseHandler):
    def __init__(self, opts):
        self.selected = 0
        self.opt = opts
    def call_selected(self):
        return self.opt[self.selected][1]()
    def on_joy_event(self, ev):
        if ev.event == JOY_UP:
            if self.selected > 0:
                self.selected -= 1
        elif ev.event == JOY_DOWN:
            if self.selected < len(self.opt) - 1:
                self.selected += 1
        elif ev.event == JOY_BTN_A:
            return self.call_selected()
    def on_key_down_event(self, event):
        if event.sym == SDLK_RETURN:
            return self.call_selected()
        elif event.sym == SDLK_ESCAPE:
            return False  # same as continue


class MenuEsc(MenuBase):
    def __init__(self):
        super().__init__([("continue", self.on_cont), ("exit", self.on_exit)])
    def on_cont(self):
        return False
    def on_exit(self):
        return MENU_QUIT_APP


g_inf = None

def infra_init(args = sys.argv):
    global g_inf
    if g_inf is None:
        g_inf = InfraSDL(args)
    return g_inf

TARGET_FPS = 60.0
TARGET_FRAME_TIME = 1.0 / TARGET_FPS

# this is used for time dependent events that need to draw chance every frame
# not useing TARGET_FPS since I don't want them slowed down in high-fps mode
PRINCIPLE_FPS = 60
# in high-fps mode this is used for scaling any time contants
def time_scaled(period):
    return period * PRINCIPLE_FPS / TARGET_FPS

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





# image is made of 16x16 pixels grid

CHAR_HEIGHT = 5

this_dir = os.path.dirname(os.path.abspath(__file__))



class PicoFont:
    def __init__(self):
        img = PIL.Image.open(os.path.join(this_dir, "pico-8_font_022_real_size.png"))
        data = img.getdata()
        self.data = [(r | (g << 8) | (b << 16)) for r,g,b in data]
        self.data_width = img.width

    def put_text(self, m, text, out_x, out_y, upside_down=False):
        char_width = 3
        sign = 1
        if upside_down:
            sign = -1
            out_x += (char_width + 1) * len(text)
            out_y += CHAR_HEIGHT

        for c in text:
            if out_x + 3 > m.width():
                break
            c_num = ord(c)
            base_y = int(c_num / 16)*8
            base_x = int(c_num % 16)*8

            for cy in range(0, CHAR_HEIGHT):
                for cx in range(0, char_width):
                    color = self.data[(base_y + cy) * self.data_width + base_x + cx]
                    if color == 0:
                        continue
                    m.set(out_x + sign*cx, out_y + sign*cy, color | 0xff000000)
            out_x += sign*(char_width + 1)


class ShapeDraw:
    def __init__(self, disp):
        self.disp = disp

    def frame(self, xstart, ystart, w, h):
        self.rect(xstart, ystart, w, h, 0x0000ff)
        xend = xstart + w
        yend = ystart + h
        ytop = ystart + 1
        ybot = yend - 2
        xleft = xstart + 1
        xright = xend - 2
        disp = self.disp.pixels
        for xi in range(xleft, xright+1):
            disp.set(xi, ytop, 0xffffff)
            disp.set(xi, ybot, 0xffffff)
        for yi in range(ytop, ybot+1):
            disp.set(xleft, yi, 0xffffff)
            disp.set(xright, yi, 0xffffff)

    def rect(self, xstart, ystart, w, h, c):
        self.disp.pixels.rect_fill(xstart, ystart, w, h, c)

    def rect_a(self, xstart, ystart, w, h, c):
        self.disp.pixels.rect_fill_a(xstart, ystart, w, h, c)

    def round_rect(self, xleft, ytop, w, h, c, thick_corner=False):
        ybot = ytop + h
        xright = xleft + w
        disp = self.disp.pixels
        disp.ihline(xleft + 2, xright - 2, ytop, c)
        disp.ihline(xleft + 2, xright - 2, ybot, c)
        disp.ivline(xleft, ytop + 2, ybot - 2, c)
        disp.ivline(xright, ytop + 2, ybot - 2, c)

        disp.iset(xleft + 1, ytop + 1, c)
        disp.iset(xleft + 1, ybot - 1, c)
        disp.iset(xright - 1, ytop + 1, c)
        disp.iset(xright - 1, ybot - 1, c)

        if thick_corner:
            disp.iset(xleft + 1, ytop + 2, c)
            disp.iset(xleft + 2, ytop + 1, c)
            disp.iset(xleft + 2, ybot - 1, c)
            disp.iset(xleft + 1, ybot - 2, c)
            disp.iset(xright - 2, ytop + 1, c)
            disp.iset(xright - 1, ytop + 2, c)
            disp.iset(xright - 2, ybot - 1, c)
            disp.iset(xright - 1, ybot - 2, c)


class VectorDraw:
    def __init__(self, disp):
        self.disp = disp
        self.surface = cairo.ImageSurface.create_for_data(self.disp.pixels.get_memview(), cairo.FORMAT_ARGB32, self.disp.width, self.disp.height)
        self.ctx = cairo.Context(self.surface)

    def test_pattern(self):
        ctx = self.ctx
        ctx.scale(self.disp.width, self.disp.height)  # Normalizing the canvas

        pat = cairo.LinearGradient(0.0, 0.0, 0.0, 1.0)
        pat.add_color_stop_rgba(1, 0.7, 0, 0, 0.5)  # First stop, 50% opacity
        pat.add_color_stop_rgba(0, 0.9, 0.7, 0.2, 1)  # Last stop, 100% opacity

        ctx.rectangle(0, 0, 1, 1)  # Rectangle(x0, y0, x1, y1)
        ctx.set_source(pat)
        ctx.fill()

        ctx.translate(0.1, 0.1)  # Changing the current transformation matrix

        ctx.move_to(0, 0)
        # Arc(cx, cy, radius, start_angle, stop_angle)
        ctx.arc(0.2, 0.1, 0.1, -math.pi / 2, 0)
        ctx.line_to(0.5, 0.1)  # Line to (x,y)
        # Curve(x1, y1, x2, y2, x3, y3)
        ctx.curve_to(0.5, 0.2, 0.5, 0.4, 0.2, 0.8)
        ctx.close_path()

        ctx.set_source_rgb(0.3, 0.2, 0.5)  # Solid color
        ctx.set_line_width(0.02)
        ctx.stroke()

    def test_pattern2(self):
        ctx = self.ctx
        ctx.scale(self.disp.width, self.disp.height)

        ctx.move_to(0, 0)
        # Arc(cx, cy, radius, start_angle, stop_angle)
        ctx.arc(0.5, 0.5, 0.1, 0, math.pi * 2)
       # ctx.line_to(0.5, 0.1)  # Line to (x,y)
        # Curve(x1, y1, x2, y2, x3, y3)
       # ctx.curve_to(0.5, 0.2, 0.5, 0.4, 0.2, 0.8)
        ctx.close_path()

        ctx.set_source_rgb(0.3, 0.2, 0.5)  # Solid color
       # ctx.set_line_width(0.02)
       # ctx.stroke()
        ctx.fill()

    def set_color(self, c):
        b = (c & 0xff)/255
        g = ((c >> 8) & 0xff)/255
        r = ((c >> 16) & 0xff)/255
        self.ctx.set_source_rgb(r, g, b)

    def set_color_f(self, c, f):
        b = (c & 0xff)/255*f
        g = ((c >> 8) & 0xff)/255*f
        r = ((c >> 16) & 0xff)/255*f
        self.ctx.set_source_rgb(r, g, b)

    def circle(self, x, y, r, color):
        self.set_color(color)
        self.ctx.arc(x, y, r, 0, 2*math.pi)
        self.ctx.fill()

def star_path(ctx, x, y, r1, r2, np):
    dnp = math.pi / np

    ctx.move_to(x, y + r1)
    ang2 = dnp
    ctx.line_to(x + r2 * math.sin(ang2), y + r2 * math.cos(ang2))

    for i in range(1, np):
        di = i * 2
        ang1 = di * dnp
        ctx.line_to(x + r1 * math.sin(ang1), y + r1 * math.cos(ang1))
        ang2 = (di + 1) * dnp
        ctx.line_to(x + r2 * math.sin(ang2), y + r2 * math.cos(ang2))




class Sprite:
    def __init__(self, filename):
        assert os.path.exists(filename), "no such file " + filename
        self.img = infra_c.mat_from_image(filename)

    def blit_to(self, to_mat, dst_x, dst_y):
        to_mat.blit_from_sp(self.img, 0, 0, dst_x, dst_y, self.img.width(), self.img.height(), 1.0)

    def blit_to_center(self, to_mat, center_x, center_y):
        ytop = center_y - self.img.height() // 2
        xleft = center_x - self.img.width() // 2
        self.blit_to(to_mat, xleft, ytop)

# image made with make_anim.py
class AnimSprite:
    def __init__(self, filename):
        self.img = infra_c.mat_from_image(filename)
        # assume square
        self.h = self.img.width()
        self.hh = self.h // 2
        self.w = self.img.width()
        self.hw = self.w // 2
        self.fnum = int(self.img.height() / self.h)
        self.at_frame = 0

    def step_blit_to(self, to_mat, dst_x, dst_y, f = 1.0):
        dst_x -= self.hw  # position is center of the sprite
        dst_y -= self.hh
        to_mat.blit_from_sp(self.img, 0, self.at_frame * self.h, dst_x, dst_y, self.w, self.h, f)
        self.at_frame = (self.at_frame + 1) % self.fnum


P1_SIDE = "left"
P2_SIDE = "right"

def by_player_audio(pattern):
    p1 = pattern.replace('PPP', P1_SIDE)
    p2 = pattern.replace('PPP', P2_SIDE)
    assert os.path.exists(p1) and os.path.exists(p2), f"{p1},{p2}"
    return [None, AudioChunk(p1), AudioChunk(p2)]

# left, right, group of sounds
class AudioDualGroup:
    def __init__(self, pattern, count):
        self.d = [by_player_audio(pattern.replace('III', str(i))) for i in range(0, count)]
    def play(self, player):
        r = random.randrange(0, len(self.d))
        self.d[r][player].play()


buffer_from_memory = ctypes.pythonapi.PyMemoryView_FromMemory
buffer_from_memory.restype = ctypes.py_object

def sig_from_buf(chunk):
    rwav = scipy.io.wavfile.read(chunk.filename)
    fbuf = rwav[1]
    rbuf = fbuf.reshape(fbuf.shape[0] // ONLINE_BUF_SZ_F, ONLINE_BUF_SZ_F)
    smin = np.min(rbuf, axis=1)
    smax = np.max(rbuf, axis=1)
    sig = np.stack((smin, smax), axis=1)
    return sig

# https://lazyfoo.net/SDL_tutorials/lesson11/index.php
class AudioChunk:
    def __init__(self, filename):
        self.filename = filename
        self.wav = Mix_LoadWAV(filename.encode('utf-8'))
        assert self.wav.contents.alen > 0, "failed load " + filename + "  `" + Mix_GetError().decode('utf-8') + "`"

        fmt = AUDIO_F32
        chans = 2
        freq = 44100
        # bytes / samplesize == sample points
        points = (self.wav.contents.alen / ((fmt & 0xFF) / 8))
        # sample points / channels == sample frames
        frames = (points / chans)
        # (sample frames * 1000) / frequency == play length in s
        self.time = frames / freq

        self.count_playing = 0  # managed by MixTracker

    def play(self):
        return Mix_PlayChannel(-1, self.wav, False)

    def is_playing(self):
        return self.count_playing > 0

    def play_wait(self):
        Mix_PlayChannel(-1, self.wav, False)
        time.sleep(self.time)


buffer_from_memory = ctypes.pythonapi.PyMemoryView_FromMemory
buffer_from_memory.restype = ctypes.py_object
PyBUF_READ = 0x100
PyBUF_WRITE = 0x200

ONLINE_BUF_SZ = 4096  # byfes, don't change this
ONLINE_BUF_SZ_F = ONLINE_BUF_SZ // 4
DISP_WAVE_WIDTH = 128
SAMP_DISP_WIDTH = 32  # must divide by DISP_WAVE_WIDTH

# https://github.com/walshbp/pym/blob/9246bf7f222bb832ca8c03437475f2c733355452/examples/pym_sdl/pmSDL.py
# https://fossies.org/linux/SDL2/test/testaudiocapture.c

class AudioRecorder:
    def __init__(self, start_q: AudioChunk):
        self.start_q = start_q

        driver_name = SDL_GetCurrentAudioDriver()
        print("driver:", driver_name.decode('utf-8'))
        count = SDL_GetNumAudioDevices(True)
        for i in range(0, count):
            dev_name = SDL_GetAudioDeviceName(i, True)
            print(i, dev_name.decode('utf-8'))
        dev_name = None  # SDL_GetAudioDeviceName(2, True)

        # in windows with sdl 2.0.16 dll it crashes with 1 channel
        spec = SDL_AudioSpec(44100, AUDIO_F32, 1, 4096)

        obtained = SDL_AudioSpec(0, 0, 0, 0)

        self.devId = SDL_OpenAudioDevice(dev_name, True, spec, ctypes.byref(obtained), 0)
        self.spec = spec  # must keep a reference to these otherwise it crashes
        self.obtained = obtained
        assert self.devId != 0

        self.thread = None
        self.stop_thread = False
        self.save_filepath = None

        # online shape of the wave
        self.disp_wave = None
        self.dw_offset = 0
        self.sig_disp_wave = None  # list of (min, max), one for each 1024 samples

        # a visual signature of the last recorded
        self.did_save = False

    def close(self):
        SDL_CloseAudioDevice(self.devId)
        self.devId = None

    def make_disp_wave(self, fbuf):
        r = fbuf.reshape(DISP_WAVE_WIDTH, fbuf.shape[0] // DISP_WAVE_WIDTH)
        self.disp_wave = np.average(r, axis=1)

    def make_disp_wave2(self, fbuf):
        r = fbuf.reshape(SAMP_DISP_WIDTH, fbuf.shape[0] // SAMP_DISP_WIDTH)
        smin = np.min(r, axis=1)
        smax = np.max(r, axis=1)
        off = self.dw_offset
        self.disp_wave[off:off + SAMP_DISP_WIDTH, 0] = smin
        self.disp_wave[off:off + SAMP_DISP_WIDTH, 1] = smax
        self.dw_offset = (off + SAMP_DISP_WIDTH) % DISP_WAVE_WIDTH

        sboth = (np.min(fbuf), np.max(fbuf))
        self.sig_disp_wave.append(sboth)


    def data_thread(self):
        if self.start_q is not None:
            self.start_q.play_wait()

        SDL_PauseAudioDevice(self.devId, False)

        self.disp_wave = np.zeros((DISP_WAVE_WIDTH, 2))
        self.sig_disp_wave = []
        buffers = []
        bbuf = ctypes.create_string_buffer(ONLINE_BUF_SZ)
        while not self.stop_thread:
            dsz = SDL_DequeueAudio(self.devId, bbuf, ONLINE_BUF_SZ)
            dsz_f = dsz//4
            #print("got", dsz, dsz_f)
            if dsz > 0:
                fbuf_both = np.frombuffer(bbuf, np.float32, dsz_f)
                if self.spec.channels == 2:
                    fbuf = fbuf_both[0::2]
                else:
                    fbuf = fbuf_both
                buffers.append(fbuf)
                self.make_disp_wave2(fbuf)

                # recreate for the next sample
                bbuf = ctypes.create_string_buffer(ONLINE_BUF_SZ)

            if dsz < ONLINE_BUF_SZ:
                time.sleep(0.016)

        SDL_PauseAudioDevice(self.devId, True)

        if len(buffers) > 0:
            total_buf = np.concatenate(buffers)
            scipy.io.wavfile.write(self.save_filepath, 44100, total_buf)
            print("wrote", self.save_filepath, total_buf.shape, len(buffers))
            self.did_save = True
        else:
            print("no buffers to write")
            self.did_save = False
        self.disp_wave = None
        self.sig_disp_wave = None

    def start_online(self):
        assert self.thread is None
        self.stop_thread = False
        self.did_save = False
        self.thread = threading.Thread(target=self.data_thread)
        self.thread.start()

    def stop_online(self, filepath):
        if self.thread is None:
            return False
        self.save_filepath = filepath
        self.stop_thread = True
        self.thread.join()
        self.thread = None
        return self.did_save

    def start(self):
        SDL_PauseAudioDevice(self.devId, False)

    def stop(self, filepath):
        SDL_PauseAudioDevice(self.devId, True)

        sz = SDL_GetQueuedAudioSize(self.devId)
        if sz == 0:
            print("nothing recorded")
            return

        bbuf = ctypes.create_string_buffer(sz)
        dsz = SDL_DequeueAudio(self.devId, bbuf, sz)
        fbuf_both = np.frombuffer(bbuf, np.float32)

        if self.spec.channels == 2:
            fbuf = fbuf_both[0::2]
        else:
            fbuf = fbuf_both

        scipy.io.wavfile.write(filepath, 44100, fbuf)
        print("wrote", filepath, fbuf.shape)


CHANNEL_COUNT = 8

class MixTracker:
    def __init__(self):
        self.channels = [None] * CHANNEL_COUNT
        self.call_eff = Mix_EffectFunc_t(self.effect_call)
        self.call_done = Mix_EffectDone_t(self.channel_done)
        self.call_fin = channel_finished(self.channel_fin)

        Mix_ChannelFinished(self.call_fin)

        #for i in range(0, CHANNEL_COUNT):

        #    ret = Mix_RegisterEffect(i, self.call_eff, self.call_done, 0)
        #    if ret == 0:
        #        print(ret, Mix_GetError())

    def play(self, chunk):
        chan = chunk.play()
        chunk.count_playing += 1
        #Mix_RegisterEffect(chan, self.call_eff, self.call_done, 0)
        print("play in chan", chan)
        self.channels[chan] = chunk

    def effect_call(self, chan, ptr, len, ud):
        print("eff", chan)

    def channel_done(self, chan, ptr):
        print("done", chan)


    def channel_fin(self, chan):
        chunk = self.channels[chan]
        chunk.count_playing -= 1
        self.channels[chan] = None
        print("fin", chan, chunk.count_playing)



PLID_AI = 0
PLID_GIRL = 1
