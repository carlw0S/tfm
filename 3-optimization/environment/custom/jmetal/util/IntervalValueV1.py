# ###
# NOTAS DE CARLOS
#
# ORIGEN: Alberto, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - Ninguna
# ###

class IntervalValue:
    """
    A class used to represent an range of values

    ...

    Attributes
    ----------
    lower_bound : float
        Lower bound of the range.
    upper_bound : float
        Upper bound of the range

    Methods
    -------
    center() -> float
        Return the center of the interval.
    width() -> float
        Return the width of the interval.

    """

    # Default constructor
    def __init__(self, a: float = 0, b: float = 1):
        """

        Parameters
        ----------
        a : float, optional
            Lower bound of the range.
        b : float, optional
            Upper bound of the range.

        """
        self.lower_bound = a
        self.upper_bound = b

    # Interval center
    def center(self) -> float:
        """

        Returns
        ----------
        float
            Center of the interval.

        """
        return float(self.upper_bound + self.lower_bound)/2

    # Interval width
    def width(self) -> float:
        """

        Returns
        ----------
        float
            Width of the interval.

        """
        return abs(self.upper_bound - self.lower_bound)

    # Interval equality
    def __eq__(self, o) -> bool:
        if o is None:
            return False
        else:
            return (self.lower_bound == o.lower_bound and self.upper_bound == o.upper_bound)

    # Minimization order relationship (Art 8)
    def __le__(self, o) -> bool:
        if o.center() != self.center():
            return self.center() < o.center()
        else:
            return self.width() <= o.width()

    def __lt__(self, o) -> bool:
        return (self <= o and not(self == o))

    # IntervalValue obj to str
    def __str__(self):
        return f"interval: [{self.lower_bound},{self.upper_bound}], center: {self.center()}, width : {self.width()}\n"

    # + operator overload
    def __add__(self,o) -> float:
        return self.center() + o.center()

    # - operator overload
    def __sub__(self,o) -> float:
        return self.center() - o.center()
