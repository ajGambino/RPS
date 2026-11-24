# Rock-Paper-Scissors and Game Theory

Two small Python programs that use Rock-Paper-Scissors (RPS) to teach one of
the most important ideas in game theory: the **Nash equilibrium**, and the
trade-off between _playing safe_ and _playing to win_.

You don't need any math background. If you know the rules of RPS, you can
follow along.

| File            | What it shows                                          | Good for                           |
| --------------- | ------------------------------------------------------ | ---------------------------------- |
| `rps_simple.py` | Three matchups, raw win counts                         | A first look. Short, easy to read. |
| `rps.py`        | A five-lesson "tour" with learning bots and statistics | The full picture.                  |

## Running them

You need Python 3.8 or newer. No extra packages.

```
python rps_simple.py
python rps.py
```

`rps.py` plays over a million rounds, so give it around 10 seconds.

---

## Part 1: The ideas, in plain English

### A game, a strategy, a payoff

- **Game:** any situation where your result depends on what _you_ do and what
  _someone else_ does.
- **Strategy:** your plan for choosing moves.
- **Payoff:** what you get. In these programs it's **+1 for a win, 0 for a
  tie, -1 for a loss.**

### Pure vs. mixed strategies

- A **pure** strategy always does the same thing ("always Rock").
- A **mixed** strategy chooses at random using fixed odds ("Rock 50%, Paper
  25%, Scissors 25%").

In RPS, every pure strategy is terrible: once your opponent notices, they play
the move that beats it and win every round.

### Expected value (EV)

**EV** is your average payoff per round over the long run. If you win 40% of
rounds and lose 30%, your EV is `0.40 - 0.30 = +0.10`, or one tenth of a point
per round.

- EV above 0: you're winning on average.
- EV of 0: break-even.
- EV below 0: you're losing on average.

Both programs judge strategies by EV, not by any single game.

### The Nash equilibrium

A **Nash equilibrium** is a pair of strategies where **neither player can do
better by changing only their own strategy.** Each player is already making
the best reply to the other.

In RPS, the Nash equilibrium is for both players to choose **Rock, Paper and
Scissors with probability 1/3 each, completely at random.**

Why 1/3? Suppose you lean toward Rock, say 40%. A smart opponent plays Paper
more often and profits. Any lean at all can be punished. At exactly 1/3 each,
there's nothing to punish: every move your opponent might pick has an EV of 0
against you. Nobody gains by switching, so it's an equilibrium.

### The catch: Nash is a floor, not a profit engine

Playing 1/3 each means **you can never lose on average, but you can never win
on average either.** Your EV is 0 against _any_ opponent, even a terrible one
who plays Rock every time. (Check it: against all-Rock you win 1/3 with Paper,
lose 1/3 with Scissors, and tie 1/3 with Rock.)

To actually _win_, you have to move away from Nash and target your
opponent's weakness. This is called **exploitation.**

### Exploitation and its cost

- **Exploitative play:** spot a pattern in your opponent ("they throw Rock too
  often") and lean toward the counter ("throw more Paper").
- **The cost:** the moment you lean, _you_ have a pattern. An opponent who
  spots it can exploit you back.

That is the central tension in game theory, and in competitive games like
poker:

> **Nash (also called "GTO", for game-theory optimal) is safe but doesn't
> profit. Exploitation profits but can be punished.**

---

## Part 2: `rps_simple.py`, the short version

This file has four bots. Each bot is a function that receives the history of
past rounds and returns a move.

| Bot                       | Strategy                                                                                                                                                                      |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nash_strategy`           | 1/3 each, at random. The equilibrium.                                                                                                                                         |
| `biased_rock_bot`         | Rock 60%, Paper 20%, Scissors 20%. A player with a leak.                                                                                                                      |
| `win_stay_lose_shift_bot` | Mimics a common human habit: **repeat** a move that just won, and **shift** to the next move (Rock → Paper → Scissors) after a loss. Ties are random. Always opens with Rock. |
| `exploitative_bot`        | Hand-written to beat the habit above. Opens with Paper, then predicts "stay" or "shift" and plays the counter.                                                                |

It runs three matchups of 10,000 rounds each.

**1. Nash vs. Biased Bot: about 33% / 33% / 33%.**
The biased bot has an obvious leak (too much Rock) and Nash _still_ doesn't
profit, because Nash doesn't look at its opponent at all. Safe, but it leaves
money on the table.

**2. Nash vs. Human Psychology Bot: about 33% / 33% / 33%.**
Same story. Nash can't be beaten and can't take advantage.

**3. Exploitative Bot vs. Human Psychology Bot: 100% wins.**
The exploiter knows exactly how its opponent thinks. Its Paper opener beats the
psychology bot's Rock opener. After that, the psychology bot always loses, so
it always shifts in a predictable way, and the exploiter always counters it.
The psychology bot never wins or ties, so its only random rule (the tie rule)
never comes into play.

**Lesson from the simple version:** Nash guarantees you can't lose, and a
targeted exploit can crush a predictable opponent.

**Limitations (which `rps.py` fixes):**

- The exploiter "cheats": a programmer gave it the opponent's exact rules. Real
  players have to _learn_ an opponent's tendencies.
- The human bot follows its habit 100% of the time, which no real person does.
- A single run of 10,000 rounds can't tell you whether 33.6% vs. 33.1% is a
  real difference or just luck.

---

## Part 3: `rps.py`, the guided tour

### What's different

- **Bots are classes with memory**, so they can learn during a match.
- **Exploiters learn from results alone.** Nobody tells them how the opponent
  works.
- **The human bots are noisier and more realistic.**
- **Every matchup is played 30 times** (30 "seeds", each 2,000 rounds), and
  results are reported as EV with a **95% confidence interval**. More on that
  below.

### The cast

| Bot                        | Strategy                                                                                                                               |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Nash (1/3 each)**        | The equilibrium.                                                                                                                       |
| **Rock-Heavy Human**       | Rock 50%, Paper 25%, Scissors 25%. Never adapts.                                                                                       |
| **Habit Human (WSLS 60%)** | Win-stay / lose-shift, but only 60% of the time. Otherwise random.                                                                     |
| **Frequency Exploiter**    | Counts how often the opponent plays each move (recent rounds count more) and plays the best counter.                                   |
| **Pattern Exploiter**      | Learns "what does the opponent play _next_ after a round that went like _this_?" It discovers win-stay / lose-shift habits on its own. |
| **Leveler**                | Thinks one step ahead: "My opponent is counting _my_ moves to counter me. I'll predict their counter and beat it."                     |
| **Hedged Exploiter**       | Plays like the Frequency Exploiter, but mixes in a chosen percentage of pure Nash moves as a safety net.                               |

### Reading the output

A line looks like this:

```
Frequency Exploiter            vs Rock-Heavy Human
   EV +0.226 ± 0.008   W/L/T 47.8% / 25.2% / 26.9%   -> A has a real edge
```

- **EV +0.226:** the first bot (A) gains about 0.23 points per round on average.
- **± 0.008:** the 95% confidence interval. The true EV is very likely between
  +0.218 and +0.234.
- **W/L/T:** win, loss and tie rates for bot A.
- **Verdict:** "real edge" requires both (a) the whole interval to be on one
  side of zero, and (b) the edge to be at least 0.02. Otherwise it's reported as
  noise.

**Why the confidence interval matters:** random games produce lucky streaks.
Without a measure of uncertainty, you can't tell a real +0.006 edge from luck.
The interval answers the question "if I ran this again, how much could the
number move?"

### Lesson 1: Nash can't lose, but it can't win either

Nash vs. Rock-Heavy Human and Nash vs. Habit Human both come out at **EV ≈ 0
(noise).** Two leaky opponents, and Nash takes nothing from either.

### Lesson 2: Exploitation is where the profit is

- Frequency Exploiter vs. Rock-Heavy Human: **about +0.23 per round.** The best
  possible result is +0.25 (always play Paper), and the bot gets close to that
  just by counting.
- Pattern Exploiter vs. Habit Human: **about +0.49 per round.** It found the
  win-stay / lose-shift habit without being told it existed.

### Lesson 3: You can't exploit Nash

Both exploiters vs. Nash: **EV ≈ 0.** There's no pattern to learn in true 1/3
randomness, so every attempt to exploit it breaks even. This is the "neither
player can improve" property of the equilibrium, shown in action.

### Lesson 4: Every exploit is exploitable

- Leveler vs. Frequency Exploiter: **about +0.70 per round**, a crushing win.
  The exploiter's habit of "counter whatever my opponent plays most" is itself
  a predictable pattern, and the Leveler cashes in on it.
- Leveler vs. Rock-Heavy Human and vs. Nash: **EV ≈ 0.** The Leveler is a
  specialist. It only beats opponents who are trying to model it.

The hunter becomes the hunted. Any strategy other than Nash has _some_
counter-strategy that beats it.

### Lesson 5: Hedging, trading edge for safety

The Hedged Exploiter is run at different Nash mixes against two opponents: one
it can profit from (Rock-Heavy Human) and one that punishes it (Leveler).

| % Nash mixed in | EV vs. Rock-Heavy Human | EV vs. Leveler |
| --------------: | ----------------------: | -------------: |
|              0% |                   +0.23 |          −0.69 |
|             20% |                   +0.18 |          −0.55 |
|             40% |                   +0.13 |          −0.41 |
|             60% |                   +0.09 |          −0.28 |
|             80% |                   +0.04 |          −0.14 |
|            100% |                    0.00 |           0.00 |

_(Your exact numbers will differ slightly.)_

Read the table from top to bottom:

- **0% Nash:** maximum profit against the weak player, and maximum damage
  against the Leveler.
- **100% Nash:** can't be hurt, can't profit.
- **Rows in between:** each step toward Nash gives up some profit in exchange
  for a smaller worst case.

**Picking a row is the real-world decision.** If you're confident your
opponent is a leaky beginner, exploit hard. If you don't know who you're
facing, or they might adapt, hedge toward Nash.

---

## Part 4: The big picture

1. **Nash equilibrium** = a strategy pair where nobody gains by changing
   alone. In RPS, that's 1/3 each.
2. **Nash is unexploitable** but earns nothing against bad players.
3. **Exploitation earns** by targeting a weakness, but creates a weakness of
   your own.
4. **Every exploit has a counter.** Only Nash has no counter.
5. **Good players blend the two**, leaning on Nash as a safety net and
   exploiting as far as their confidence in a read allows.

These ideas apply far beyond RPS: poker, sports play-calling (run vs. pass),
penalty kicks (left vs. right), pricing, auctions, and cybersecurity.

## Ideas to try

- In `rps_simple.py`, make `win_stay_lose_shift_bot` open with
  `random.choice(MOVES)` instead of `"Rock"`. Why does the exploiter stop
  winning 100%?
- In `rps.py`, change the Habit Human's `discipline` from 0.6 to 0.3 or 0.9.
  How does the Pattern Exploiter's edge change?
- Change the Rock-Heavy Human to 34/33/33. Can the Frequency Exploiter still
  find an edge? Does the verdict still call it "real"?
- Add a Pattern Exploiter vs. Leveler matchup. Who wins, and why?
