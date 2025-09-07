import itertools
import logging
import math
import random

from src.model.database import Team, TeamSide

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("team_generator")


def generate_teams(players, champions, choices_number):
    team_size = len(players) // 2

    if len(players) % 2 != 0:
        raise ValueError("The number of players must be even")

    all_combinations = list(itertools.combinations(players, team_size))

    num_unique_matches = math.ceil(len(all_combinations) / 2)

    matchups = []

    all_players_set = set(players)

    for i in range(num_unique_matches):
        team_a = list(all_combinations[i])
        team_b = list(all_players_set.difference(team_a))

        rating_a = sum(player.points for player in team_a) / team_size
        rating_b = sum(player.points for player in team_b) / team_size

        elo_difference = abs(rating_a - rating_b)

        matchups.append(
            {
                "team_a": team_a,
                "team_b": team_b,
                "rating_a": rating_a,
                "rating_b": rating_b,
                "elo_difference": elo_difference,
            }
        )

    matchups.sort(key=lambda x: x["elo_difference"])

    pool_size = min(10, len(matchups) // 2)

    if pool_size == 0 and len(matchups) > 0:
        pool_size = len(matchups)

    good_matches_pool = matchups[:pool_size]

    chosen_match = random.choice(good_matches_pool)

    team_a_champion_names = []
    team_b_champion_names = []

    for i in range(choices_number if choices_number else team_size * 2):
        choice_a = random.randint(0, len(champions) - 1)
        team_a_champion_names.append(champions[choice_a]["id"])
        del champions[choice_a]

        choice_b = random.randint(0, len(champions) - 1)
        team_b_champion_names.append(champions[choice_b]["id"])
        del champions[choice_b]

    teams = [
        Team(champions=team_a_champion_names, players=chosen_match["team_a"], team_rating=chosen_match["rating_a"]),
        Team(champions=team_b_champion_names, players=chosen_match["team_b"], team_rating=chosen_match["rating_b"]),
    ]

    random.shuffle(teams)

    teams[0].side = TeamSide.blue
    teams[1].side = TeamSide.red

    return teams
