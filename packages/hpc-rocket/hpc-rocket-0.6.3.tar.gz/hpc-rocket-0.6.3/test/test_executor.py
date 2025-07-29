from typing import cast

from hpcrocket.core.executor import CommandExecutor, RunningCommand


class ExecutorSpy(CommandExecutor):
    def __init__(self) -> None:
        self.is_connected = False

    def exec_command(self, cmd: str) -> RunningCommand:
        pass

    def connect(self) -> None:
        self.is_connected = True

    def close(self) -> None:
        self.is_connected = False


def test__when_using_executor_in_context_manager__should_connect_and_close_executor() -> None:
    with ExecutorSpy() as executor:
        executor = cast(ExecutorSpy, executor)
        assert executor.is_connected

    assert not executor.is_connected
