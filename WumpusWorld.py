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
        self.player = Player()
        self.gold_pos = None
        self.wumpus_pos = None
        self.pits = []
        self.environment = []

        # random generation of a world

        # generate potential winning path so every world is "solvable"
        winning_path = [self.player.pos]
        path_len = randint(min_path_len, max_path_len)
        while len(winning_path) < path_len:
            direction = sample(list(DIRECTIONS.values()), 1)[0]
            tmp_pos = (winning_path[-1][0] + direction[0], winning_path[-1][1] + direction[1])
            if tmp_pos != self.player.pos and (0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width):
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

        # generate stench and breeze

        # generate grid
        for h in range(self.height):
            line = []
            for w in range(self.width):
                cell = []
                line.append(cell)
            self.environment.append(line)

        for d in DIRECTIONS.values():
            tmp_pos = (self.wumpus_pos[0] + d[0], self.wumpus_pos[1] + d[1])
            if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
                if "Stench" not in self.environment[tmp_pos[0]][tmp_pos[1]]:
                    self.environment[tmp_pos[0]][tmp_pos[1]].append("Stench")
        for p in self.pits:
            for d in DIRECTIONS.values():
                tmp_pos = (p[0] + d[0], p[1] + d[1])
                if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
                    if "Breeze" not in self.environment[tmp_pos[0]][tmp_pos[1]]:
                        self.environment[tmp_pos[0]][tmp_pos[1]].append("Breeze")


    def move_player(self):
        tmp_pos = (self.player.pos[0] + self.player.p_dir[0], self.player.pos[1] + self.player.p_dir[1])
        if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
            if tmp_pos not in self.pits and tmp_pos != self.wumpus_pos:
                self.player.pos = tmp_pos
                return True
            else:
                # game over
                return False
        raise Warning("Failed to move player as move was out of bounds")

    def turn_player(self, new_direction):
        self.player.p_dir = new_direction

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

ww = WumpusWorld()
for w in ww.worlds:
    w.print_world()