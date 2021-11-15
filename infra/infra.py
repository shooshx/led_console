import time, threading, os, math, ctypes
import sdl2.ext
from sdl2 import *
from sdl2.sdlmixer import *
import PIL.Image
import cairo

import infra_c

DISP_WIDTH = 128
DISP_HEIGHT = 128

this_dir = os.path.dirname(os.path.abspath(__file__))
imgs_path = os.path.join(this_dir, "imgs")

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
        self.surface = SDL_GetWindowSurface(self.window)

        self.pixels = infra_c.IntMatrix(DISP_WIDTH, DISP_HEIGHT)

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
    def ok_key_down_event(self, eventObj):
        return None
    def on_joy_event(self, eventObj):
        return None

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

keyboard_joy = {SDLK_UP: (PLAYER_1, JOY_UP),
                SDLK_LEFT: (PLAYER_1, JOY_LEFT),
                SDLK_RIGHT: (PLAYER_1, JOY_RIGHT),
                SDLK_DOWN: (PLAYER_1, JOY_DOWN),
                ord(']'): (PLAYER_1, JOY_BTN_A),
                ord('['): (PLAYER_1, JOY_BTN_B),
                ord('p'): (PLAYER_1, JOY_BTN_C),
                ord('o'): (PLAYER_1, JOY_BTN_D),
                ord('i'): (PLAYER_1, JOY_BTN_ESC),
                ord('u'): (PLAYER_1, JOY_BTN_START),

                ord('w'): (PLAYER_2, JOY_UP),
                ord('a'): (PLAYER_2, JOY_LEFT),
                ord('d'): (PLAYER_2, JOY_RIGHT),
                ord('s'): (PLAYER_2, JOY_DOWN),
                ord('z'): (PLAYER_2, JOY_BTN_A),
                ord('x'): (PLAYER_2, JOY_BTN_B),
                ord('c'): (PLAYER_2, JOY_BTN_C),
                ord('v'): (PLAYER_2, JOY_BTN_D),
                ord('b'): (PLAYER_2, JOY_BTN_ESC),
                ord('n'): (PLAYER_2, JOY_BTN_START),
                }
NonePair = (None,None)

class InfraSDL:
    def __init__(self):
        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_JOYSTICK | SDL_INIT_AUDIO)
        self.display = None
        self.joysticks = {}
        self.joy_by_player = {}
        self.last_events_tick = time.time()
        self.text = PicoFont()
        self.got_quit = False

        self.init_joysticks()
        self.init_sound()

    def get_display(self, show_fps=False, with_vector=False):
        if self.display is None:
            self.display = DisplaySDL(show_fps)
            self.draw = ShapeDraw(self.display)
            self.vdraw = VectorDraw(self.display) if with_vector else None
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
                # needs to be first so that the menu handler can dismiss menu on esc
                bret = handler.ok_key_down_event(event)
                if bret is not None:
                    return bret

                pl, ev = keyboard_joy.get(event.sym, NonePair)
                if pl is not None:
                    ji = self.joy_by_player[pl]
                    bret = self.do_joy_event(event, ev, ji, handler)
                    if bret is not None:
                        return bret

                if event.sym == SDLK_ESCAPE:
                    bret = self.joy_by_player[PLAYER_1].got_btn_down(JOY_BTN_ESC)
                    if bret is not None:
                        return bret


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
    def ok_key_down_event(self, event):
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



def infra_init(name):
    if name == "sdl":
        return InfraSDL()
    raise Exception("unknown infra " + name)

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
        for xi in range(xleft, xright+1):
            self.disp.set_pixel(xi, ytop, 0xffffff)
            self.disp.set_pixel(xi, ybot, 0xffffff)
        for yi in range(ytop, ybot+1):
            self.disp.set_pixel(xleft, yi, 0xffffff)
            self.disp.set_pixel(xright, yi, 0xffffff)

    def rect(self, xstart, ystart, w, h, c):
        self.disp.pixels.rect_fill(xstart, ystart, w, h, c)

    def rect_a(self, xstart, ystart, w, h, c):
        self.disp.pixels.rect_fill_a(xstart, ystart, w, h, c)

    def round_rect(self, xleft, ytop, w, h, c):
        ybot = ytop + h
        xright = xleft + w
        disp = self.disp
        for xi in range(xleft + 2, xright - 1):
            disp.set_pixel(xi, ytop, c)
            disp.set_pixel(xi, ybot, c)
        for yi in range(ytop + 2, ybot - 1):
            disp.set_pixel(xleft, yi, c)
            disp.set_pixel(xright, yi, c)
        disp.set_pixel(xleft + 1, ytop + 1, c)
        disp.set_pixel(xleft + 1, ybot - 1, c)
        disp.set_pixel(xright - 1, ytop + 1, c)
        disp.set_pixel(xright - 1, ybot - 1, c)


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



class Sprite:
    def __init__(self, filename):
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


# https://lazyfoo.net/SDL_tutorials/lesson11/index.php
class AudioChunk:
    def __init__(self, filename):
        self.wav = Mix_LoadWAV(filename.encode('utf-8'))
        assert self.wav.contents.alen > 0, "failed load " + filename + "  `" + Mix_GetError().decode('utf-8') + "`"
        #print("Loaded", filename)

    def play(self):
        Mix_PlayChannel(-1, self.wav, False)
