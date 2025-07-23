from abc import abstractmethod

"""
.. module:: fitness_function
   :platform: Unix, Windows
   :synopsis: Template for Fitness Functions.
.. moduleauthor:: Carlos Benito-Jareño <carlos.benito@uca.es>
"""

class FitnessFunction():
    """
    Base class for fitness functions in the JMetal framework.
    This class is intended to be extended by specific fitness functions.
    """
    def __init__(self):
        pass

    @abstractmethod
    def calculate(self, solution_variables: list) -> object:
        """
        Calculate the fitness value of a solution.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the fitness function.
        """
        raise NotImplementedError("Subclasses should implement this method.")