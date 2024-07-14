import random
from schedule_creation import create_new_round

def swap_rounds(schedule, home_teams_per_round):
    """Function to perform the mutation of swapping two randomly chosen rounds."""
    n_rounds = schedule.shape[0]
    
    round1, round2 = random.sample(range(n_rounds), 2)
    schedule[[round1, round2]] = schedule[[round2, round1]]
    home_teams_per_round[round1], home_teams_per_round[round2] = home_teams_per_round[round2], home_teams_per_round[round1]

    return round1, round2


def revert_swap_rounds(schedule, home_teams_per_round, round1, round2):
    """Reverts the swapRound mutation."""
    schedule[[round1, round2]] = schedule[[round2, round1]]
    home_teams_per_round[round1], home_teams_per_round[round2] = home_teams_per_round[round2], home_teams_per_round[round1]


def rebuild_round(schedule, home_teams_per_round):
    """Function to rebuild a randomly chosen round."""
    n_rounds = schedule.shape[0]
    n_teams = schedule.shape[1]
    round_to_rebuild = random.randint(0, n_rounds - 1)
    
    original_round = schedule[round_to_rebuild].copy()
    original_home_teams = home_teams_per_round[round_to_rebuild][:]
    
    schedule[round_to_rebuild], new_home_teams = create_new_round(n_teams)
    home_teams_per_round[round_to_rebuild] = new_home_teams

    return round_to_rebuild, original_round, original_home_teams


def revert_rebuild_round(schedule, home_teams_per_round, round_to_rebuild, original_round, original_home_teams):
    """Reverts the rebuildRound mutation."""
    schedule[round_to_rebuild] = original_round
    home_teams_per_round[round_to_rebuild] = original_home_teams


def invert_round(schedule, home_teams_per_round):
    """Function to perform the mutation of inverting the home/away assignments in a randomly chosen round."""
    n_rounds = schedule.shape[0]
    round_to_invert = random.randint(0, n_rounds - 1)
    original_round = schedule[round_to_invert].copy()
    original_home_teams = home_teams_per_round[round_to_invert][:]

    # Remove original home teams
    for team in original_home_teams:
        home_teams_per_round[round_to_invert].remove(team)
    
    schedule[round_to_invert] *= -1

    home_teams_per_round[round_to_invert] = [team for team in original_round if team > 0]

    return round_to_invert, original_round, original_home_teams


def revert_invert_round(schedule, home_teams_per_round, round_to_invert, original_round, original_home_teams):
    """Reverts the invertRound mutation."""
    schedule[round_to_invert] = original_round
    home_teams_per_round[round_to_invert] = original_home_teams[:]


def invert_match(schedule, home_teams_per_round):
    """ Function to perform the mutation of inverting the home/away assignments in a randomly chosen match."""
    n_rounds = schedule.shape[0]
    n_teams = schedule.shape[1]

    round_to_invert = random.randint(0, n_rounds - 1)
    team_1_to_invert = random.randint(0, n_teams - 1) 
    team_2_to_invert = abs(schedule[round_to_invert,team_1_to_invert]) - 1  # Find the index of the opponent

    # Store original state
    original_team1 = schedule[round_to_invert, team_1_to_invert]
    original_team2 = schedule[round_to_invert, team_2_to_invert]
    original_home_teams = home_teams_per_round[round_to_invert][:]

    # Invert the teams
    schedule[round_to_invert, team_1_to_invert] *= -1
    schedule[round_to_invert, team_2_to_invert] *= -1

    # Update home_teams_per_round
    if team_1_to_invert + 1 in home_teams_per_round[round_to_invert]:
        home_teams_per_round[round_to_invert].remove(team_1_to_invert + 1)
    else:
        home_teams_per_round[round_to_invert].append(team_1_to_invert + 1)

    if team_2_to_invert + 1 in home_teams_per_round[round_to_invert]:
        home_teams_per_round[round_to_invert].remove(team_2_to_invert + 1)
    else:
        home_teams_per_round[round_to_invert].append(team_2_to_invert + 1)

    return round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams


def revert_invert_match(schedule, home_teams_per_round, round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams):
    """Reverts the invertMatch mutation."""
    schedule[round_to_invert, team_1_to_invert] = original_team1
    team_2_to_invert = abs(original_team1) - 1
    schedule[round_to_invert, team_2_to_invert] = original_team2
    home_teams_per_round[round_to_invert] = original_home_teams