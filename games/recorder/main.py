import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra

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
        self.filename = os.path.join(this_path, '_recs', f'rec_p{self.player}_{self.label}.wav')
        self.selected = False
        self.wav = None

    def draw(self):
        ytop = 1 if self.player == 2 else (self.state.disp.height - SLOT_HEIGHT - 2)
        xleft = (3 - self.xpos) * SLOT_PITCH + 1
        if self.selected:
            self.state.inf.draw.rect(xleft, ytop, SLOT_WIDTH+1, SLOT_HEIGHT+1, SEL_FILL)
            self.state.inf.draw.round_rect(xleft-1, ytop-1, SLOT_WIDTH+2, SLOT_HEIGHT+2, SEL_LINE)
        self.state.inf.draw.round_rect(xleft, ytop, SLOT_WIDTH, SLOT_HEIGHT, infra.BTN_COLORS[self.label])


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
            self.recs[pl].start()
        elif eventObj.event == infra.JOY_Y_CENTER:
            slot = self.sel_slot[pl]
            print("rec stop player", pl, "slot", slot.xpos)
            filename = slot.filename
            self.recs[pl].stop(filename)
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


    def step(self):
        pass

    def draw(self):
        self.disp.pixels.fill(0)
        for s in self.slots:
            s.draw()
        self.disp.refresh()

# SDL_RWFromMem, Mix_LoadWAV_RW

def main(argv):
    inf = infra.infra_init("sdl")
    disp = inf.get_display(show_fps=False, with_vector=True)

    state = State(inf, disp)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()

# TBD
# ???? flush small buffer?
# mabe just use util?
# close device

if __name__ == "__main__":
    sys.exit(main(sys.argv))
