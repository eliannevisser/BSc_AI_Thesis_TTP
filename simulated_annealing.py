import numpy as np
import random
import os
import csv
import time
import mutations as m
from schedule_creation import create_schedule, check_violations

def simulated_annealing(initial_schedule, initial_home_teams, max_evaluations, initial_T):
    """ 
    Implementation of the Simulated Annealing algorithm used for valid initial schedule generation.

    Parameters:
    initial_schedule: initial schedule matrix
    initial_home_teams: dictionary containing home teams corresponding to the rounds in schedule
    max_evaluations: maximum number of evaluations
    initial_T: the initial temperature 

    Returns:
    best_schedule: the schedule with the lowest number of violations after mutating
    best_home_teams: the home teams per round corresponding to the best schedule
    all_mutations: count of all mutation types applied
    all_accepted_mutations: count of all accepted mutations
    T_values: all temperature values that occurred during the evaluations
    """
    
    current_violations = check_violations(initial_schedule, initial_home_teams)
    current_schedule = initial_schedule.copy()
    current_home_teams = {k: v[:] for k, v in initial_home_teams.items()}
    
    best_schedule = current_schedule.copy()
    best_home_teams = current_home_teams.copy()

    T_values = []
    T = initial_T
    T_values.append(T)
    all_mutations = [0, 0, 0, 0]
    all_accepted_mutations = [0, 0, 0, 0]

    for _ in range(max_evaluations):
        mutation_type = random.choice(['swap_rounds', 'rebuild_round', 'invert_round', 'invert_match'])
        if mutation_type == 'swap_rounds':
            idx = 0
            all_mutations[0] += 1
            round1, round2 = m.swap_rounds(current_schedule, current_home_teams)
            revert_func = lambda: m.revert_swap_rounds(current_schedule, current_home_teams, round1, round2)
        elif mutation_type == 'rebuild_round':
            idx = 1
            all_mutations[1] += 1
            round_to_rebuild, original_round, original_home_teams = m.rebuild_round(current_schedule, current_home_teams)
            revert_func = lambda: m.revert_rebuild_round(current_schedule, current_home_teams, round_to_rebuild, original_round, original_home_teams)
        elif mutation_type == 'invert_round':
            idx = 2
            all_mutations[2] += 1
            round_to_invert, original_round, original_home_teams = m.invert_round(current_schedule, current_home_teams)
            revert_func = lambda: m.revert_invert_round(current_schedule, current_home_teams, round_to_invert, original_round, original_home_teams)
        elif mutation_type == 'invert_match':
            idx = 3
            all_mutations[3] += 1
            round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams = m.invert_match(current_schedule, current_home_teams)
            revert_func = lambda: m.revert_invert_match(current_schedule, current_home_teams, round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams)
        
        new_violations = check_violations(current_schedule, current_home_teams)
        delta = sum(new_violations) - sum(current_violations)

        if delta <= 0 or np.random.rand() < np.exp(-delta / T):
            # Accept the mutation
            current_violations = new_violations

            # Update the best schedule found so far
            best_schedule = current_schedule.copy()
            best_home_teams = {k: v[:] for k, v in current_home_teams.items()}
            all_accepted_mutations[idx] += 1 
        else:
            revert_func()
        
        T = T * 0.9999  # cooling schedule
        if T <= 0:
            break
        T_values.append(T)

    return best_schedule, best_home_teams, all_mutations, all_accepted_mutations, T_values


def run_sa_experiment(n_schedules, league_sizes, max_evaluations, T, run_nr, base_dir):
    """ 
    Function that executes an experiment using the SA algorithm.
    
    Parameters:
    n_schedules: number of schedules to generate for each league size
    league_sizes: list of league sizes that should be used during experiment
    max_evaluations: maximum number of evaluations for HC algorithm
    T: initial temperature
    run_nr: the run number of this experiment
    base_dir: base directory for saving results

    Returns:
    all_init_schedules: all initial schedules before mutations are applied
    all_init_home_teams: all initial home teams corresponding to initial schedules
    all_final_schedules: all final schedules after application of mutations
    all_final_home_teams: all final home teams corresponding to final schedules
    all_violations: tuple of initial and final violation count for all schedules
    """
    start_time = time.time()
    all_initial_schedules = []
    all_initial_home_teams = []
    all_final_schedules = []
    all_final_home_teams = []
    all_violations = []

    dest_dir = os.path.join(base_dir, f'SA_mix_T{T}_run{run_nr}')
    os.makedirs(dest_dir, exist_ok=True)
    violations_file_path = os.path.join(dest_dir, f'violations_SA_t{T}_run{run_nr}.txt')
    total_violations_file_path = os.path.join(dest_dir, f'total_violations_SA_t{T}_run{run_nr}.txt')
    mutation_count_file_path= os.path.join(dest_dir, f'mutations_SA_mix_t{T}_run{run_nr}.txt')
    accepted_mutation_count_file_path = os.path.join(dest_dir, f'accepted_mutation_count_SA_t{T}_{run_nr}.txt')

    for n_teams in league_sizes:
        folder_path = os.path.join(dest_dir, f'schedules_{n_teams}')
        os.makedirs(folder_path, exist_ok=True)
        total_violations = [0,0,0]

        with open(violations_file_path, 'a') as f, open(mutation_count_file_path, 'a') as m, open(accepted_mutation_count_file_path, 'a') as a:
            for i in range(n_schedules):
                initial_schedule, initial_home_teams = create_schedule(n_teams)
                initial_violations = check_violations(initial_schedule, initial_home_teams)

                final_schedule, final_home_teams, all_mutations, accepted_mutations, t_values = simulated_annealing(initial_schedule, initial_home_teams, max_evaluations, T)

                all_initial_schedules.append(initial_schedule)
                all_initial_home_teams.append(initial_home_teams)
                all_final_schedules.append(final_schedule)
                all_final_home_teams.append(final_home_teams)
                all_violations.append((initial_violations, check_violations(final_schedule, final_home_teams)))

                total_violations = [sum(x) for x in zip(total_violations, check_violations(final_schedule, final_home_teams))]
                f.write(str(check_violations(final_schedule, final_home_teams))+ '\n')
                m.write(str(all_mutations) + '\n')
                a.write(str(accepted_mutations) + '\n')

                schedule_file_path = os.path.join(folder_path, f'initial_schedule_SA_t{T}_run{run_nr}_{i}.csv')
                with open(schedule_file_path, 'w', newline='') as schedule_file:
                    writer = csv.writer(schedule_file)
                    writer.writerows(initial_schedule)

                schedule_file_path = os.path.join(folder_path, f'final_schedule_SA_t{T}_run{run_nr}_{i}.csv')
                with open(schedule_file_path, 'w', newline='') as schedule_file:
                    writer = csv.writer(schedule_file)
                    writer.writerows(final_schedule)

                home_file_path = os.path.join(folder_path, f'home_teams_per_round_t{T}_run{run_nr}_{i}.txt')
                with open(home_file_path, 'w') as home_file:
                    for _, teams in final_home_teams.items():
                        home_file.write(','.join(map(str, teams)) + '\n')
                    home_file.write('Violations: ' + ', '.join(map(str, check_violations(final_schedule, final_home_teams))) + '\n')
                
                t_values_file_path = os.path.join(folder_path, f'T_values_SA_t{T}_run{run_nr}_{i}.txt')
                with open(t_values_file_path, 'w') as t_value_file:
                    for t_value in t_values:
                        t_value_file.write(f"{t_value}\n")

            f.write('-'*50 +'\n')
            m.write('-'*50 +'\n')
            a.write('-'*50 +'\n')

            with open(total_violations_file_path, 'a') as f:
                f.write(f"{n_teams}:{total_violations}\n")

    end_time = time.time()
    runtime = end_time - start_time
    print(f"Simulated annealing runtime run {run_nr} (T = {T}): {runtime} seconds")
    return all_initial_schedules, all_initial_home_teams, all_final_schedules, all_final_home_teams, all_violations

if __name__ == '__main__':
    n_schedules = 1
    league_sizes = list(range(4, 51, 2))
    max_evaluations = 1000000
    T = 1000
    run_nr = 1
    base_dir = '/'
    all_initial_schedules, all_initial_home_teams, all_final_schedules, all_final_home_teams, all_violations = run_sa_experiment(n_schedules, league_sizes, max_evaluations, T, run_nr, base_dir)