import numpy as np
import random
import os
import csv
import time
import mutations as m
from schedule_creation import create_schedule, check_violations

def plant_propagation(n_teams, max_evaluations, n_max_runners, population_size):
    """ 
    Implementation of the Plant Propagation Algorithm (PPA) used for valid initial schedule generation.

    Parameters:
    n_teams: number of teams participating, or league size
    max_evaluations: maximum number of evaluations
    n_max_runners: maximum number of runners that can be generated
    population_size: maximum number of individuals in a population

    Returns:
    init_population: all schedules of the initial population
    init_home_teams: all home_teams per schedule of the initial population
    best_schedule: the schedule with the lowest number of violations after mutating
    best_home_teams: the home teams per round corresponding to the best schedule
    accepted_mutations: count of all accepted mutations
    """
    accepted_mutations = [0, 0, 0, 0]
    total_runners_generated = 0
    init_population, init_home_teams_population = generate_initial_population(n_teams, population_size)
    violations_current_population = [check_violations(schedule, home_teams) for schedule, home_teams in zip(init_population, init_home_teams_population)]
    summed_violations_current_population = [sum(v) for v in violations_current_population] 
        
    min_fitness = min(summed_violations_current_population)
    max_fitness = max(summed_violations_current_population)

    best_schedule = None
    best_home_teams = None
    best_violations = min(summed_violations_current_population)

    for _ in range(max_evaluations):
        new_population = []
        new_home_teams_population = []
        new_mutations = []
        runners_generated_in_iteration = 0

        for i in range(population_size):
            Ni = normalised_fitness(summed_violations_current_population[i], min_fitness, max_fitness)
            n_runners = min(n_max_runners, max(1, int(n_max_runners * Ni * random.random())))

            for _ in range(n_runners):
                runner, home_teams_runner, revert_func, mutation_idx = generate_runner(init_population[i], init_home_teams_population[i])
                new_population.append(runner)
                new_home_teams_population.append(home_teams_runner) 
                new_mutations.append(mutation_idx)
                total_runners_generated += 1
                runners_generated_in_iteration += 1
                if total_runners_generated > max_evaluations:
                    return init_population, init_home_teams_population, best_schedule, best_home_teams, accepted_mutations           

        violations_new_population = [check_violations(schedule, home_teams) for schedule, home_teams in zip(new_population, new_home_teams_population)]
        summed_violations_new_population = [sum(v) for v in violations_new_population]         

        combined_population = list(new_population) + list(init_population)
        combined_home_teams_population = list(new_home_teams_population) + list(init_home_teams_population)
        combined_violations = summed_violations_new_population + summed_violations_current_population
        combined_mutations = new_mutations + [-1] * len(init_population)

        # Sort combined population based on violations (minimize violations)
        sorted_population = sorted(zip(combined_population, combined_home_teams_population, combined_violations, combined_mutations), key=lambda x: x[2])
        init_population, init_home_teams_population = zip(*[(x[0], x[1]) for x in sorted_population[:population_size]])

        for schedule, home_teams, violations, mutation_idx in sorted_population[:population_size]:
            if mutation_idx != -1:  # Only update if there is a valid mutation index
                accepted_mutations[mutation_idx] += 1
            if violations <= best_violations:
                best_schedule = schedule
                best_home_teams = home_teams
                best_violations = violations
            else:
                revert_func()
    
    return init_population, init_home_teams_population, best_schedule, best_home_teams, accepted_mutations


def generate_initial_population(n_teams, population_size):
    """Helper function for generating the initial population."""
    population = []
    home_teams_population = []
    for _ in range(population_size):
        schedule, home_teams = create_schedule(n_teams)
        population.append(schedule)
        home_teams_population.append(home_teams)
    return population, home_teams_population


def normalised_fitness(violations, min_fitness, max_fitness):
    """Helper function for calculating the normalised fitness."""
    return (max_fitness - violations) / (max_fitness - min_fitness) if max_fitness != min_fitness else 1


def generate_runner(schedule, home_teams):
    """Helper function for generating runners in PPA."""
    new_schedule = schedule.copy()
    new_home_teams = {k: v[:] for k, v in home_teams.items()}
    revert_func = lambda: None
    mutation_idx = None
    num_changes = 1

    # Apply mutations
    for _ in range(num_changes):
        mutation_type = random.choice(['swap_rounds', 'rebuild_round', 'invert_round', 'invert_match'])
        if mutation_type == 'swap_rounds':
            mutation_idx = 0
            round1, round2 = m.swap_rounds(new_schedule, new_home_teams)
            revert_func = lambda: m.revert_swap_rounds(new_schedule, new_home_teams, round1, round2)
        elif mutation_type == 'rebuild_round':
            mutation_idx = 1
            round_to_rebuild, original_round, original_home_teams = m.rebuild_round(new_schedule, new_home_teams)
            revert_func = lambda: m.revert_rebuild_round(new_schedule, new_home_teams, round_to_rebuild, original_round, original_home_teams)
        elif mutation_type == 'invert_round':
            mutation_idx = 2
            round_to_invert, original_round, original_home_teams = m.invert_round(new_schedule, new_home_teams)
            revert_func = lambda: m.revert_invert_round(new_schedule, new_home_teams, round_to_invert, original_round, original_home_teams)
        elif mutation_type == 'invert_match':
            mutation_idx = 3
            round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams = m.invert_match(new_schedule, new_home_teams)
            revert_func = lambda: m.revert_invert_match(new_schedule, new_home_teams, round_to_invert, team_1_to_invert, original_team1, original_team2, original_home_teams)
        
    return new_schedule, new_home_teams, revert_func, mutation_idx


def run_ppa_experiment(n_schedules, league_sizes, max_evaluations, n_max_runners, population_size, run_nr, base_dir):
    """ 
    Function that executes an experiment using the PPA.
    
    Parameters:
    n_schedules: number of schedules to generate for each league size
    league_sizes: list of league sizes that should be used during experiment
    max_evaluations: maximum number of evaluations for PPA
    n_max_runners: maximum number of runners that can be generated
    population_size: maximum number of individuals in a population
    run_nr: the run number of this experiment
    base_dir: base directory for saving results

    Returns:
    best_schedule: the schedule with the lowest number of violations after mutating
    best_home_teams: the home teams per round corresponding to the best schedule
    """
    start_time = time.time()

    all_initial_schedules = []
    all_initial_home_teams = []
    all_final_schedules = []
    all_final_home_teams = []
    all_violations = []

    dest_dir = os.path.join(base_dir, f'PPA_run{run_nr}')
    os.makedirs(dest_dir, exist_ok=True)
    violations_file_path = os.path.join(dest_dir, f'violations_PPA_run{run_nr}.txt')
    total_violations_file_path = os.path.join(dest_dir, f'total_violations_PPA_run{run_nr}.txt')
    accepted_mutation_count_file_path = os.path.join(dest_dir, f'accepted_mutation_count_PPA_run{run_nr}.txt')

    for n_teams in league_sizes:
        folder_path = os.path.join(dest_dir, f'schedules_{n_teams}')
        os.makedirs(folder_path, exist_ok=True)
        total_violations = [0,0,0]

        with open(violations_file_path, 'a') as f, open(accepted_mutation_count_file_path, 'a') as m:
            for i in range(n_schedules):
                start_time = time.time()
                init_population, init_home_teams_population, best_schedule, best_home_teams, accepted_mutations  = plant_propagation(n_teams, max_evaluations, n_max_runners, population_size)
                end_time = time.time()
                runtime = end_time - start_time

                all_initial_schedules.append(init_population)
                all_initial_home_teams.append(init_home_teams_population)
                all_final_schedules.append(best_schedule)
                all_final_home_teams.append(best_home_teams)
                all_violations.append( check_violations(best_schedule, best_home_teams))

                total_violations = [sum(x) for x in zip(total_violations, check_violations(best_schedule, best_home_teams))]
                f.write(str(check_violations(best_schedule, best_home_teams))+ '\n')
                m.write(str(accepted_mutations) + '\n')

                schedule_file_path = os.path.join(folder_path, f'initial_schedules_PPA_run{run_nr}_{i}.csv')
                with open(schedule_file_path, 'w', newline='') as schedule_file:
                    writer = csv.writer(schedule_file)
                    writer.writerows(init_population)

                schedule_file_path = os.path.join(folder_path, f'final_schedule_PPA_run{run_nr}_{i}.csv')
                with open(schedule_file_path, 'w', newline='') as schedule_file:
                    writer = csv.writer(schedule_file)
                    writer.writerows(best_schedule)

                home_file_path = os.path.join(folder_path, f'home_teams_per_round_PPA_run{run_nr}_{i}.txt')
                with open(home_file_path, 'w') as home_file:
                    for _, teams in best_home_teams.items():
                        home_file.write(','.join(map(str, teams)) + '\n')
                    home_file.write('Violations: ' + ', '.join(map(str, check_violations(best_schedule, best_home_teams))) + '\n')

            f.write('-'*50 +'\n')
            m.write('-'*50 +'\n')

            with open(total_violations_file_path, 'a') as f:
                f.write(f"{n_teams}:{total_violations}\n")

    end_time = time.time()
    runtime = end_time - start_time
    print(f"PPA {run_nr} runtime: {runtime} seconds")
    return best_schedule, best_home_teams

if __name__ == '__main__':
    n_schedules = 1
    league_sizes = list(range(4,51,2))
    max_evaluations = 1000000
    n_max_runners = 10
    population_size = 10
    run_nr = 1
    base_dir = '/'
    best_schedule, best_home_teams, runtime = run_ppa_experiment(n_schedules, league_sizes, max_evaluations, n_max_runners, population_size, run_nr, base_dir)		