# ###
# NOTAS DE CARLOS
#
# ORIGEN: Alberto, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - Cambiada la llamada a self.get_observable_data() por self.observable_data() (¿lo habrán refactorizado en jmetal?)
#   - Movido el cálculo del epoch aquí, en vez de depender del problem (creo que tiene más sentido así, como las evaluations)
#   - Cambiado el nombre y la ruta del fichero de progreso
#   - Renombrado current_individual a current_individual_index
#   - Cambiado el método get_result() por result() para sobreescribir el de la clase padre (tiene pinta de que refactorizaron en jmetal)
#   - Añadido el guardado de la epoch 0 al fichero de progreso
# ###

import os
from pathlib import Path
from typing import TypeVar, List

from jmetal.algorithm.singleobjective.genetic_algorithm import GeneticAlgorithm
from jmetal.config import store
from jmetal.core.operator import Mutation, Crossover, Selection
from jmetal.core.problem import Problem
from jmetal.operator import BinaryTournamentSelection
from jmetal.util.comparator import MultiComparator
from jmetal.util.density_estimator import CrowdingDistance
from jmetal.util.evaluator import Evaluator
from jmetal.util.generator import Generator
from jmetal.util.neighborhood import Neighborhood
from jmetal.util.ranking import FastNonDominatedRanking
from jmetal.util.termination_criterion import TerminationCriterion

S = TypeVar('S')
R = TypeVar('R')

"""
.. module:: Cellular Genetic Algorithm
   :platform: Unix, Windows
   :synopsis: Cellular Genetic Algorithm (cGA) implementation
.. moduleauthor:: Jose M. Aragon
"""


class CellularGeneticAlgorithm(GeneticAlgorithm[S, R]):

    """
    cGA implementation as described in:
    :param timestamp: Timestamp of the current execution for intermediate results output file.
    :param problem: The problem to solve.
    :param population_size: Size of the population.
    :param mutation: Mutation operator (see :py:mod:`jmetal.operator.mutation`).
    :param crossover: Crossover operator (see :py:mod:`jmetal.operator.crossover`).
    :param selection: Selection operator (see :py:mod:`jmetal.operator.selection`).
    """
    def __init__(self,
                 timestamp: str,
                 problem: Problem,
                 population_size: int,
                 neighborhood: Neighborhood,
                 mutation: Mutation,
                 crossover: Crossover,
                 selection: Selection = BinaryTournamentSelection(
                     MultiComparator([FastNonDominatedRanking.get_comparator(),
                                      CrowdingDistance.get_comparator()])),
                 termination_criterion: TerminationCriterion = store.default_termination_criteria,
                 population_generator: Generator = store.default_generator,
                 population_evaluator: Evaluator = store.default_evaluator
                ):
        super(CellularGeneticAlgorithm, self).__init__(
            problem=problem,
            population_size=population_size,
            offspring_population_size=1,
            mutation=mutation,
            crossover=crossover,
            selection=selection,
            termination_criterion=termination_criterion,
            population_evaluator=population_evaluator,
            population_generator=population_generator
        )
        self.neighborhood = neighborhood
        self.current_individual_index = 0
        self.current_neighbors = []
        self.epochs = 0
        self.progress_file = './data/progress/ga_progress-' + timestamp + '.txt'
        Path(os.path.dirname(self.progress_file)).mkdir(parents=True, exist_ok=True)

    def _save_progress(self) -> None:
        with open(self.progress_file, 'a+') as f:
            f.write('## EPOCH {} ##\n'.format(self.epochs))
            f.write('Population: \n')
            for sol in self.solutions:
                f.write('\tSolution: {}\n'.format(sol.variables))
                f.write('\tFitness: {}\n'.format(sol.objectives[0]))
            f.write('BEST SOLUTION:\n')
            f.write('\tSolution: {}\n'.format(self.result().variables))
            f.write('\tFitness: {}\n'.format(self.result().objectives[0]))

    def init_progress(self) -> None:
        super(CellularGeneticAlgorithm, self).init_progress()
        self._save_progress()
    
    def update_progress(self) -> None:
        self.evaluations += 1
        
        observable_data = self.observable_data()
        self.observable.notify_all(**observable_data)

        self.current_individual_index = (self.current_individual_index + 1) % self.population_size
        if self.current_individual_index == 0:
            self.epochs += 1
            self._save_progress()

    def selection(self, population: List[S]):
        parents = []

        self.current_neighbors = self.neighborhood.get_neighbors(self.current_individual_index, population)
        self.current_neighbors.append(self.solutions[self.current_individual_index])
        
        
        p1 = self.selection_operator.execute(self.current_neighbors)
        self.current_neighbors.remove(p1)
        p2 = self.selection_operator.execute(self.current_neighbors)
        
        parents = parents + [p1,p2]

        return parents

    def reproduction(self, mating_population: List[S]) -> List[S]:
        number_of_parents_to_combine = self.crossover_operator.get_number_of_parents()
        if len(mating_population) % number_of_parents_to_combine != 0:
            raise Exception('Wrong number of parents')

        offspring_population = self.crossover_operator.execute(mating_population)
        self.mutation_operator.execute(offspring_population[0])

        return [offspring_population[0]]

    def replacement(self, population: List[S], offspring_population: List[S]) -> List[List[S]]:
        if population[self.current_individual_index].objectives[0] > offspring_population[0].objectives[0]: # Check if new solution is better
            population[self.current_individual_index] = offspring_population[0]
            
        return population

    def result(self) -> R:
        return min(self.solutions,key=lambda s: s.objectives[0])

    def get_name(self) -> str:
        return 'cGA'
