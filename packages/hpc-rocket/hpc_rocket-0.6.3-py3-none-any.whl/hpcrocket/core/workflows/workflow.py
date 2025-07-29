from typing import List, Optional

from hpcrocket.typesafety import get_or_raise
from hpcrocket.ui import UI

try:
    from typing import Protocol
except ImportError:  # pragma: no cover
    from typing_extensions import Protocol  # type: ignore


class Stage(Protocol):
    """
    An isolated step that is part of a larger Workflow
    """

    def allowed_to_fail(self) -> bool:
        """
        Returns whether this stage is allowed to fail
        """
        ...

    def __call__(self, ui: UI) -> bool:
        """
        Starts running the stage. Returns true if the stage completed successfully.

        Args:
            ui (UI): The ui to send output to.

        Returns:
            bool
        """
        ...

    def cancel(self, ui: UI) -> None:
        """
        Cancels the stage.

        Args:
            ui (UI): The ui to send output to.
        """
        ...


class Workflow:
    """
    Represents a series of isolated steps that are executed in order
    """

    def __init__(self, stages: List[Stage]) -> None:
        self._stages = stages
        self._active_stage: Optional[Stage] = None
        self._canceled = False

    def run(self, ui: UI) -> bool:
        """
        Runs the workflow. Returns true if all stages completed successfully.

        Args:
            ui (UI): The ui to send output to.

        Returns:
            bool
        """
        results: List[bool] = []
        for stage in self._stages:
            self._active_stage = stage

            if self._canceled:
                break

            result = stage(ui)
            results.append(result)
            if self._workflow_failed(stage, result):
                return False

        return all(results)

    def _workflow_failed(self, stage: Stage, result: bool) -> bool:
        return not (result or stage.allowed_to_fail())

    def cancel(self, ui: UI) -> None:
        """
        Cancels the workflow.

        Args:
            ui (UI): The ui to send output to.

        Raises:
            WorkflowNotStartedError: If the workflow is canceled before it was started.
        """
        active_stage = get_or_raise(self._active_stage, WorkflowNotStartedError)
        active_stage.cancel(ui)
        self._canceled = True


class WorkflowNotStartedError(Exception):
    pass
