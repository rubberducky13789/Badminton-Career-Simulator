"""Badminton Career Simulator - a standard-library terminal game."""

import random


# Tournament costs, difficulty bonuses, and base rewards.
TOURNAMENTS = {
    "1": {"name": "Local Tournament", "cost": 100, "difficulty": 34, "prize": 1000, "points": 35},
    "2": {"name": "National Tournament", "cost": 350, "difficulty": 48, "prize": 3500, "points": 80},
    "3": {"name": "International Tournament", "cost": 900, "difficulty": 62, "prize": 10000, "points": 160},
    "4": {"name": "Major Championship", "cost": 1800, "difficulty": 76, "prize": 30000, "points": 300},
}

RESULT_REWARDS = {
    "Champion": (1.00, 1.00),
    "Runner-Up": (0.55, 0.72),
    "Semi-Finalist": (0.30, 0.48),
    "Quarter-Finalist": (0.15, 0.28),
    "Early Exit": (0.00, 0.08),
}


def clamp(value, minimum=0, maximum=100):
    """Keep a stat inside its allowed range."""
    return max(minimum, min(maximum, value))


def ask_choice(prompt, valid_choices):
    """Read and validate a menu choice."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print("Please enter one of: " + ", ".join(sorted(valid_choices)))


def create_player(name):
    """Create a player with the requested starting statistics."""
    return {
        "name": name,
        "age": 16,
        "skill": 40,
        "fitness": 40,
        "stamina": 70,
        "confidence": 50,
        "money": 1000,
        "ranking": 1000,
        "injury": "Healthy",
        "injury_weeks": 0,
        "titles": 0,
        "week": 1,
        "tournaments": 0,
        "wins": 0,
        "runner_ups": 0,
        "career_earnings": 0,
        "ranking_points": 0,
        "best_ranking": 1000,
        "season_ending_won": False,
        "equipment_bonus": 0,
    }


def display_stats(player):
    """Show the full player card at the beginning of a week."""
    season = ((player["week"] - 1) // 52) + 1
    season_week = ((player["week"] - 1) % 52) + 1
    print("\n" + "=" * 62)
    print(f"SEASON {season} - WEEK {season_week} | {player['name']}'s Career")
    print("=" * 62)
    print(f"Age: {player['age']:<3}  Skill: {player['skill']:<3}  Fitness: {player['fitness']:<3}")
    print(f"Stamina: {player['stamina']:<3}  Confidence: {player['confidence']:<3}")
    print(f"Money: ${player['money']:,}  World Ranking: #{player['ranking']}")
    print(f"Injury Status: {player['injury']}  Tournament Titles: {player['titles']}")
    if season_week == 52:
        print("*** Season-ending week: win the Major to claim the championship! ***")


def injury_risk(player, base_risk):
    """Resolve injury risk, made worse by exhaustion and overtraining."""
    risk = base_risk
    if player["stamina"] < 40:
        risk += (40 - player["stamina"]) * 0.006
    if player["stamina"] < 15:
        risk += 0.10
    if player["injury"] != "Healthy":
        risk += 0.12

    if random.random() >= risk:
        return

    severity_roll = random.random()
    if (player["injury"] == "Serious Injury" and severity_roll < 0.12) or severity_roll < 0.015:
        player["injury"] = "Career-Ending Injury"
        player["injury_weeks"] = 999
        print("DISASTER: The injury is career-ending.")
    elif severity_roll < 0.23 or player["injury"] == "Minor Injury":
        player["injury"] = "Serious Injury"
        player["injury_weeks"] = random.randint(5, 10)
        player["fitness"] = clamp(player["fitness"] - random.randint(3, 7))
        print("Bad news: you suffered a serious injury!")
    else:
        player["injury"] = "Minor Injury"
        player["injury_weeks"] = random.randint(2, 4)
        print("You picked up a minor injury.")


def technical_training(player):
    """Improve technique at the cost of stamina and injury exposure."""
    if player["injury"] == "Serious Injury":
        print("You cannot train technically with a serious injury. You rest instead.")
        rest_and_recovery(player)
        return
    gain = random.randint(2, 6)
    stamina_cost = random.randint(10, 18)
    player["skill"] = clamp(player["skill"] + gain)
    player["stamina"] = clamp(player["stamina"] - stamina_cost)
    print(f"Sharp session! Skill +{gain}; Stamina -{stamina_cost}.")
    injury_risk(player, 0.04)


def fitness_training(player):
    """Improve fitness at the cost of stamina and injury exposure."""
    if player["injury"] == "Serious Injury":
        print("You cannot do fitness training with a serious injury. You rest instead.")
        rest_and_recovery(player)
        return
    gain = random.randint(2, 6)
    stamina_cost = random.randint(11, 19)
    player["fitness"] = clamp(player["fitness"] + gain)
    player["stamina"] = clamp(player["stamina"] - stamina_cost)
    print(f"Hard conditioning pays off! Fitness +{gain}; Stamina -{stamina_cost}.")
    injury_risk(player, 0.05)


def rest_and_recovery(player):
    """Restore stamina and advance injury recovery."""
    stamina_gain = random.randint(20, 34)
    confidence_gain = random.randint(1, 4)
    player["stamina"] = clamp(player["stamina"] + stamina_gain)
    player["confidence"] = clamp(player["confidence"] + confidence_gain)
    print(f"A restorative week: Stamina +{stamina_gain}; Confidence +{confidence_gain}.")

    if player["injury"] != "Healthy":
        recovery = 2 if random.random() < 0.35 else 1
        player["injury_weeks"] -= recovery
        if player["injury_weeks"] <= 0:
            player["injury"] = "Healthy"
            player["injury_weeks"] = 0
            print("Excellent news: you have fully recovered!")
        else:
            print(f"Your injury is healing (about {player['injury_weeks']} week(s) remaining).")


def choose_tournament(player):
    """Display tournament choices and return a selected tournament."""
    season_week = ((player["week"] - 1) % 52) + 1
    print("\nChoose a tournament:")
    for key, data in TOURNAMENTS.items():
        name = data["name"]
        if key == "4" and season_week == 52:
            name = "Season-Ending Championship (Major)"
        print(f"  {key}. {name} - Entry fee ${data['cost']:,}")
    print("  5. Cancel")
    choice = ask_choice("Tournament choice: ", {"1", "2", "3", "4", "5"})
    if choice == "5":
        return None, False
    tournament = dict(TOURNAMENTS[choice])
    is_season_ending = choice == "4" and season_week == 52
    if is_season_ending:
        tournament["name"] = "Season-Ending Championship"
    return tournament, is_season_ending


def calculate_result(player, tournament):
    """Compare player form against tournament difficulty with match-day variance."""
    form = (
        player["skill"] * 0.38
        + player["fitness"] * 0.25
        + player["stamina"] * 0.20
        + player["confidence"] * 0.17
        + player["equipment_bonus"]
    )
    if player["injury"] == "Minor Injury":
        form -= 8
    elif player["injury"] == "Serious Injury":
        form -= 22

    score = form - tournament["difficulty"] + random.gauss(0, 11)
    if score >= 25:
        return "Champion"
    if score >= 15:
        return "Runner-Up"
    if score >= 6:
        return "Semi-Finalist"
    if score >= -4:
        return "Quarter-Finalist"
    return "Early Exit"


def update_ranking(player, points):
    """Turn accumulated ranking points into a world ranking, down to #1."""
    player["ranking_points"] += points
    # Early progress is quick; the final climb requires sustained elite results.
    new_ranking = max(1, 1000 - int(player["ranking_points"] * 1.65))
    if new_ranking < player["ranking"]:
        print(f"Your ranking improves from #{player['ranking']} to #{new_ranking}!")
    player["ranking"] = min(player["ranking"], new_ranking)
    player["best_ranking"] = min(player["best_ranking"], player["ranking"])


def enter_tournament(player):
    """Run tournament selection, result calculation, and rewards."""
    if player["injury"] == "Serious Injury":
        print("The doctor will not clear you to compete. Choose recovery this week.")
        rest_and_recovery(player)
        return

    tournament, is_season_ending = choose_tournament(player)
    if tournament is None:
        print("Tournament entry cancelled; you spend the week recovering.")
        rest_and_recovery(player)
        return
    if player["money"] < tournament["cost"]:
        print("You cannot afford that entry fee. You spend the week resting.")
        rest_and_recovery(player)
        return

    player["money"] -= tournament["cost"]
    player["tournaments"] += 1
    print(f"\nYou enter the {tournament['name']}...")
    result = calculate_result(player, tournament)
    prize_multiplier, points_multiplier = RESULT_REWARDS[result]
    prize = int(tournament["prize"] * prize_multiplier)
    points = max(1, int(tournament["points"] * points_multiplier))
    player["money"] += prize
    player["career_earnings"] += prize
    player["stamina"] = clamp(player["stamina"] - random.randint(14, 25))

    print(f"Result: {result}!")
    print(f"Prize money: ${prize:,} | Ranking points: +{points}")
    update_ranking(player, points)

    confidence_changes = {
        "Champion": 12, "Runner-Up": 7, "Semi-Finalist": 3,
        "Quarter-Finalist": 0, "Early Exit": -6,
    }
    player["confidence"] = clamp(player["confidence"] + confidence_changes[result])
    if result == "Champion":
        player["titles"] += 1
        player["wins"] += 1
        if is_season_ending:
            player["season_ending_won"] = True
            print("You are the Season-Ending Champion!")
    elif result == "Runner-Up":
        player["runner_ups"] += 1

    injury_risk(player, 0.035)


def random_event(player):
    """Occasionally apply one of several career events."""
    if random.random() > 0.20:
        return

    event = random.choice([
        "sponsor", "coach", "rival", "illness", "injury", "burnout", "equipment"
    ])
    print("\n--- RANDOM EVENT ---")

    if event == "sponsor":
        payment = random.randint(500, 3500) + player["titles"] * 250
        player["money"] += payment
        player["career_earnings"] += payment
        print(f"A sponsor backs your career. You receive ${payment:,}!")
    elif event == "coach":
        gain = random.randint(2, 5)
        player["skill"] = clamp(player["skill"] + gain)
        print(f"A respected coach offers advice. Skill +{gain}.")
    elif event == "rival":
        if random.random() < 0.55:
            gain = random.randint(3, 7)
            player["confidence"] = clamp(player["confidence"] + gain)
            print(f"You beat a rising rival in a practice match. Confidence +{gain}.")
        else:
            loss = random.randint(3, 7)
            player["confidence"] = clamp(player["confidence"] - loss)
            print(f"A rival gets under your skin. Confidence -{loss}.")
    elif event == "illness":
        loss = random.randint(10, 22)
        player["stamina"] = clamp(player["stamina"] - loss)
        print(f"A sudden illness drains your energy. Stamina -{loss}.")
    elif event == "injury":
        print("A slip during practice puts your body at risk...")
        injury_risk(player, 0.75)
    elif event == "burnout":
        loss = random.randint(8, 15)
        player["confidence"] = clamp(player["confidence"] - loss)
        player["stamina"] = clamp(player["stamina"] - 8)
        print(f"The relentless schedule causes burnout. Confidence -{loss}; Stamina -8.")
    elif event == "equipment":
        cost = random.randint(300, 900)
        if player["money"] >= cost:
            player["money"] -= cost
            player["equipment_bonus"] = min(8, player["equipment_bonus"] + 2)
            print(f"You invest ${cost:,} in upgraded equipment. Match performance improves!")
        else:
            print("New equipment becomes available, but it is beyond your current budget.")


def check_game_end(player):
    """Return (ended, won, reason), checking immediate terminal conditions."""
    if player["ranking"] == 1 and player["season_ending_won"]:
        return True, True, "You reached World #1 and won the Season-Ending Championship!"
    if player["money"] < 0:
        return True, False, "Your career has ended in financial ruin."
    if player["injury"] == "Career-Ending Injury":
        return True, False, "A career-ending injury forces you to retire."
    if player["age"] >= 35:
        if player["ranking"] != 1:
            return True, False, "You reached age 35 without becoming World #1."
        return True, False, "You retire at 35 without completing the championship double."
    return False, False, ""


def career_summary(player, won, reason):
    """Print a detailed summary after victory or defeat."""
    seasons = ((player["week"] - 1) // 52) + 1
    print("\n" + "#" * 62)
    print("CAREER COMPLETE")
    print("#" * 62)
    print(reason)
    if won:
        print(f"\nVICTORY! {player['name']} has conquered the badminton world!")
    else:
        print(f"\n{player['name']} leaves the court with a career full of memories.")
    print("\nCareer Summary")
    print(f"  Final age: {player['age']}")
    print(f"  Seasons played: {seasons}")
    print(f"  Weeks played: {player['week']}")
    print(f"  Best world ranking: #{player['best_ranking']}")
    print(f"  Tournament titles: {player['titles']}")
    print(f"  Tournaments entered: {player['tournaments']}")
    print(f"  Runner-up finishes: {player['runner_ups']}")
    print(f"  Career earnings: ${player['career_earnings']:,}")
    print(f"  Final money: ${player['money']:,}")
    print(f"  Final Skill/Fitness: {player['skill']}/{player['fitness']}")
    print(f"  Season-Ending Championship won: {'Yes' if player['season_ending_won'] else 'No'}")
    print("#" * 62)


def advance_week(player):
    """Move time forward and age the player after every 52 weeks."""
    # Travel, food, court time, and basic career expenses make finances matter.
    weekly_expenses = 45 + max(0, player["ranking"] < 200) * 20
    player["money"] -= weekly_expenses
    print(f"Weekly career expenses: -${weekly_expenses}.")

    if player["injury"] != "Healthy" and player["injury"] != "Career-Ending Injury":
        # Injuries heal slowly even without choosing full rest.
        player["injury_weeks"] -= 1
        if player["injury_weeks"] <= 0:
            player["injury"] = "Healthy"
            player["injury_weeks"] = 0
            print("Your injury has healed by the end of the week.")

    if player["week"] % 52 == 0:
        player["age"] += 1
        print(f"\nA season ends. Happy birthday—you are now {player['age']}!")
        # Rankings decay a little between seasons unless already #1.
        if player["ranking"] > 1:
            old_rank = player["ranking"]
            player["ranking"] = min(1000, player["ranking"] + random.randint(8, 25))
            if player["ranking"] != old_rank:
                print(f"Off-season ranking adjustment: #{old_rank} to #{player['ranking']}.")
    player["week"] += 1


def game_loop(player):
    """Run weekly choices until an immediate win or loss occurs."""
    while True:
        display_stats(player)
        print("\nChoose this week's focus:")
        print("  1. Technical Training")
        print("  2. Fitness Training")
        print("  3. Rest & Recovery")
        print("  4. Enter Tournament")
        choice = ask_choice("Your choice: ", {"1", "2", "3", "4"})

        if choice == "1":
            technical_training(player)
        elif choice == "2":
            fitness_training(player)
        elif choice == "3":
            rest_and_recovery(player)
        else:
            enter_tournament(player)

        # End checks happen after every meaningful phase, so play stops immediately.
        ended, won, reason = check_game_end(player)
        if ended:
            career_summary(player, won, reason)
            return

        random_event(player)
        ended, won, reason = check_game_end(player)
        if ended:
            career_summary(player, won, reason)
            return

        advance_week(player)
        ended, won, reason = check_game_end(player)
        if ended:
            career_summary(player, won, reason)
            return


def main():
    """Display the introduction, obtain a valid name, and start the game."""
    print("=" * 62)
    print("BADMINTON CAREER SIMULATOR")
    print("Rise from a teenage prospect to the top of the badminton world.")
    print("=" * 62)
    while True:
        name = input("Enter your badminton player's name: ").strip()
        if name:
            break
        print("Your player needs a name. Please try again.")

    print(f"\nWelcome, {name}! Reach World #1 and win the Season-Ending Championship.")
    print("Manage your stamina, health, confidence, and finances carefully.")
    game_loop(create_player(name))


if __name__ == "__main__":
    main()
