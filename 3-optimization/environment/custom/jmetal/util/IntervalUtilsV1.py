# ###
# NOTAS DE CARLOS
#
# ORIGEN: Alberto, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - Adaptado el import de IntervalValue
# ###

import numpy as np

from custom.jmetal.util.IntervalValueV1 import IntervalValue

class IntervalUtils:
    """
    A class used to provide utilities relationed with IntervalValue class.

    ...

    Methods
    -------
    @staticmethod
    make_interval(runtimes: np.ndarray, n_iterations: int = 500, significance_level: int = 5)
        Build a IntervalValue object using the bootstrap replication method.
    """

    @staticmethod
    def make_interval(runtimes: np.ndarray, n_iterations: int = 500, significance_level: int = 5) -> IntervalValue:
        """

        Parameters
        ----------
        runtimes : numpy.ndarray
            Numpy array with the data sample used to build the confidence interval.
        n_iterations : int, optional
            Number of bootstrap replications (Default value is 500).
        significance_level: int, optional.
            Significance level for the confidence interval (Default is 5%).

        Returns
        -------
        IntervalValue
            IntervalValue object constructed.

        """

        stats = np.empty(n_iterations)
        for i in range(n_iterations):
            bs_sample = np.random.choice(runtimes,size=len(runtimes))
            stats[i] = np.mean(bs_sample)

        conf_inv = np.percentile(stats,[float(significance_level)/2,100 - float(significance_level)/2])

        return IntervalValue(conf_inv[0],conf_inv[1])
