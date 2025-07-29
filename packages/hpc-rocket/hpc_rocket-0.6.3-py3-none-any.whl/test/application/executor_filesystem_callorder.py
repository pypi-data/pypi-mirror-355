from io import TextIOWrapper
import io
from test.testdoubles.executor import SlurmJobExecutorSpy
from typing import Any, List, Optional
from unittest.mock import Mock

from hpcrocket.core.executor import RunningCommand
from hpcrocket.core.filesystem import Filesystem, FilesystemFactory


class CallOrderVerification(SlurmJobExecutorSpy, Filesystem):
    def __init__(self, expected: List[str]) -> None:
        super().__init__()
        self.log: List[str] = []
        self.expected = expected

    def __getattr__(self, name: str) -> Any:
        return Mock(name=name)

    def exec_command(self, command: str) -> RunningCommand:
        executable = command.split()[0]
        self.log.append(executable)
        return super().exec_command(command)

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def glob(self, pattern: str) -> List[str]:
        return []

    def openread(self, path: str) -> TextIOWrapper:
        return TextIOWrapper(io.BytesIO())

    def copy(
        self,
        source: str,
        target: str,
        overwrite: bool = False,
        filesystem: Optional["Filesystem"] = None,
    ) -> None:
        self.log.append(f"copy {source} {target}")

    def delete(self, path: str) -> None:
        self.log.append(f"delete {path}")

    def exists(self, path: str) -> bool:
        return False

    def __call__(self) -> None:
        assert (
            self.log == self.expected
        ), f"Expected: {self.expected}\n\n Got {self.log}"


class VerifierReturningFilesystemFactory(FilesystemFactory):
    def __init__(self, verifier: CallOrderVerification) -> None:
        self.verifier = verifier

    def create_local_filesystem(self) -> "Filesystem":
        return self.verifier

    def create_ssh_filesystem(self) -> "Filesystem":
        return self.verifier
