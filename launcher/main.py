import sys, os, stat, glob, importlib.util, importlib, subprocess

this_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(this_path, "..", "infra"))
import infra

def import_file(filepath):
    name = os.path.splitext(os.path.split(filepath)[1])[0]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class App:
    def __init__(self, icon_file):
        self.main_func = None
        if os.path.exists(icon_file):
            self.icon = infra.Sprite(icon_file)
        else:
            self.icon = None

    def start(self):
        if self.main_func is None:
            self.main_func = self.get_main()
        self.main_func(sys.argv)

class PyApp(App):
    def __init__(self, main_mod_file, icon_file):
        super().__init__(icon_file)
        self.main_mod_file = main_mod_file

    def get_main(self):
        mod = import_file(self.main_mod_file)
        return mod.main

PICO8_ICON_PATH = os.path.join(this_path, "..", "pico8", "icon.png")

if sys.platform == "linux":
    PICO8_EXE = os.path.join(this_path, "../pico8/pico-8/pico8_dyn")
else:
    PICO8_EXE = os.path.join(this_path, r"..\pico8\pico-8\pico-8_0.2.3_windows\pico-8\pico8.exe")

def start_pico8(args):
    cmd = [PICO8_EXE] + args
    print(' '.join(cmd))
    subprocess.call(cmd)


class Pico8App(App):
    def __init__(self, cart_file, icon_file):
        super().__init__(icon_file)
        self.cart_file = cart_file

    def start(self):
        start_pico8(['-run', self.cart_file])

class Pico8SploreApp(App):
    def __init__(self):
        super().__init__(PICO8_ICON_PATH)

    def start(self):
        start_pico8(['-splore'])


BUTTONS_IN_LINE = 4
BTN_X_PITCH = 32
BTN_Y_PITCH = 33
BTN_WIDTH = 29
BTN_HEIGHT = 30

BTN_COLOR = 0x888888
BTN_SEL_COLOR = 0xdddddd

class State(infra.BaseHandler):
    def __init__(self, inf, disp):
        self.disp = disp
        self.joys = inf.get_joystick_state()
        self.inf = inf

        self.apps = []
        games = os.path.join(this_path, "..", "games")
        for path in glob.glob(os.path.join(games, "*")):
            if stat.S_ISDIR(os.stat(path).st_mode):
                mainpy = os.path.join(path, "main.py")
                if os.path.exists(mainpy):
                    self.apps.append(PyApp(mainpy, os.path.join(path, "icon.png")))

        self.apps.append(Pico8SploreApp())
        picos = os.path.join(this_path, "..", "pico8", "games")
        for modfile in glob.glob(os.path.join(picos, "*.py")):
            mod = import_file(modfile)
            self.apps.append(Pico8App(os.path.join(picos, mod.CART), os.path.join(picos, mod.ICON)))


        cur = []
        self.grid = [cur]  # list of lists
        for app in self.apps:
            cur.append(app)
            if len(cur) == 4:
                cur = []
                self.grid.append(cur)

        self.selected_coord = infra.Vec2i(0, 0)
        self.rep_filter_p1 = infra.JoyRepeatFilter()
        self.rep_filter_p2 = infra.JoyRepeatFilter()

    def draw(self):
        self.disp.pixels.fill(0)
        for y, line in enumerate(self.grid):
            for x, item in enumerate(line):
                rx = x * BTN_X_PITCH
                ry = y * BTN_Y_PITCH
                is_selected = self.selected_coord.x == x and self.selected_coord.y == y
                self.inf.draw.round_rect(rx + 1, ry + 1, BTN_WIDTH, BTN_HEIGHT, BTN_SEL_COLOR if is_selected else BTN_COLOR)
                if item.icon is not None:
                    item.icon.blit_to(self.disp.pixels, rx + 3, ry + 3)

                if is_selected:
                    self.inf.draw.round_rect(rx, ry, BTN_WIDTH + 2, BTN_HEIGHT + 2, BTN_SEL_COLOR, True)
        self.disp.refresh()

    def process_joy(self, joy, rep_filter):
        if not rep_filter.check(joy):
            return
        started = self.selected_coord.copy()
        sel_line_len = len(self.grid[self.selected_coord.y])
        if joy.x > 0:
            self.selected_coord.x = (self.selected_coord.x + 1) % sel_line_len
        elif joy.x < 0:
            self.selected_coord.x = (self.selected_coord.x - 1 + sel_line_len) % sel_line_len
        if joy.y != 0:
            if joy.y > 0 and self.selected_coord.y + 1 < len(self.grid):
                self.selected_coord.y += 1
            if joy.y < 0 and self.selected_coord.y > 0:
                self.selected_coord.y -= 1
            # adjust x if we reached a partial line
            sel_line_len = len(self.grid[self.selected_coord.y])
            if self.selected_coord.x >= sel_line_len:
                self.selected_coord.x = sel_line_len - 1
        return self.selected_coord.equals(started)


    def on_joy_event(self, eventObj):
        if eventObj.event == infra.JOY_BTN_A:
            app = self.grid[self.selected_coord.y][self.selected_coord.x]
            app.start()

    def step(self):
        if not self.process_joy(self.joys.p1, self.rep_filter_p1):
            self.process_joy(self.joys.p2, self.rep_filter_p2)





def main(args):
    inf = infra.infra_init(args)
    disp = inf.get_display()

    state = State(inf, disp)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()



if __name__ == "__main__":
    sys.exit(main(sys.argv))
