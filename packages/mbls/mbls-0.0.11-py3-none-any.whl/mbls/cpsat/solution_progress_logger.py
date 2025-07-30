import logging
from typing import Optional

from ortools.sat.python import cp_model

from .. import ElapsedTimer


class SolutionProgressLogger(cp_model.CpSolverSolutionCallback):
    """
    A lightweight logger for tracking the progress of solution discovery
    during CP-SAT solving.

    This class is designed to be used as a callback with the OR-Tools CpSolver.
    It logs a timestamped record of each feasible solution found, capturing:

    - Elapsed time since solving began
    - Objective value of the current solution
    - Best known lower (upper) bound found when min(max)imizing at that moment

    The logger does **not** analyze or interpret results.
    It only accumulates raw progress data, which can be retrieved later
    (e.g., for plotting, reporting, or summary generation).

    Example usage:
        >>> logger = SolutionProgressLogger(timer)
        >>> solver.SolveWithSolutionCallback(model, logger)
        >>> progress = logger.get_log()
    """

    _e_timer: ElapsedTimer
    _log: list[tuple[float, float, float]]
    """A list of tuples containing (elapsed time, objective value, best bound)."""

    def __init__(
        self,
        elapsed_timer: Optional[ElapsedTimer] = None,
        print_on_solution_callback: bool = False,
        log_info_on_solution_callback: bool = False,
    ) -> None:
        super().__init__()
        self._log = []
        if elapsed_timer is None:
            self._e_timer = ElapsedTimer()
            self._e_timer.set_start_time_as_now()
        else:
            self._e_timer = elapsed_timer
        self._print_on_solution_callback = print_on_solution_callback
        """If True, prints progress on each solution callback."""
        self._log_info_on_solution_callback = log_info_on_solution_callback
        """If True, logs additional information on each solution callback."""

    def on_solution_callback(self) -> None:
        """
        Callback method called on each solution found.

        - The method must be implemented in subclass of cp_model.CpSolverSolutionCallback.
        - This method logs the elapsed time, objective value, and best bound
        at the time of the solution discovery.
        - It also prints the progress if `self._print_on_solution_callback` is True.
        - It logs additional information if `self._log_info_on_solution_callback` is True.
        """
        elapsed = self._e_timer.get_elapsed_sec()
        objective = self.objective_value
        best_bound = self.best_objective_bound
        self._log.append((elapsed, objective, best_bound))
        info_str = (
            f"Elapsed: {elapsed:.2f} sec, "
            f"Objective: {objective}, "
            f"Best Bound: {best_bound}"
        )
        if self._print_on_solution_callback:
            print(info_str)
        if self._log_info_on_solution_callback:
            logging.info(info_str)

    @property
    def log(self) -> list[tuple[float, float, float]]:
        """Property to access the log list.

        Returns:
            list[tuple[float, float, float]]: a list of tuples
                containing (elapsed time, objective value, best bound)
        """
        return self._log.copy()

    def get_log(self) -> list[tuple[float, float, float]]:
        """Returns the log list.

        Returns:
            list[tuple[float, float, float]]: a list of tuples
                containing (elapsed time, objective value, best bound)
        """
        return self.log
