"""Contains function to create a chain of jobs in SLURM."""

import graphlib
import itertools
import logging
import shutil
import subprocess
from pathlib import Path

from churn.task import Task

logger = logging.getLogger(__name__)


def create_batch_graph(*tasks: tuple[Task, list[str]], run_all: bool = False) -> bool:
    """
    Create a dependency graph of jobs in SLURM.

    Each job is created with a dependency on the listed other jobs. Tasks are run
    in the task folder.

    Parameters
    ----------
    tasks : tuple[Task, list[str]]
        Paths to the tasks to be submitted and the names of the tasks they depend on.
    run_all : bool
        If True, all tasks are run regardless of their dependencies. Default is False.

    Returns
    -------
    bool
        True if any tasks were submitted.
    """
    sbatch_executable = shutil.which('sbatch')
    if sbatch_executable is None:
        msg = 'sbatch executable not found in PATH'
        raise RuntimeError(msg)

    graph = {task.task_folder.name: ls for task, ls in tasks}
    name_task_map = {task.task_folder.name: (task, ls) for task, ls in tasks}
    name_job_id_map: dict[str, str] = {}

    for task_name in graphlib.TopologicalSorter(graph).static_order():
        task, dependencies = name_task_map[task_name]
        dependency_job_ids = [
            name_job_id_map[dependency]
            for dependency in dependencies
            if dependency in name_job_id_map
        ]
        if run_all or dependency_job_ids or task.run():
            logger.info(
                'Running task %s via SLURM',
                task.task_folder.name,
            )
            try:
                result = subprocess.run(  # noqa: S603
                    [
                        sbatch_executable,
                        *(
                            [
                                f'--dependency=afterok:{previous_jobid}'
                                for previous_jobid in dependency_job_ids
                            ]
                        ),
                        '--export=ALL',
                        'batch.sh',
                    ],
                    cwd=task.output_folder / task.task_folder.name,
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                logger.exception('Error submitting job: %s', e.stderr.decode())
                raise
            name_job_id_map[task_name] = result.stdout.decode().split()[-1]
    return len(name_job_id_map) > 0


def create_batch_chain(*tasks: Task, run_all: bool = False) -> bool:
    """
    Create a chain of jobs in SLURM.

    Each job is created with a dependency on the previous job. Tasks are run
    in the task folder.

    Parameters
    ----------
    tasks : Task
        Paths to the tasks to be submitted.
    run_all : bool
        If True, all tasks are run regardless of their dependencies. Default is False.

    Returns
    -------
    bool
        True if any tasks were submitted.
    """
    return create_batch_graph(
        *(
            (task, [previous.task_folder.name] if previous is not None else [])
            for previous, task in itertools.pairwise(itertools.chain([None], tasks))
        ),  # pyright: ignore[reportArgumentType]
        run_all=run_all,
    )


def run_chain(*tasks: Task, run_all: bool = False) -> bool:
    """
    Run a chain of jobs directly.

    The jobs run sequentially in the task folder.

    Parameters
    ----------
    tasks : Task
        Paths to the tasks to be run.
    run_all : bool
        If True, all tasks are run regardless of their dependencies. Default is False.

    Returns
    -------
    bool
        True if any tasks ran.
    """
    previous_ran = run_all
    for task in tasks:
        if previous_ran or task.run():
            logger.info(
                'Running task %s locally',
                task.task_folder.name,
            )
            cwd = task.output_folder / task.task_folder.name
            batch_name = next(cwd.glob('batch.*'))
            proc = subprocess.Popen(  # noqa: S603
                [Path.cwd() / batch_name],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            buffer = b''
            for c in iter(lambda: proc.stdout.read(1), b''):  # pyright: ignore[reportOptionalMemberAccess]  # noqa: B023
                if c != b'\n':
                    buffer += c
                else:
                    logger.info('[SUBPROCESS] %s', buffer.decode())
                    buffer = b''
            logger.info('[SUBPROCESS] %s', buffer.decode())
            proc.wait()
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(
                    proc.returncode, Path.cwd() / batch_name
                )
            previous_ran = True
    return previous_ran
