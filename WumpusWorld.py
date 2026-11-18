from random import randint, sample

DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

class WumpusWorld:
    def __init__(self, n_worlds=100):
        self.worlds = [w for w in range(n_worlds)]
        self.player = None

class World:
    def __init__(self, n_pits=3, min_path_len=3, max_path_len=8, height=4, width=4):
        self.height = height
        self.width = width
        self.n_pits = n_pits
        self.pits = []
        self.player_pos = (3,0)
        self.gold_pos = None
        self.wumpus_pos = None

        # random generation of a world

        # generate potential winning path so every world is "solvable"
        winning_path = [self.player_pos]
        path_len = randint(min_path_len, max_path_len)
        while len(winning_path) < path_len:
            direction = sample(list(DIRECTIONS.values()), 1)[0]
            tmp_pos = (winning_path[-1][0] + direction[0], winning_path[-1][1] + direction[1])
            if (tmp_pos[0] <= self.height and tmp_pos[1] <= self.width) and (tmp_pos != self.player_pos):
                winning_path.append(tmp_pos)
        self.gold_pos = winning_path[-1]

        # generate wumpus
        while True:
            tmp_pos = (randint(0, self.height - 1), randint(0, self.width - 1))
            if tmp_pos not in winning_path and tmp_pos != self.player_pos:
                self.wumpus_pos = tmp_pos
                break

        # generate pits
        self.pits = []
        while len(self.pits) < self.n_pits:
            tmp_pos = (randint(0, self.height - 1), randint(0, self.width - 1))
            if tmp_pos not in winning_path and tmp_pos != self.player_pos and tmp_pos != self.wumpus_pos:
                self.pits.append(tmp_pos)

ww = WumpusWorld()