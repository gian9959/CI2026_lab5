from LCS import LCS
from random import randint, sample

DIRECTIONS = {"up": (-1, 0), "right": (0, 1), "down": (1, 0), "left": (0, -1)}
ARROWS = {(-1, 0): "^", (0, 1): ">", (1, 0): "v", (0, -1): "<"}

START_POS = (3, 0)

MAX_STEPS = 100

# REWARDS
R_STEP = -1
R_SHOOT = -10
R_DEATH = -1000
R_WIN = 1000

BATCH_SIZE = 1000

class WumpusWorld:
    def __init__(self, n_worlds=BATCH_SIZE):
        self.training_set = [Level() for _ in range(n_worlds)]
        self.validation_set = [Level() for _ in range(n_worlds)]
        self.lcs = LCS()

        self.stats = {"WINS": 0, "LOSSES": 0, "FAILED": 0}

    def play_level(self, level, train):
        self.lcs.reset()
        percepts = level.player_perception()
        total = 0.0
        end = False
        while not end:
            action = self.lcs.act(percepts, train)
            percepts, reward, end = level.step(action)
            if train:
                self.lcs.reinforce(reward, end)
            total += reward
        match level.outcome:
            case "SUCCESS":
                self.stats["WINS"] += 1
            case "DEAD":
                self.stats["LOSSES"] += 1
            case "FAILED":
                self.stats["FAILED"] += 1
        return total, level.outcome

    def train(self):
        print("!!!TRAINING!!!")
        for i, level in enumerate(self.training_set):
            total, outcome = self.play_level(level, train=True)
            self.lcs.evolve()
            print(f"Training on level {i}: {outcome} ({total})")

    def validate(self):
        print("!!!VALIDATION!!!")
        for i, level in enumerate(self.validation_set):
            total, outcome = self.play_level(level, train=False)
            print(f"VALIDATING on level {i}: {outcome} ({total})")

    def reset(self):
        self.stats = {"WINS": 0, "LOSSES": 0, "FAILED": 0}
        self.lcs.reset()

class Level:
    def __init__(self, n_pits=3, max_path_len=8, height=4, width=4):
        self.height = height
        self.width = width
        self.n_pits = n_pits
        self.player = Player()
        self.gold_pos = None
        self.wumpus_pos = None
        self.pits = []
        self.environment = []

        self.bump = False
        self.scream = False

        self.steps = 0
        self.outcome = "FAILED"

        # random generation of a level

        # generate potential winning path so every level is "solvable"
        winning_path = [self.player.pos]
        path_len = randint(min(height, width), max_path_len)
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
            if tmp_pos not in winning_path and tmp_pos != self.wumpus_pos and tmp_pos not in self.pits:
                self.pits.append(tmp_pos)

        # generate stench, breeze and glitter

        # generate grid
        for h in range(self.height):
            line = []
            for w in range(self.width):
                cell = set()
                line.append(cell)
            self.environment.append(line)

        self.environment[self.gold_pos[0]][self.gold_pos[1]].add("glitter")

        self.environment[self.wumpus_pos[0]][self.wumpus_pos[1]].add("stench")
        for d in DIRECTIONS.values():
            tmp_pos = (self.wumpus_pos[0] + d[0], self.wumpus_pos[1] + d[1])
            if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
                self.environment[tmp_pos[0]][tmp_pos[1]].add("stench")

        for p in self.pits:
            for d in DIRECTIONS.values():
                tmp_pos = (p[0] + d[0], p[1] + d[1])
                if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
                    self.environment[tmp_pos[0]][tmp_pos[1]].add("breeze")

        # add "at_start" on starting point
        self.environment[self.player.pos[0]][self.player.pos[1]].add("at_start")

    def step(self, action):
        self.steps += 1
        reward = R_STEP
        end = False
        self.bump = False
        self.scream = False
        try:
            match action:
                case "fwd":
                    if not self.move_player():
                        self.bump = True
                case "turn_l":
                    self.turn_player("left")
                case "turn_r":
                    self.turn_player("right")
                case "grab":
                    if self.player.pos == self.gold_pos and not self.player.has_gold:
                        self.player.has_gold = True
                        self.gold_pos = None
                case "shoot":
                    if self.player_shoot():
                        reward += R_SHOOT
                case "climb":
                    if self.player.pos == START_POS and self.player.has_gold:
                        reward = R_WIN
                        end = True
                        self.outcome = "SUCCESS"
                case _:
                    raise ValueError(f"INVALID ACTION {action}")
        # GAME OVER
        except Warning:
            reward = R_DEATH
            end = True
            self.outcome = "DEAD"
        if not end and self.steps >= MAX_STEPS:
            end = True
        return self.player_perception(), reward, end


    def move_player(self):
        tmp_pos = (self.player.pos[0] + self.player.p_dir[0], self.player.pos[1] + self.player.p_dir[1])
        if 0 <= tmp_pos[0] < self.height and 0 <= tmp_pos[1] < self.width:
            if tmp_pos not in self.pits and (self.wumpus_pos is None or tmp_pos != self.wumpus_pos):
                self.player.pos = tmp_pos
                return True
            else:
                raise Warning("GAME OVER")
        # bumped into a wall
        self.bump = True
        return False

    def turn_player(self, rotation):
        clockwise = list(DIRECTIONS.values())
        index = clockwise.index(self.player.p_dir)
        match rotation:
            case "right":
                new_dir = clockwise[(index+1) % 4]
            case "left":
                new_dir = clockwise[(index+3) % 4]
            case _:
                raise ValueError("INVALID ROTATION")
        self.player.p_dir = new_dir

    def player_shoot(self):
        if not self.player.has_arrow:
            return False
        self.player.has_arrow = False
        p_pos = self.player.pos
        p_dir = self.player.p_dir
        target = (p_pos[0] + p_dir[0], p_pos[1] + p_dir[1])
        while 0 <= target[0] < self.height and 0 <= target[1] < self.width:
            if target == self.wumpus_pos:
                self.wumpus_pos = None
                self.scream = True
                break
            target = (target[0] + p_dir[0], target[1] + p_dir[1])
        return True

    def player_perception(self):
        p = set(self.environment[self.player.pos[0]][self.player.pos[1]])
        if self.wumpus_pos is None:
            p.discard("stench")
        if self.gold_pos is None:
            p.discard("glitter")
        if self.bump:
            p.add("bump")
        if self.scream:
            p.add("scream")
        if self.player.pos == START_POS:
            p.add("at_start")
        return p

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
    def __init__(self, pos=START_POS, p_dir=DIRECTIONS["right"]):
        self.pos = pos
        self.p_dir = p_dir
        self.has_gold = False
        self.has_arrow = True

if __name__ == "__main__":
    ww = WumpusWorld()
    ww.train()
    tr_stats = ww.stats
    print()

    ww.reset()
    ww.validate()
    vl_stats = ww.stats
    print()

    print("---TRAINING OUTCOMES---")
    print(tr_stats)
    print()

    print("---VALIDATION OUTCOMES---")
    print(vl_stats)
    print()

    print("---BEST RULES---")
    for i, c in enumerate(ww.lcs.best_rules()):
        print(f"{i + 1}: {c}")
        print(f"strength: {c.strength}")
        print()