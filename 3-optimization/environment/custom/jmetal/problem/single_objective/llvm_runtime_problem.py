# ###
# NOTAS DE CARLOS
#
# ORIGEN: Javi, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - El nombre del archivo (original: optimizationLLVMproblem.py)
#   - Refactorizado para quitar todo lo sobrante y hacer que se parezca al problema ZDT1 (el del ejemplo del GitHub)
#   - Diseñado como un problema base/genérico donde únicamente cambia la evaluación de una solución y el LlvmUtils
# ###

from datetime import datetime
import json
import os
from pathlib import Path
from jmetal.core.problem import IntegerProblem
from jmetal.core.solution import IntegerSolution

from custom.jmetal.fitness_function import FitnessFunction

from custom.jmetal.util import LlvmUtils

"""
.. module:: llvm_runtime_problem
   :platform: Unix, Windows
   :synopsis: Generic LLVM runtime optimization problem.
.. moduleauthor:: Carlos Benito-Jareño <carlos.benito@uca.es>
"""

class LlvmRuntimeProblem(IntegerProblem):
    """
    Generic LLVM runtime optimization problem.

    :param int n_passes_in_solution: Number of passes that represents any solution.
    :param FitnessFunction fitness_function: Fitness function to evaluate the solutions.
    :param str fitness_archive_file: Path to the file containing fitness values of already evaluated solutions. None to skip this feature.
    :param str timestamp: Timestamp of the current execution for fitness archive output file.
    """
    def __init__(self, 
                 n_passes_in_solution: int,
                 fitness_function: FitnessFunction,
                 fitness_archive_file: str,
                 timestamp: str,
                 llvm_utils = 0): # !!! TODO O QUIZÁ PONERLO MEJOR EN EL FITNESS FUNCTION? esto se podría convertir en "GenericMinimizationProblem" o algo así, y que lo interesante sea que incluya el diccionario de soluciones ya evaluadas
        super(LlvmRuntimeProblem, self).__init__()
        self.lower_bound = n_passes_in_solution * [0]
        self.upper_bound = n_passes_in_solution * [len(LlvmUtils.get_passes()) - 1]
        self.obj_directions = [self.MINIMIZE]
        self.obj_labels = ["Runtime"]

        self.fitness_function = fitness_function

        if fitness_archive_file:
            with open(fitness_archive_file, 'r') as f:
                self.fitness_archive = json.load(f)
            self.fitness_archive_file = fitness_archive_file
        else:
            self.fitness_archive = dict()
            self.fitness_archive_file = './results/fitness/fitness-' + timestamp + '.json'
            Path(os.path.dirname(self.fitness_archive_file)).mkdir(parents=True, exist_ok=True)

    def number_of_variables(self) -> int:
        return super().number_of_variables()    # (Should be) equal to n_passes_in_solution

    def create_solution(self) -> IntegerSolution:
        return super().create_solution()    # (Should) create a random solution

    def number_of_objectives(self) -> int:
        return len(self.obj_directions)

    def number_of_constraints(self) -> int:
        return 0

    def evaluate(self, solution: IntegerSolution) -> IntegerSolution:
        # Avoid re-evaluating solutions
        passes_indexes_str = str(solution.variables)
        fitness_value = self.fitness_archive.get(passes_indexes_str)
        if not fitness_value:
            fitness_value = self.fitness_function.calculate(solution.variables)
            self.fitness_archive.update({passes_indexes_str: fitness_value})
            with open(self.fitness_archive_file, 'w') as f:
                json.dump(self.fitness_archive, f, indent=2)
        solution.objectives[0] = fitness_value
        return solution

    def name(self) -> str:
        return 'LLVM Runtime Problem' + ', with ' + self.fitness_function.name()