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
    This fitness function simulates the evaluation of a solution by always returning the same fitness value.

    :param float delay: The delay in seconds to simulate processing time.
    :param float fitness_value: The fixed fitness value to return.
    """
    def __init__(self, delay: float = 1.0, fitness_value: float = 13.0):
        super().__init__()
        self.delay = delay
        self.fitness_value = fitness_value

    def calculate(self, solution_variables: list) -> float:
        """
        Evaluate a solution by returning the fixed fitness value.

        :param list solution_variables: The variables of the solution to evaluate.
        :return fitness_value: The evaluated solution with the fixed fitness value.
        """
        time.sleep(self.delay)
        return self.fitness_value

    def name(self) -> str:
        return "Dummy Fitness Function"