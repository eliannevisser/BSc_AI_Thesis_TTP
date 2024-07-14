import numpy as np
import random
import os
import csv


def create_schedule(n_teams):
    """ Function to create a complete schedule given a number of teams."""
    if n_teams % 2 == 1:
        raise Exception("Number of teams must be even")

    n_rounds = (n_teams - 1) * 2
    schedule_matrix = np.zeros((n_rounds, n_teams), dtype=int)
    home_teams_per_round = {}

    for round_num in range(n_rounds):
        round_schedule, home_teams = create_new_round(n_teams)
        home_teams_per_round[round_num] = home_teams
        schedule_matrix[round_num] = round_schedule

    return schedule_matrix, home_teams_per_round


def create_new_round(n_teams):
    """ Function to create a single round given a number of teams."""
    teams = list(range(1, n_teams + 1))
    round_schedule = np.zeros(n_teams, dtype=int)

    home_teams = []
    while teams:
        team1, team2 = random.sample(teams, 2)  # Pick two teams randomly
        teams.remove(team1)
        teams.remove(team2)

        if random.choice([True, False]):
            home, away = team1, team2
        else:
            home, away = team2, team1

        round_schedule[home - 1] = -away
        round_schedule[away - 1] = home
        home_teams.append(home)

    return round_schedule, home_teams


def check_violations(schedule, home_teams_per_round, max_streak=3):
    """Function to check the violations of the constraints."""
    n_max_streak = 0
    n_no_repeat = 0
    n_round_robin = 0

    # Check no repeat constraint
    for i in range(1, len(schedule)):
        round1 = schedule[i - 1]
        round2 = schedule[i]
    
        for match1, match2 in zip(round1, round2):
            team1_round1 = abs(match1)
            team2_round1 = abs(match2)
        
            if team1_round1 == team2_round1:
                n_no_repeat += 1

    # Check max streak constraint
    for team in range(1, len(schedule[0]) + 1):
        home_streak = 0
        away_streak = 0

        for r in range(len(schedule)):
            if team in home_teams_per_round[r]:
                home_streak += 1
                away_streak = 0
            else:
                away_streak += 1
                home_streak = 0

            if home_streak > max_streak:
                n_max_streak += 1
            if away_streak > max_streak:
                n_max_streak += 1

    # Check double round robin constraint
    matches = {team: [] for team in range(1, len(schedule[0]) + 1)}
    for round_schedule, home_teams in zip(schedule, home_teams_per_round.values()):

        # Check if every team plays in a round
        teams_in_round = [abs(match) for match in round_schedule]
        if len(set(teams_in_round)) != len(schedule[0]):
            n_round_robin += 1 

        for match in round_schedule:
            team1 = abs(match)
            team2 = abs(round_schedule[team1 - 1])
            matches[team1].append((team2, team1 in home_teams))
            matches[team2].append((team1, team2 in home_teams))

    # Check if each team has played both a home match and an away match against each other team
    for team, team_matches in matches.items():
        for opponent in range(1, len(matches) + 1):
            if opponent != team:
                home_match = any(match[0] == opponent and match[1] for match in team_matches)
                away_match = any(match[0] == opponent and not match[1] for match in team_matches)
                if not home_match or not away_match:
                    n_round_robin += 1
    
    n_total = [n_max_streak, n_no_repeat, n_round_robin]
    
    return n_total

def execute_experiment(n_schedules, base_dir):
    """ Function to replicate the work of Verduin et al. where for teams = {4, 6, 8... 46, 48, 50}, 
     n_schedule times,  a schedule is created. The number of violations occurring in these
    schedules is saved to a .txt file. """
    
    league_sizes = list(range(4, 52, 2))
    dest_dir = os.path.join(base_dir, f'replication_study')
    os.makedirs(dest_dir, exist_ok=True)

    # Define the path to the violations files
    violations_file_path = os.path.join(dest_dir, 'violations_replication_study.txt')
    total_violations_file_path = os.path.join(dest_dir, 'total_violations_replication_study.txt')

    for teams in league_sizes:
        folder_path = os.path.join(dest_dir, f'schedules_{teams}')
        os.makedirs(folder_path, exist_ok=True)
        total_violations = [0,0,0]

        with open(violations_file_path, 'a') as f:
            for i in range(n_schedules):
                schedule, home_teams_per_round = create_schedule(teams)
                violations = check_violations(schedule, home_teams_per_round)
                total_violations = [sum(x) for x in zip(total_violations, violations)]
                f.write(str(violations)+ '\n')

                with open(os.path.join(folder_path, f'schedule_{i}.csv'), 'w', newline='') as schedule_file:
                    writer = csv.writer(schedule_file)
                    writer.writerows(schedule)

                with open(os.path.join(folder_path, f'home_teams_{i}.txt'), 'w') as home_file:
                    for round in home_teams_per_round.values():
                        home_file.write(','.join(map(str, round)) + '\n')
                    home_file.write('Violations: ' + ', '.join(map(str, violations)) + '\n')
            
            f.write('-'*50 +'\n')
            with open(total_violations_file_path, 'a') as f:
                f.write(f"{teams}:{total_violations}\n")

        
if __name__ == '__main__':
    n_schedules = 50
    base_dir = '/'
    execute_experiment(n_schedules, base_dir)