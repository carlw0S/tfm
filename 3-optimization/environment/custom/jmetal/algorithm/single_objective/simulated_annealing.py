import copy
import os
from pathlib import Path
import random
import threading
import time
from typing import List, TypeVar

import numpy

from jmetal.config import store
from jmetal.core.algorithm import Algorithm
from jmetal.core.operator import Mutation
from jmetal.core.problem import Problem
from jmetal.core.solution import Solution
from jmetal.util.generator import Generator
from jmetal.util.termination_criterion import TerminationCriterion

S = TypeVar("S")
R = TypeVar("R")

"""
.. module:: simulated_annealing
   :platform: Unix, Windows
   :synopsis: Custom implementation of Simulated Annealing with progress saving.

.. moduleauthor:: Antonio J. Nebro <antonio@lcc.uma.es>, Antonio Benítez-Hidalgo <antonio.b@uma.es>, Carlos Benito-Jareño <carlos.benito@uca.es>
"""


class SimulatedAnnealing(Algorithm[S, R], threading.Thread):
    """
    Receives the same parameters as the original Simulated Annealing, except for one extra parameter:

    :param timestamp: Timestamp of the current execution for intermediate results output file.
    """
    def __init__(
        self,
        timestamp: str,
        problem: Problem[S],
        mutation: Mutation,
        termination_criterion: TerminationCriterion,
        solution_generator: Generator = store.default_generator,
    ):
        super(SimulatedAnnealing, self).__init__()
        self.problem = problem
        self.mutation = mutation
        self.termination_criterion = termination_criterion
        self.solution_generator = solution_generator
        self.observable.register(termination_criterion)
        self.temperature = 1.0
        self.minimum_temperature = 0.000001
        self.alpha = 0.95
        self.counter = 0
        self.progress_file = './data/progress/progress_sa-' + timestamp + '.txt'
        Path(os.path.dirname(self.progress_file)).mkdir(parents=True, exist_ok=True)

    def _save_progress(self) -> None:
        with open(self.progress_file, 'a+') as f:
            f.write('## ITERATION {} ##\n'.format(self.evaluations))
            f.write('SOLUTION:\n')
            f.write('\tSolution: {}\n'.format(self.result().variables))
            f.write('\tFitness: {}\n'.format(self.result().objectives[0]))
            f.write('\n')

    def create_initial_solutions(self) -> List[S]:
        return [self.solution_generator.new(self.problem)]

    def evaluate(self, solutions: List[S]) -> List[S]:
        return [self.problem.evaluate(solutions[0])]

    def stopping_condition_is_met(self) -> bool:
        return self.termination_criterion.is_met

    def init_progress(self) -> None:
        self.evaluations = 0
        self._save_progress()

    def step(self) -> None:
        mutated_solution = copy.deepcopy(self.solutions[0])
        mutated_solution: Solution = self.mutation.execute(mutated_solution)
        mutated_solution = self.evaluate([mutated_solution])[0]

        acceptance_probability = self.compute_acceptance_probability(
            self.solutions[0].objectives[0], mutated_solution.objectives[0], self.temperature
        )

        if acceptance_probability > random.random():
            self.solutions[0] = mutated_solution

        self.temperature *= self.alpha

    def compute_acceptance_probability(self, current: float, new: float, temperature: float) -> float:
        if new < current:
            return 1.0
        else:
            t = temperature if temperature > self.minimum_temperature else self.minimum_temperature
            value = (new - current) / t
            return numpy.exp(-1.0 * value)

    def update_progress(self) -> None:
        self.evaluations += 1

        observable_data = self.observable_data()
        self.observable.notify_all(**observable_data)

        self._save_progress()

    def observable_data(self) -> dict:
        ctime = time.time() - self.start_computing_time
        return {
            "PROBLEM": self.problem,
            "EVALUATIONS": self.evaluations,
            "SOLUTIONS": self.result(),
            "COMPUTING_TIME": ctime,
        }

    def result(self) -> R:
        return self.solutions[0]

    def get_name(self) -> str:
        return "Simulated Annealing"
