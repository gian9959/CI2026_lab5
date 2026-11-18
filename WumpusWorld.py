from random import randint, sample

DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
ARROWS = {(-1, 0): "^", (1, 0): "v", (0, -1): "<", (0, 1): ">"}

BATCH_SIZE = 100

class WumpusWorld:
    def __init__(self, n_worlds=BATCH_SIZE):
        self.worlds = [World() for i in range(n_worlds)]
        self.player = None

class World:
    def __init__(self, n_pits=3, min_path_len=3, max_path_len=8, height=4, width=4):
        self.height = height
        self.width = width
        self.n_pits = n_pits
        self.pits = []
        self.player = Player()
        self.gold_pos = None
        self.wumpus_pos = None

        # random generation of a world

        # generate potential winning path so every world is "solvable"
        winning_path = [self.player.pos]
        path_len = randint(min_path_len, max_path_len)
        while len(winning_path) < path_len:
            direction = sample(list(DIRECTIONS.values()), 1)[0]
            tmp_pos = (winning_path[-1][0] + direction[0], winning_path[-1][1] + direction[1])
            if (0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width) and tmp_pos != self.player.pos:
                winning_path.append(tmp_pos)
        self.gold_pos = winning_path[-1]

        # generate wumpus
        while True:
            tmp_pos = (randint(0, self.height - 1), randint(0, self.width - 1))
            if tmp_pos not in winning_path:
                self.wumpus_pos = tmp_pos
                break

        # generate pits
        self.pits = []
        while len(self.pits) < self.n_pits:
            tmp_pos = (randint(0, self.height - 1), randint(0, self.width - 1))
            if tmp_pos not in winning_path and tmp_pos != self.wumpus_pos:
                self.pits.append(tmp_pos)

    def move_player(self):
        if 0 <= self.player.pos[0] < self.height and 0 <= self.player.pos[1] < self.width:
            self.player.move()
            return True
        return False

    def turn_player(self, new_direction):
        self.player.turn(new_direction)

    def print_world(self):
        for h in range(self.height):
            line = ""
            for w in range(self.width):
                char = "."
                tmp_pos = (h, w)
                match tmp_pos:
                    case self.player.pos:
                       char = ARROWS[self.player.p_dir]
                    case self.wumpus_pos:
                        char = "W"
                    case self.gold_pos:
                        char = "G"
                    case _:
                        if tmp_pos in self.pits:
                            char = "x"
                line += char
            print(line)
        print()

class Player:
    def __init__(self, pos=(3,0), p_dir=DIRECTIONS["right"]):
        self.pos = pos
        self.p_dir = p_dir
        self.has_gold = False
        self.has_arrow = False

    def move(self):
        self.pos = (self.pos[0] + self.p_dir[0], self.pos[1] + self.p_dir[1])

    def turn(self, new_dir):
        self.p_dir = new_dir


ww = WumpusWorld()
for w in ww.worlds:
    w.print_world()