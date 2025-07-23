# ###
# NOTAS DE CARLOS
#
# ORIGEN: Parte del ejemplo del GitHub de jmetalpy (2025-06-26, v1.7.0, instalado mediante pip en un venv)
# DESTINO: TFM Godot
# ###

import random
import sys
import json
import os
from datetime import datetime

from custom.jmetal.algorithm.single_objective import CellularGeneticAlgorithm
from custom.jmetal.algorithm.single_objective import SimulatedAnnealing
from jmetal.util.neighborhood import L5
from jmetal.operator.crossover import IntegerSBXCrossover
from jmetal.operator.mutation import IntegerPolynomialMutation
# from custom.jmetal.problem.single_objective import GodotProblem
from custom.jmetal.problem.single_objective import LlvmRuntimeProblem
from custom.jmetal.fitness_function import DummyFitnessFunction
from jmetal.util.termination_criterion import StoppingByEvaluations
from jmetal.util.observer import ProgressBarObserver, BasicObserver



# Save execution timestamp for output files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")



# Get required arguments: algorithm and seed
if len(sys.argv) < 4:
    print("ERROR --- Usage: python run_optimizer.py <ga|sa> <seed> <fitness_archive_file>")
    print("  Example: python run_optimizer.py ga 42 fitness_archive-20250723_144639.json")
    print("    ga: (Cellular) Genetic Algorithm")
    print("    sa: Simulated Annealing")
    print("    seed: Integer seed for reproducibility")
    print("    fitness_archive_file: Path to a JSON file with fitness values of already evaluated solutions. Use an empty string to skip this feature.")
    sys.exit(1)

algorithm_choice = sys.argv[1].lower()
try:
    seed = int(sys.argv[2])
except ValueError:
    print("ERROR --- Seed must be an integer.")
    sys.exit(1)
fitness_archive_file = sys.argv[3]

# For reproducibility
random.seed(seed)

print(f"Running '{algorithm_choice}' with seed {seed}...")



# !!! PONER ESTO EN UNA VARIABLE CONFIG?

# Problem parameters
n_passes_in_solution = 30   # Una décima parte de lo que solemos usar, por cuestión de tiempo
godot_source_path = "/home/fedora/Carlos/tfm/3-optimization/environment/godot_source"
opt_timeout = 5 * 60        # Con 30 passes, nunca me ha tardado más de 3 min realmente
clang_timeout = 15 * 60     # Nunca me ha tardado más de 15 min
benchmark = 'animation/animation_tree/animation_tree_quads'    # Bastante estable entre ejecuciones y máquinas
benchmark_statistic = 'render_cpu'  # Va en conjunción del benchmark en sí
benchmark_timeout = 1 * 60  # Timeout de una ejecución, no de las 5
max_evaluations = 27

# Common algorithm parameters
mutation_probability = 0.1  # Mutamos, en promedio, 1 de cada 10 passes (es decir, 3 de los 30 que tenemos)
mutation_distribution_index = 1.0
mutation = IntegerPolynomialMutation(probability=mutation_probability, distribution_index=mutation_distribution_index)
    # distribution_index=0.2 por defecto es BUG???
    # a mi el distribution_index me da igual realmente, porque no hay distancia entre los valores de las variables (el pass que sea)
    # con 1.0 se supone que obtengo una distribucion bastante uniforme (chatgpt)
    # a efectos practicos, creo que estoy aplicando la mutacion simple esa que teniamos custom
termination_criterion = StoppingByEvaluations(max_evaluations=max_evaluations)

# GA-specific parameters
population_size = 9         # !!! Decidir tamano poblacion
neighborhood_rows = 3       # !!! Decidir forma poblacion
neighborhood_columns = 3
neighborhood = L5(rows=neighborhood_rows, columns=neighborhood_columns)
crossover_probability = 1.0
crossover_distribution_index = 1.0
crossover = IntegerSBXCrossover(probability=crossover_probability, distribution_index=crossover_distribution_index)  # !!! Confirmar que escojo este cruce, y que parametros (existe un TPX porai también, creo que custom)
    # aqui he puesto tambien el 1.0...

# problem = GodotProblem(
#     n_passes_in_solution=n_passes_in_solution,
#     godot_source_path=godot_source_path,
#     opt_timeout=opt_timeout,
#     clang_timeout=clang_timeout,
#     benchmark=benchmark,
#     benchmark_statistic=benchmark_statistic,
#     benchmark_timeout=benchmark_timeout,
# )

problem = LlvmRuntimeProblem(
    n_passes_in_solution=n_passes_in_solution,
    fitness_function=DummyFitnessFunction(),
    fitness_archive_file=fitness_archive_file,
    timestamp=timestamp,
)

if algorithm_choice == 'ga':
    algorithm = CellularGeneticAlgorithm(
        timestamp=timestamp,
        problem=problem,
        population_size=population_size,
        neighborhood=neighborhood,
        crossover=crossover,
        mutation=mutation,
        termination_criterion=termination_criterion,
    )
elif algorithm_choice == 'sa':
    algorithm = SimulatedAnnealing(
        timestamp=timestamp,
        problem=problem,
        mutation=mutation,
        termination_criterion=termination_criterion,
    )
else:
    print("ERROR --- Unknown algorithm. Use 'ga' or 'sa'.")
    sys.exit(1)

progress_bar_observer = ProgressBarObserver(max=max_evaluations)
algorithm.observable.register(progress_bar_observer)
# basic_observer = BasicObserver(frequency=3)
# algorithm.observable.register(basic_observer)

algorithm.run()

# Get results
result = algorithm.result()
observable_data = algorithm.observable_data()

# Print to console
print(result)
print(observable_data)

# Prepare output folder
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

# File paths
result_filename = os.path.join(output_dir, f"result_{algorithm_choice}_{timestamp}.txt")
observable_filename = os.path.join(output_dir, f"observable_data_{algorithm_choice}_{timestamp}.json")
config_filename = os.path.join(output_dir, f"config_{algorithm_choice}_{timestamp}.json")

# Save result and observable data
with open(result_filename, "w") as result_file:
    result_file.write(str(result))

# with open(observable_filename, "w") as observable_file:
#     json.dump(observable_data, observable_file, indent=2)

# Save configuration
config_data = {
    "timestamp": timestamp,
    "seed": seed,
    "algorithm": algorithm_choice,
    "n_passes_in_solution": n_passes_in_solution,
    "godot_source_path": godot_source_path,
    "opt_timeout": opt_timeout,
    "clang_timeout": clang_timeout,
    "benchmark": benchmark,
    "benchmark_statistic": benchmark_statistic,
    "benchmark_timeout": benchmark_timeout,
    "max_evaluations": max_evaluations,
    "mutation_probability": mutation_probability,
    "mutation_distribution_index": mutation_distribution_index,
    "mutation_operator": mutation.__class__.__name__,
}

# Add GA-specific parameters only if applicable
if algorithm_choice == 'ga':
    config_data.update({
        "population_size": population_size,
        "neighborhood_rows": neighborhood_rows,
        "neighborhood_columns": neighborhood_columns,
        "crossover_probability": crossover_probability,
        "crossover_distribution_index": crossover_distribution_index,
        "crossover_operator": crossover.__class__.__name__,
        "neighborhood_operator": neighborhood.__class__.__name__,
    })

with open(config_filename, "w") as config_file:
    json.dump(config_data, config_file, indent=2)
