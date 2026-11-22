"""
Rock-Paper-Scissors: a guided tour of Nash vs. exploitation.

Each matchup is run across many seeds, and results are reported as
EV per round (+1 win, 0 tie, -1 loss) with a 95% confidence interval,
so you can tell a real edge from noise.

The lesson in order:
  1. Nash can't lose.. but it can't win either.
  2. Exploitation is where the profit is.
  3. You can't exploit Nash.
  4. Every exploit can itself be exploited.
  5. Hedging: give up some edge in exchange for a smaller worst case.
"""

import math
import random
import statistics

MOVES = ("Rock", "Paper", "Scissors")
BEATS = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}      # key beats value
LOSES_TO = {"Rock": "Paper", "Paper": "Scissors", "Scissors": "Rock"}   # key loses to value


def payoff(a, b):
    if a == b:
        return 0
    return 1 if BEATS[a] == b else -1


def best_response(dist, rng):
    """Move with the highest EV against a predicted opponent distribution.
    Ties are broken at random, so a learner facing a uniform opponent is uniform itself."""
    evs = {m: dist[BEATS[m]] - dist[LOSES_TO[m]] for m in MOVES}
    top = max(evs.values())
    return rng.choice([m for m, ev in evs.items() if math.isclose(ev, top)])


# --------------------------------------------------------------------------
# Bots. Each one gets its own RNG and sees history as [(my_move, opp_move), ...]
# --------------------------------------------------------------------------

class Bot:
    name = "Bot"

    def __init__(self, rng):
        self.rng = rng

    def move(self, history):
        raise NotImplementedError


class Nash(Bot):
    """Exactly 1/3 each. Unexploitable, and it exploits nobody."""
    name = "Nash (1/3 each)"

    def move(self, history):
        return self.rng.choice(MOVES)


class Biased(Bot):
    """A leaky player: favors Rock 50/25/25. Static, never adapts."""
    name = "Rock Human"

    def move(self, history):
        return self.rng.choices(MOVES, weights=[0.5, 0.25, 0.25])[0]


class NoisyWSLS(Bot):
    """Win-stay / lose-shift, but only `discipline` of the time; otherwise random.
    Real people follow their habits sometimes, not every time."""
    name = "Habit Human (WSLS 60%)"

    def __init__(self, rng, discipline=0.6):
        super().__init__(rng)
        self.discipline = discipline

    def move(self, history):
        if not history or self.rng.random() > self.discipline:
            return self.rng.choice(MOVES)
        mine, theirs = history[-1]
        r = payoff(mine, theirs)
        if r == 1:
            return mine                                    # won -> stay
        if r == -1:
            return MOVES[(MOVES.index(mine) + 1) % 3]      # lost -> shift R->P->S
        return self.rng.choice(MOVES)                      # tie -> random


class FrequencyExploiter(Bot):
    """Tracks how often the opponent plays each move (with decay, so it can adapt)
    and best responds to that. Knows nothing about the opponent's code."""
    name = "Frequency Exploiter"

    def __init__(self, rng, decay=0.97):
        super().__init__(rng)
        self.decay = decay
        self.counts = {m: 1.0 for m in MOVES}  # uniform prior

    def move(self, history):
        if history:
            for m in MOVES:
                self.counts[m] *= self.decay
            self.counts[history[-1][1]] += 1
        total = sum(self.counts.values())
        return best_response({m: c / total for m, c in self.counts.items()}, self.rng)


class PatternExploiter(Bot):
    """Learns what the opponent plays NEXT given the last round (my move, their move).
    This picks up habits like win-stay/lose-shift without ever being told about them."""
    name = "Pattern Exploiter"

    def __init__(self, rng, decay=0.99):
        super().__init__(rng)
        self.decay = decay
        self.table = {}  # context -> {move: weight}

    def _ctx(self, history, i):
        return history[i] if i >= 0 else None

    def move(self, history):
        n = len(history)
        if n >= 2:  # learn: context at n-2 led to opponents move at n-1
            ctx = history[n - 2]
            row = self.table.setdefault(ctx, {m: 1.0 for m in MOVES})
            for m in MOVES:
                row[m] *= self.decay
            row[history[-1][1]] += 1
        if not history:
            return self.rng.choice(MOVES)
        row = self.table.get(history[-1], {m: 1.0 for m in MOVES})
        total = sum(row.values())
        return best_response({m: c / total for m, c in row.items()}, self.rng)


class Leveler(Bot):
    """Thinks one level higher: 'My opponent is counting MY moves and best responding.
    So I'll predict their counter, and counter that.' Same meta a poker reg uses
    against a population tendencies exploiter."""
    name = "Leveler (counters exploiters)"

    def __init__(self, rng, decay=0.9, confidence=0.8):
        super().__init__(rng)
        self.decay = decay            # deliberately NOT the exploiters 0.97: it doesn't know their settings
        self.confidence = confidence  # acts on its read 80% of the time
        self.my_counts = {m: 1.0 for m in MOVES}

    def move(self, history):
        if history:
            for m in MOVES:
                self.my_counts[m] *= self.decay
            self.my_counts[history[-1][0]] += 1
        total = sum(self.my_counts.values())
        my_dist = {m: c / total for m, c in self.my_counts.items()}
        if self.rng.random() > self.confidence:
            return self.rng.choice(MOVES)
        their_predicted = best_response(my_dist, self.rng)  # what a frequency exploiter would play
        return LOSES_TO[their_predicted]                    # beat it


class Hedged(Bot):
    """Plays Nash with probability `hedge`, the exploiter otherwise.
    Smaller edge, but much harder to punish. This is 'exploit with a GTO safety net'."""
    name = "Hedged Exploiter (40% Nash)"

    def __init__(self, rng, hedge=0.4):
        super().__init__(rng)
        self.hedge = hedge
        self.inner = FrequencyExploiter(rng)

    def move(self, history):
        exploit_move = self.inner.move(history)  # always update the model
        return self.rng.choice(MOVES) if self.rng.random() < self.hedge else exploit_move


# --------------------------------------------------------------------------
# Simulation + stats
# --------------------------------------------------------------------------

def play_match(cls_a, cls_b, rounds, seed):
    a = cls_a(random.Random(seed * 2 + 1))
    b = cls_b(random.Random(seed * 2 + 2))
    ha, hb = [], []
    w = l = t = 0
    for _ in range(rounds):
        ma, mb = a.move(ha), b.move(hb)
        ha.append((ma, mb))
        hb.append((mb, ma))
        r = payoff(ma, mb)
        if r == 1:
            w += 1
        elif r == -1:
            l += 1
        else:
            t += 1
    return w, l, t


def run_matchup(cls_a, cls_b, rounds, seeds):
    evs, W, L, T = [], 0, 0, 0
    for s in range(seeds):
        w, l, t = play_match(cls_a, cls_b, rounds, s)
        evs.append((w - l) / rounds)
        W, L, T = W + w, L + l, T + t
    mean = statistics.mean(evs)
    ci = 1.96 * statistics.stdev(evs) / math.sqrt(seeds)
    n = rounds * seeds
    return mean, ci, W / n, L / n, T / n


MIN_EDGE = 0.02  # anything smaller than 2 cents a round is not worth calling an edge here


def verdict(mean, ci):
    """Real edge = the CI clears zero AND the edge is big enough to matter.
    With dozens of matchups, a 95% CI alone will flag a fake edge about 1 time in 20."""
    if abs(mean) - ci <= 0 or abs(mean) < MIN_EDGE:
        return "no real edge (noise)"
    return "A has a real edge" if mean > 0 else "B has a real edge"


LESSONS = [
    ("1. Nash can't lose... but it can't win either",
     [(Nash, Biased), (Nash, NoisyWSLS)],
     "Against ANY opponent, Nash's EV is exactly 0. It's a floor, not a profit engine."),
    ("2. Exploitation is where the money is",
     [(FrequencyExploiter, Biased), (PatternExploiter, NoisyWSLS)],
     "Neither bot was told how its opponent works. They learned the leak from results alone.\n"
     "   Theoretical max vs. the 50/25/25 Rock player: always Paper = +0.25/round."),
    ("3. You can't exploit Nash",
     [(FrequencyExploiter, Nash), (PatternExploiter, Nash)],
     "There's no pattern to find. Every learner ends up at EV 0 against 1/3-1/3-1/3."),
    ("4. Every exploit is exploitable",
     [(Leveler, FrequencyExploiter), (Leveler, Biased), (Leveler, Nash)],
     "The exploiter's model is now a predictable pattern, and the leveler cashes it in.\n"
     "   But the leveler only wins against that one type: vs. the human and vs. Nash it's 0."),
]


def hedge_sweep(rounds, seeds):
    title = "5. Hedging: trading edge for safety"
    print(title)
    print("-" * len(title))
    print(f"  {'% Nash mixed in':>16} | {'EV vs Rock Human':>24} | {'EV vs Leveler':>15}")
    for h in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        cls = type("H", (Hedged,), {"__init__": lambda self, rng, h=h: Hedged.__init__(self, rng, h)})
        up, up_ci, *_ = run_matchup(cls, Biased, rounds, seeds)
        dn, dn_ci, *_ = run_matchup(cls, Leveler, rounds, seeds)
        print(f"  {h:>15.0%} | {up:+.3f} ± {up_ci:.3f}{'':>9} | {dn:+.3f} ± {dn_ci:.3f}")
    print("   Takeaway: 0% Nash = max profit vs. the leak, max punishment by the leveler.\n"
          "   100% Nash = can't be hurt, can't profit. Every row in between is a price for safety.\n"
          "   Picking a row based on who you think you're facing IS the GTO vs exploit decision.\n")


if __name__ == "__main__":
    ROUNDS, SEEDS = 2000, 30
    print(f"=== ROCK-PAPER-SCISSORS: GAME THEORY TOUR ===")
    print(f"{SEEDS} matches x {ROUNDS:,} rounds per matchup. EV = (wins - losses) / rounds, per A.\n")

    for title, pairs, takeaway in LESSONS:
        print(title)
        print("-" * len(title))
        for A, B in pairs:
            mean, ci, w, l, t = run_matchup(A, B, ROUNDS, SEEDS)
            print(f"  {A.name:<30} vs {B.name:<30}")
            print(f"     EV {mean:+.3f} ± {ci:.3f}   W/L/T {w:5.1%} / {l:5.1%} / {t:5.1%}   -> {verdict(mean, ci)}")
        print(f"   Takeaway: {takeaway}\n")

    hedge_sweep(ROUNDS, SEEDS)