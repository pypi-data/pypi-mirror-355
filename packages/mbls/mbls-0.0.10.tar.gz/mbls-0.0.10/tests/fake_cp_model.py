# tests/fake_cp_model.py
from typing import Optional

from routix import ElapsedTimer

from src.mbls.cpsat.custom_cp_model import CustomCpModel


class FakeCpModel(CustomCpModel):
    def __init__(self, maximize=False):
        super().__init__()
        self._maximize = maximize
        self._progress_log = [
            (0.0, 100.0, 60.0),
            (1.0, 90.0, 70.0),
            (2.0, 85.0, 50.0),
        ]

    def solve_with_prog_logger(
        self,
        computational_time: float,
        num_workers: int,
        random_seed: Optional[int] = None,
        timer: Optional[ElapsedTimer] = None,
    ):
        return "OPTIMAL", 3.0, self._progress_log[-1][1], self._progress_log[-1][2]

    def get_progress_log(self):
        return self._progress_log

    def is_maximize(self) -> bool:
        return self._maximize

    def set_num_base_constraints(self):
        pass
