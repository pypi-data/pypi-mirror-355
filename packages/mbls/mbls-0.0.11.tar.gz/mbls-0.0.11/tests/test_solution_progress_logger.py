from ortools.sat.python import cp_model

from mbls import ElapsedTimer
from mbls.cpsat import SolutionProgressLogger


def test_solution_progress_logger_records_solutions():
    # Arrange
    model = cp_model.CpModel()
    x = model.NewIntVar(0, 2, "x")
    y = model.NewIntVar(0, 2, "y")
    model.Add(x != y)
    model.Maximize(x + y)

    timer = ElapsedTimer()
    logger = SolutionProgressLogger(
        elapsed_timer=timer, print_on_solution_callback=False
    )

    # Act
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.solve(model, logger)
    log = logger.get_log()

    # Assert
    assert isinstance(log, list)
    assert len(log) >= 1  # At least one solution is found
    for entry in log:
        elapsed, objective, best_bound = entry
        assert isinstance(elapsed, float)
        assert isinstance(objective, float)
        assert isinstance(best_bound, float)
    # Optionally: Check the timer increments as expected
    elapsed_times = [entry[0] for entry in log]
    assert elapsed_times == sorted(elapsed_times)  # should be increasing
