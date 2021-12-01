import sys, os, random

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra"))
import infra

this_path = os.path.dirname(os.path.abspath(__file__))

class Player:
    def __init__(self, state, disp, player):
        self.state = state
        self.player = player  # 1 or 2
        self.pos = infra.Vec2f(int(disp.width/2), (disp.height*(0.9 if player == 1 else 0.1)))
        self.base_speed = 0.5
        self.v = infra.Vec2f(0, self.base_speed * (-1 if player == 1 else -1))
        self.color = infra.COLOR_BLUE if player == 1 else infra.COLOR_RED


    def step(self):
        self.pos.x += self.v.x
        self.pos.y += self.v.y

        ex = self.state.board.get(self.pos.x, self.pos.y)

        self.state.board.set(self.pos.x, self.pos.y, self.player * 10)




class State:
    def __init__(self, inf, disp):
        self.disp = disp
        self.joys = inf.get_joystick_state()
        self.inf = inf
        # need a separate board from pixels since pixels also has more visual stuff
        # 10,11, 20,21 : players (center, side)
        self.board = infra.IntMatrix(self.disp.width, self.disp.height)
        self.p1 = Player(self, self.disp, 1)
        self.p2 = Player(self, self.disp, 2)
        self.p = [None, self.p1, self.p2]

    def draw_board(self):
        pass
        #for

    def draw(self):
        self.draw_board()

    def step(self):
        self.p1.step()
        self.p2.step()


def main(argv):
    inf = infra.infra_init()
    disp = inf.get_display()

    state = State(inf, disp)

    while True:
        if not inf.handle_events(state):
            break
        state.step()
        state.draw()


