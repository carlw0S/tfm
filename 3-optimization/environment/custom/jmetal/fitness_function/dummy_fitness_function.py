import random
import time

from custom.jmetal.fitness_function import FitnessFunction

"""
.. module:: dummy_fitness_function
   :platform: Unix, Windows
   :synopsis: Dummy fitness function for testing purposes.
.. moduleauthor:: Carlos Benito-Jareño <carlos.benito@uca.es>
"""

class DummyFitnessFunction(FitnessFunction):
    """
    Dummy fitness function for testing purposes.
    This fitness function simulates the evaluation of a solution by returning a random fitness value.

    :param float delay: The delay in seconds to simulate processing time.
    :param tuple fitness_range: A tuple representing the range of fitness values to return.
    """
    def __init__(self, delay: float = 1.0, fitness_range: tuple = (0.0, 100.0)):
        super().__init__()
        self.delay = delay
        self.fitness_range = fitness_range

    def calculate(self, solution_variables: list) -> float:
        """
        Evaluate a solution by returning a random fitness value.
        
        :param list solution_variables: The variables of the solution to evaluate.
        :return fitness_value: The evaluated solution with a random fitness value.
        """
        time.sleep(self.delay)
        return random.uniform(*self.fitness_range)
    
    def name(self) -> str:
        return "Dummy Fitness Function"