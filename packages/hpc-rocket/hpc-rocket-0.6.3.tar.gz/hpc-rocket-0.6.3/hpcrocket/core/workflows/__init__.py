from pathlib import Path
from typing import List

from hpcrocket.core.filesystem import FilesystemFactory
from hpcrocket.core.launchoptions import (
    FinalizeOptions,
    ImmediateCommandOptions,
    LaunchOptions,
    WatchOptions,
)
from hpcrocket.core.slurmbatchjob import SlurmBatchJob
from hpcrocket.core.slurmcontroller import SlurmController
from hpcrocket.core.workflows.workflow import Stage, Workflow
from hpcrocket.core.workflows.stages import (
    CancelStage,
    FinalizeStage,
    JobLoggingStage,
    PrepareStage,
    LaunchStage,
    StatusStage,
    WatchStage,
)
from hpcrocket.ui import UI


def launchworkflow(
    filesystem_factory: FilesystemFactory,
    controller: SlurmController,
    options: LaunchOptions,
) -> Workflow:
    launch_stage = LaunchStage(controller, options.sbatch)
    stages: List[Stage] = [
        PrepareStage(filesystem_factory, options.copy_files),
        launch_stage,
    ]

    if options.job_id_file:
        stages.append(JobLoggingStage(launch_stage, Path(options.job_id_file)))

    if options.watch:
        stages.append(
            WatchStage(
                launch_stage, options.poll_interval, options.continue_if_job_fails
            )
        )
        stages.append(
            FinalizeStage(
                filesystem_factory, options.collect_files, options.clean_files
            )
        )

    return Workflow(stages)


def statusworkflow(
    controller: SlurmController, options: ImmediateCommandOptions
) -> Workflow:
    return Workflow([StatusStage(controller, options.jobid)])


def cancelworkflow(
    controller: SlurmController, options: ImmediateCommandOptions
) -> Workflow:
    return Workflow([CancelStage(controller, options.jobid)])


def watchworkflow(controller: SlurmController, options: WatchOptions) -> Workflow:
    class SimpleBatchJobProvider:
        def get_batch_job(self) -> SlurmBatchJob:
            return SlurmBatchJob(controller, options.jobid)

        def cancel(self, ui: UI) -> None:
            pass

    return Workflow([WatchStage(SimpleBatchJobProvider(), options.poll_interval)])


def finalizeworkflow(
    filesystem_factory: FilesystemFactory,
    options: FinalizeOptions,
) -> Workflow:
    return Workflow(
        [FinalizeStage(filesystem_factory, options.collect_files, options.clean_files)]
    )
