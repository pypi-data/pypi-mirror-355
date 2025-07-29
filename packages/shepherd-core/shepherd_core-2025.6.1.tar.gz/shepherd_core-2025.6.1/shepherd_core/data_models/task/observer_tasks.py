"""Collection of tasks for selected observer included in experiment."""

from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Annotated
from typing import Optional

from pydantic import validate_call
from typing_extensions import Self
from typing_extensions import deprecated

from shepherd_core.data_models.base.content import IdInt
from shepherd_core.data_models.base.content import NameStr
from shepherd_core.data_models.base.shepherd import ShpModel
from shepherd_core.data_models.experiment.experiment import Experiment
from shepherd_core.data_models.testbed.testbed import Testbed

from .emulation import EmulationTask
from .firmware_mod import FirmwareModTask
from .programming import ProgrammingTask


class ObserverTasks(ShpModel):
    """Collection of tasks for selected observer included in experiment."""

    observer: NameStr

    # PRE PROCESS
    time_prep: datetime  # TODO: should be optional
    root_path: Path

    # fw mod, store as hex-file and program
    fw1_mod: Optional[FirmwareModTask] = None
    fw2_mod: Optional[FirmwareModTask] = None
    fw1_prog: Optional[ProgrammingTask] = None
    fw2_prog: Optional[ProgrammingTask] = None

    # MAIN PROCESS
    emulation: Optional[EmulationTask] = None

    # deprecations, TODO: remove before public release
    owner_id: Annotated[Optional[IdInt], deprecated("not needed anymore")] = None
    abort_on_error: Annotated[bool, deprecated("has no effect")] = False

    # post_copy / cleanup, Todo: could also just intake emuTask
    #  - delete firmwares
    #  - decode uart
    #  - downsample
    #  - zip it

    @classmethod
    @validate_call
    def from_xp(cls, xp: Experiment, tb: Testbed, tgt_id: IdInt) -> Self:
        if not tb.shared_storage:
            raise ValueError("Implementation currently relies on shared storage!")

        t_start = (
            xp.time_start
            if isinstance(xp.time_start, datetime)
            else datetime.now().astimezone() + timedelta(minutes=3)
        )  # TODO: this is messed up, just a hotfix

        obs = tb.get_observer(tgt_id)
        xp_dir = "experiments/" + xp.name + "_" + t_start.strftime("%Y-%m-%d_%H-%M-%S")
        root_path = tb.data_on_observer / xp_dir
        # TODO: Paths should be "friendlier"
        #    - replace whitespace with "_" and remove non-alphanum?

        fw_paths = [root_path / f"fw{_i}_{obs.name}.hex" for _i in [1, 2]]

        return cls(
            observer=obs.name,
            time_prep=t_start - tb.prep_duration,
            root_path=root_path,
            fw1_mod=FirmwareModTask.from_xp(xp, tb, tgt_id, 1, fw_paths[0]),
            fw2_mod=FirmwareModTask.from_xp(xp, tb, tgt_id, 2, fw_paths[1]),
            fw1_prog=ProgrammingTask.from_xp(xp, tb, tgt_id, 1, fw_paths[0]),
            fw2_prog=ProgrammingTask.from_xp(xp, tb, tgt_id, 2, fw_paths[1]),
            emulation=EmulationTask.from_xp(xp, tb, tgt_id, root_path),
        )

    def get_tasks(self) -> list[ShpModel]:
        task_names = ["fw1_mod", "fw2_mod", "fw1_prog", "fw2_prog", "emulation"]
        tasks = []

        for task_name in task_names:
            if not hasattr(self, task_name):
                continue
            task = getattr(self, task_name)
            if task is None:
                continue
            tasks.append(task)
        return tasks

    def get_output_paths(self) -> dict[str, Path]:
        values: dict[str, Path] = {}
        if isinstance(self.emulation, EmulationTask):
            if self.emulation.output_path is None:
                raise ValueError("Emu-Task should have a valid output-path")
            values[self.observer] = self.emulation.output_path
        return values
