from random import sample, choices, choice

N_RULES = 200

INIT_STRENGTH = 100.0
MIN_STRENGTH = 0.01
MAX_STRENGTH = 5000.0

BID = 0.02
TAX = 0.0005

MAX_INTERNAL = 5

SENSOR_MSGS = ["breeze", "stench", "glitter", "bump", "scream", "at_start"]
INTERNAL_MSGS = ["has_gold", "danger_ahead", "visited_here", "wumpus_near", "m1", "m2", "m3", "m4"]
COND_MSGS = SENSOR_MSGS + INTERNAL_MSGS

EFFECTOR_MSGS = ["fwd", "turn_l", "turn_r", "grab", "shoot", "climb"]
OUT_MSGS = INTERNAL_MSGS + EFFECTOR_MSGS

ALL_MSGS = COND_MSGS + EFFECTOR_MSGS

# "common sense" rules
STARTING_RULES = [(["glitter"], [], "grab"),
                  (["has_gold"], [], "has_gold"),
                  (["has_gold", "at_start"], [], "climb"),
                  (["bump"], [], "turn_l")]

class LCS:
    def __init__(self, n_rules=N_RULES, starting_rules=True):
        self.last_winner = None
        self.producers = {}
        self.internal_msgs = set()

        self.class_pop = []
        if starting_rules:
            for r in STARTING_RULES:
                self.class_pop.append(Classifier(r[0], r[1], r[2], INIT_STRENGTH))
        while len(self.class_pop) < n_rules:
            self.class_pop.append(Classifier.random())

    def reset(self):
        self.internal_msgs = set()
        self.producers = {}
        self.last_winner = None

    def act(self, percepts, train=True):
        # msgs from environment + internal ones
        msg = set(percepts) | self.internal_msgs

        # match rules
        matched = [c for c in self.class_pop if c.matches(msg)]
        # all matching rules that actuate an action in the environment
        eff = [c for c in matched if c.out in EFFECTOR_MSGS]
        # all matching rules that add an internal message
        inn = [c for c in matched if c.out not in EFFECTOR_MSGS]

        # if no action is available choose a random action
        if not eff:
            self.reset()
            return choice(EFFECTOR_MSGS)

        # select rule for action (weighted probability)
        action = choices(eff, [c.strength for c in eff])[0]

        # select top internal messages
        top_msgs = sorted(inn, key=lambda c: c.strength, reverse=True)[:MAX_INTERNAL]

        # bucket brigade
        if train:
            for c in [action] + top_msgs:
                bid = BID * c.strength
                c.strength -= bid
                # get all rules that in the previous step generated the messages that matched the current rules
                suppliers = set()
                for m in c.pos_cond:
                    for s in self.producers.get(m, []):
                        suppliers.add(s)

                # split bid between all suppliers
                for s in suppliers:
                    s.strength += bid / len(suppliers)

        # put internal msgs in queue
        self.internal_msgs = {c.out for c in top_msgs}
        self.producers = {}
        for c in top_msgs:
            self.producers.setdefault(c.out, []).append(c)

        self.last_winner = action
        return action.out

    def reinforce(self, reward, end=False):
        if self.last_winner is not None:
            self.last_winner.strength += reward
        if end:
            for c in self.class_pop:
                c.strength *= 1 - TAX
        for c in self.class_pop:
            c.strength = min(MAX_STRENGTH, max(MIN_STRENGTH, c.strength))

    def evolve(self, n_children=2):
        for _ in range(n_children):
            # select first parent randomly (weighted probability)
            a = choices(self.class_pop, [c.strength for c in self.class_pop])[0]

            # second parent selected by the same output of first parent (weighted probability)
            same_out = [c for c in self.class_pop if c.out == a.out and c is not a]
            if not same_out:
                continue
            b = choices(same_out, [c.strength for c in same_out])[0]

            pos = set(a.pos_cond) | set(b.pos_cond)
            neg = set(a.neg_cond) | set(b.neg_cond)
            # if a condition appears in both pos and neg, discard it
            both = pos & neg
            pos -= both
            neg -= both
            if not pos and not neg:
                continue

            pos = sorted(pos)
            neg = sorted(neg)

            # check if rule already exists
            exists = False
            for c in self.class_pop:
                if c.out == a.out and sorted(c.pos_cond) == pos and sorted(c.neg_cond) == neg:
                    exists = True
                    break
            if exists:
                continue

            # children replaces weakest rule
            victim = self.class_pop.index(min(self.class_pop, key=lambda c: c.strength))
            self.class_pop[victim] = Classifier(pos, neg, a.out, INIT_STRENGTH)

    def best_rules(self, n=10):
        return sorted(self.class_pop, key=lambda c: c.strength, reverse=True)[:n]


class Classifier:
    def __init__(self, pos_cond, neg_cond, out, strength):
        self.pos_cond = pos_cond
        self.neg_cond = neg_cond
        self.out = out
        self.strength = strength

    @classmethod
    def random(cls, k_pos=1, k_neg=1):
        pos_cond = set(sample(COND_MSGS, k_pos))
        neg_cond = set(sample([m for m in COND_MSGS if m not in pos_cond], k_neg))
        out = sample(OUT_MSGS, 1)[0]
        return Classifier(pos_cond, neg_cond, out, INIT_STRENGTH)

    def matches(self, msg):
        rule_match = True
        for p in self.pos_cond:
            if p not in msg:
                rule_match = False
                break
        for n in self.neg_cond:
            if n in msg:
                rule_match = False
                break
        return rule_match

    def __str__(self):
        cond = list(self.pos_cond) + ["NOT " + n for n in self.neg_cond]
        return f"{' & '.join(cond)} -> {self.out}"