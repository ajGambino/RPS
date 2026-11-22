import random

MOVES = ["Rock", "Paper", "Scissors"]
BEATS = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
LOSES_TO = {"Rock": "Paper", "Paper": "Scissors", "Scissors": "Rock"}


def nash_strategy(history):
    """Plays Rock, Paper, Scissors with an exact 1/3 probability each."""
    return random.choice(MOVES)


def biased_rock_bot(history):
    """Simulates a player who favors Rock (60% Rock, 20% Paper, 20% Scissors)."""
    return random.choices(MOVES, weights=[0.6, 0.2, 0.2])[0]


def win_stay_lose_shift_bot(history):
    """Simulates common human psychology: repeats winning moves, cycles after a loss."""
    if not history:
        return "Rock"  # Common opening tendency ESPECIALLY in men.

    my_last_move, opp_last_move = history[-1]

    if BEATS[my_last_move] == opp_last_move:
        # Won last round -> Stay
        return my_last_move
    elif BEATS[opp_last_move] == my_last_move:
        # Lost last round -> Shift to next in cycle (Rock -> Paper -> Scissors)
        next_index = (MOVES.index(my_last_move) + 1) % 3
        return MOVES[next_index]
    else:
        # Tie -> Pick randomly
        return random.choice(MOVES)

def exploitative_bot(history):
    """Counters the Win-Stay, Lose-Shift psychology."""
    if not history:
        return "Paper"  # Beats the common 'Rock' opener

    my_last_move, opp_last_move = history[-1]

    if BEATS[opp_last_move] == my_last_move:
        # Opponent won last round and will likely 'Stay' -> Play what beats their move
        return LOSES_TO[opp_last_move]
    elif BEATS[my_last_move] == opp_last_move:
        # Opponent lost last round and will likely 'Shift' -> Predict shift and counter it
        predicted_opp_move = MOVES[(MOVES.index(opp_last_move) + 1) % 3]
        return LOSES_TO[predicted_opp_move]
    else:
        return random.choice(MOVES)


def simulate_match(bot_a, bot_b, rounds=10000):
    history_a = []
    history_b = []
    scores = {"A": 0, "B": 0, "Tie": 0}

    for _ in range(rounds):
        move_a = bot_a(history_a)
        move_b = bot_b(history_b)

        history_a.append((move_a, move_b))
        history_b.append((move_b, move_a))

        if move_a == move_b:
            scores["Tie"] += 1
        elif BEATS[move_a] == move_b:
            scores["A"] += 1
        else:
            scores["B"] += 1

    return scores

if __name__ == "__main__":
    ROUNDS = 10000
    matchups = [
        ("Nash Equilibrium", nash_strategy, "Biased Bot (60% Rock)", biased_rock_bot),
        ("Nash Equilibrium", nash_strategy, "Human Psychology Bot", win_stay_lose_shift_bot),
        ("Exploitative Bot", exploitative_bot, "Human Psychology Bot", win_stay_lose_shift_bot),
    ]

    print(f"--- RO SHAM BO SIMULATION ({ROUNDS:,} ROUNDS PER MATCHUP) ---\n")
    for name_a, func_a, name_b, func_b in matchups:
        res = simulate_match(func_a, func_b, ROUNDS)
        win_pct_a = (res["A"] / ROUNDS) * 100
        win_pct_b = (res["B"] / ROUNDS) * 100
        tie_pct = (res["Tie"] / ROUNDS) * 100

        print(f"{name_a} vs. {name_b}:")
        print(f"  {name_a}: {res['A']:,} wins ({win_pct_a:.1f}%)")
        print(f"  {name_b}: {res['B']:,} wins ({win_pct_b:.1f}%)")
        print(f"  Ties: {res['Tie']:,} ({tie_pct:.1f}%)\n")