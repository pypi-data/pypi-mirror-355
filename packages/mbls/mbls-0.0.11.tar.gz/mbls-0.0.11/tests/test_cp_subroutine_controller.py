from routix import DynamicDataObject

from src.mbls.cpsat import CpSubroutineController

from .fake_cp_model import FakeCpModel


class DummyProblem:
    name = "test-problem"


class DummyStoppingCriteria(DynamicDataObject):
    pass


class DummyCpController(
    CpSubroutineController[DummyProblem, FakeCpModel, DummyStoppingCriteria]
):
    def is_stopping_condition(self) -> bool:
        return False

    def post_run_process(self):
        pass

    def create_base_cp_model(self) -> FakeCpModel:
        return FakeCpModel(maximize=False)


def test_add_obj_log_minimize():
    controller = DummyCpController(
        instance=DummyProblem(),
        shared_param_dict={},
        cp_model_class=FakeCpModel,
        subroutine_flow=DynamicDataObject({}),
        stopping_criteria=DummyStoppingCriteria({}),
    )

    controller.add_obj_log(
        (0.0, 100.0, 150.0),
        is_maximize=False,
        obj_value_is_valid=True,
        obj_bound_is_valid=True,
    )
    controller.add_obj_log(
        (1.0, 95.0, 140.0),
        is_maximize=False,
        obj_value_is_valid=True,
        obj_bound_is_valid=True,
    )
    controller.add_obj_log(
        (2.0, 105.0, 160.0),
        is_maximize=False,
        obj_value_is_valid=True,
        obj_bound_is_valid=True,
    )

    val_log = controller.obj_value_log
    bound_log = controller.obj_bound_log

    assert val_log == [(0.0, 100.0), (1.0, 95.0)]
    assert bound_log == [(0.0, 150.0), (2.0, 160.0)]


def test_append_obj_log_maximize():
    class MaxController(DummyCpController):
        def create_base_cp_model(self) -> FakeCpModel:
            return FakeCpModel(maximize=True)

    controller = MaxController(
        instance=DummyProblem(),
        shared_param_dict={},
        cp_model_class=FakeCpModel,
        subroutine_flow=DynamicDataObject({}),
        stopping_criteria=DummyStoppingCriteria({}),
    )

    logs = [
        (0.0, 10.0, 20.0),
        (1.0, 15.0, 18.0),
        (2.0, 13.0, 22.0),
    ]
    controller.append_obj_log(
        logs, is_maximize=True, obj_value_is_valid=True, obj_bound_is_valid=True
    )

    assert controller.obj_value_log == [(0.0, 10.0), (1.0, 15.0)]
    assert controller.obj_bound_log == [(0.0, 20.0), (1.0, 18.0)]


def test_solve_cp_model_triggers_logging():
    controller = DummyCpController(
        instance=DummyProblem(),
        shared_param_dict={},
        cp_model_class=FakeCpModel,
        subroutine_flow=DynamicDataObject({}),
        stopping_criteria=DummyStoppingCriteria({}),
    )

    output = controller.solve_current_cp_model(
        computational_time=10.0,
        num_workers=1,
        obj_value_is_valid=True,
        obj_bound_is_valid=True,
    )

    assert output.status == "OPTIMAL"
    assert output.elapsed_time == 3.0
    assert output.objective_value == 85.0
    assert output.best_objective_bound == 50.0

    assert controller.obj_value_log[-1] == (2.0, 85.0)
    assert controller.obj_bound_log[-1] == (2.0, 70.0)
