# ###
# NOTAS DE CARLOS
#
# ORIGEN: Parte del ejemplo del GitHub de jmetalpy (2025-06-26, v1.7.0, instalado mediante pip en un venv)
# DESTINO: TFM Godot
# ###

import random

from custom.jmetal.algorithm.single_objective import CellularGeneticAlgorithm
from jmetal.algorithm.singleobjective import SimulatedAnnealing
from jmetal.util.neighborhood import L5
from jmetal.operator.crossover import IntegerSBXCrossover
from jmetal.operator.mutation import IntegerPolynomialMutation
from custom.jmetal.problem.single_objective import GodotProblem
from jmetal.util.termination_criterion import StoppingByEvaluations



# For reproducibility
random.seed(18)   



# !!! PONER ESTO EN UNA VARIABLE CONFIG

n_passes_in_solution = 30   # Una décima parte de lo que solemos usar, por cuestión de tiempo
godot_source_path="/home/fedora/Carlos/GA/godot_source"
opt_timeout = 5 * 60        # Con 30 passes, nunca me ha tardado más de 3 min realmente
clang_timeout = 15 * 60     # Nunca me ha tardado más de 15 min
benchmark='animation/animation_tree/animation_tree_quads'    # Bastante estable entre ejecuciones y máquinas
benchmark_statistic='render_cpu'  # Va en conjunción del benchmark en sí
benchmark_timeout = 1 * 60  # Timeout de una ejecución, no de las 5

problem = GodotProblem(
    n_passes_in_solution=n_passes_in_solution,
    godot_source_path=godot_source_path,
    opt_timeout=opt_timeout,
    clang_timeout=clang_timeout,
    benchmark=benchmark,
    benchmark_statistic=benchmark_statistic,
    benchmark_timeout=benchmark_timeout,
)



# Mutamos, en promedio, 1 de cada 10 passes (es decir, 3 de los 30 que tenemos)
mutation = IntegerPolynomialMutation(probability=0.1, distribution_index=1.0)
    # distribution_index=0.2 por defecto es BUG???
    # a mi el distribution_index me da igual realmente, porque no hay distancia entre los valores de las variables (el pass que sea)
    # con 1.0 se supone que obtengo una distribucion bastante uniforme (chatgpt)
    # a efectos practicos, creo que estoy aplicando la mutacion simple esa que teniamos custom

termination_criterion = StoppingByEvaluations(max_evaluations=50)

'''
algorithm = CellularGeneticAlgorithm(
    intermediate_results_file='ga_progress.data',
    problem=problem,
    population_size=16,    # !!! Decidir tamano poblacion
    neighborhood=L5(rows=4, columns=4),    # !!! Decidir forma poblacion
    crossover=IntegerSBXCrossover(probability=1.0),  # !!! Confirmar que escojo este cruce, y que parametros (existe un TPX porai tambien, creo que custom)
    mutation=mutation,
    termination_criterion=termination_criterion,
    # Cruce TPX es de dos puntos, y mutacion simple es la de cambiar un numerito; son los operadores que use en el TFG
)
'''

algorithm = SimulatedAnnealing(
    problem=problem,
    mutation=mutation,
    termination_criterion=termination_criterion,
)

algorithm.run()

result = algorithm.result()
print(result)

observable_data = algorithm.observable_data()
print(observable_data)