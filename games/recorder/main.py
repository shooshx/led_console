import sys, os, math, random

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra, cairo

this_path = os.path.dirname(os.path.abspath(__file__))

SLOT_HEIGHT = 30
SLOT_WIDTH = 29
SLOT_PITCH = 32
SEL_LINE = 0x909090
SEL_FILL = 0x404040

class Slot:
    def __init__(self, state, label, xpos, player):
        self.state = state
        self.label = label  # A,B,C,D like the button names
        self.xpos = xpos
        self.player = player  # 1,2

        self.ytop = 1 if self.player == 2 else (self.state.disp.height - SLOT_HEIGHT - 2)
        self.xleft = (3 - self.xpos) * SLOT_PITCH + 1

        self.filename = os.path.join(this_path, '_recs', f'rec_p{self.player}_{self.label}.wav')
        self.selected = False
        self.wav = None
        self.color = infra.BTN_COLORS[self.label]

        self.saved_sig = None


    def draw_sig(self, selected):
        acc_data = self.saved_sig
        if selected:
            cur_disp = self.state.recs[self.player].acc_disp_wave
            if cur_disp is not None:
                self.saved_sig = cur_disp
                acc_data = cur_disp
        if acc_data is None:
            return

        center_x = self.xleft + 15
        center_y = self.ytop + 15
        ctx = self.state.inf.vdraw.ctx

        r, g, b = infra.BTN_COLORS_F[self.label]
        samp_i = 0

        ctx.set_operator(cairo.OPERATOR_SCREEN)

        for v_amp, v_col in acc_data:
            bx, by = SIG_BASE[samp_i % SIG_LINE_COUNT]
            samp_i += 1
            # amplitude variance
            av_amp = abs(v_amp)*50
            x = bx * av_amp
            y = by * av_amp
            # color variance
            cf = abs(v_col) * 100
            ctx.set_source_rgba(r * cf, g * cf, b * cf, 0.5)
            ctx.move_to(center_x + 0.5, center_y + 0.5)
            ctx.rel_line_to(x, y)
            ctx.stroke()
        if selected and samp_i > 0:
            self.state.disp.pixels.mset(center_x + bx, center_y + by, 0xeeeeee)

        ctx.set_operator(cairo.OPERATOR_OVER)

    def draw(self):
        if self.selected:
            self.state.inf.draw.rect(self.xleft, self.ytop, SLOT_WIDTH+1, SLOT_HEIGHT+1, SEL_FILL)
            self.state.inf.draw.round_rect(self.xleft-1, self.ytop-1, SLOT_WIDTH+2, SLOT_HEIGHT+2, SEL_LINE)
        self.state.inf.draw.round_rect(self.xleft, self.ytop, SLOT_WIDTH, SLOT_HEIGHT, self.color)
        self.draw_sig(self.selected)


SIG_LINE_COUNT = 32
SIG_LINE_LEN = 9
def make_sig_base():
    l = []
    for i in range(0, SIG_LINE_COUNT):
        x = math.sin(i / SIG_LINE_COUNT * math.pi * 2) * SIG_LINE_LEN
        y = math.cos(i / SIG_LINE_COUNT * math.pi * 2) * SIG_LINE_LEN
        l.append((x,y))
    return l

SIG_BASE = make_sig_base()

class State(infra.BaseHandler):
    def __init__(self, inf, disp):
        self.disp = disp
        self.joys = inf.get_joystick_state()
        self.inf = inf

        self.p1_rec = infra.AudioRecorder()
        self.p2_rec = infra.AudioRecorder()
        self.recs = [None, self.p1_rec, self.p2_rec]
        self.p1_slots = [Slot(self, 'A', 0, 1), Slot(self, 'B', 1, 1), Slot(self, 'C', 2, 1), Slot(self, 'D', 3, 1)]
        self.p2_slots = [Slot(self, 'D', 0, 2), Slot(self, 'C', 1, 2), Slot(self, 'B', 2, 2), Slot(self, 'A', 3, 2)]
        self.p_slots = [None, self.p1_slots, self.p2_slots]
        self.slots = self.p1_slots + self.p2_slots  # all in one list

        self.sel_slot = [None, None, None]
        self.select_slot(1, 0)
        self.select_slot(2, 3)

    def select_slot(self, player, slot_xpos):
        if self.sel_slot[player] is not None:
            self.sel_slot[player].selected = False
        if slot_xpos == -1:
            self.sel_slot[player] = None
            return
        s = self.p_slots[player][slot_xpos]
        s.selected = True
        self.sel_slot[player] = s


    def on_joy_event(self, eventObj):
        pl = eventObj.player
        if eventObj.event == infra.JOY_UP:
            print("rec start!", pl)
            self.recs[pl].start_online()

        elif eventObj.event == infra.JOY_Y_CENTER:
            slot = self.sel_slot[pl]
            print("rec stop player", pl, "slot", slot.xpos)
            filename = slot.filename
            did_save = self.recs[pl].stop_online(filename)
            if did_save:
                slot.wav = infra.AudioChunk(filename)

        elif eventObj.event == infra.JOY_LEFT or eventObj.event == infra.JOY_RIGHT:
            dx = -1 if eventObj.event == infra.JOY_RIGHT else 1
            new_xpos = (self.sel_slot[pl].xpos + dx) % 4
            self.select_slot(pl, new_xpos)

        elif eventObj.event in infra.JOY_ANY_LETTER:
            xpos = eventObj.event - infra.JOY_BTN_A
            if pl == 2:
                xpos = 3 - xpos
            slot = self.p_slots[pl][xpos]
            if slot is not None:
                if slot.wav is not None:
                    slot.wav.play()
                else:
                    print("Player", pl, "Slot", xpos, "is empty")

    def draw_rec_wave(self, rec, ybase):
        w = rec.disp_wave
        if w is None:
            return
        for x, samp in enumerate(w):
            y = ybase + samp*50
            self.disp.pixels.set(x, y, 0xffffff)

    def draw_rec_wave2(self, rec, ybase, color):
        ybase += 0.5
        w = rec.disp_wave
        if w is None:
            return
        for x, samp in enumerate(w):
            ya = ybase + samp[0] * 40
            yb = ybase + samp[1] * 40
            self.disp.pixels.vline(x, ya, yb, color)


    def draw(self):
        self.disp.pixels.fill(0)
        for s in self.slots:
            s.draw()
        self.draw_rec_wave2(self.p1_rec, 80, self.sel_slot[1].color)
        self.draw_rec_wave2(self.p2_rec, 48, self.sel_slot[2].color)
        self.disp.refresh()

    def step(self):
        pass


def main(argv):
    inf = infra.infra_init()
    disp = inf.get_display(show_fps=False, with_vector=True)

    state = State(inf, disp)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()

# TBD
# close device
# repeat
# rec dings
# load existing files

if __name__ == "__main__":
    sys.exit(main(sys.argv))
