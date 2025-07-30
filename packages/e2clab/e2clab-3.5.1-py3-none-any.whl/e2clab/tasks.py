"""
This module serves as an interface between the CLI and the Experiment object.
Creating/Reloading the experimentfrom a pickle file thanks to the 'enostask' wrapper
"""

import logging
from functools import wraps
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from enoslib.task import EnosFilePathError, enostask

import e2clab.experiment as e2c_exp
from e2clab.constants import STATE_DIR, WorkflowTasks
from e2clab.experiment import SSH, Experiment
from e2clab.log import get_logger

logger = get_logger(__name__, ["TASK"])

EXPERIMENT = "experiment"


EXP_ERROR_MSG = (
    "Could not find experiment manager in state object 'env'."
    "'env' may be corrupted or your last command did not exit gracefully."
    " You need to re-initialize an experiment with `layers-services` or `deploy`."
)

ENV_ERROR_MSG = (
    "Could not find missing state object 'env'."
    " Have you run `e2clab layers-services` to initiate an experiment before ?"
    " Are you using the right SCENARIO_DIR ?"
)


class TaskError(click.Abort):
    """Makes click abort correctly and exit"""

    pass


def env_loader_handler():
    """Handle enostask error when missing env"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            kwargs["env"] /= STATE_DIR
            try:
                r = fn(*args, **kwargs)
                return r
            except EnosFilePathError:
                logger.error(ENV_ERROR_MSG)

        return wrapper

    return decorator


def e2ctask(new: bool = False):
    """
    Returns a decorator to manage experiment instance creation, storage and retrieval
    i.e. tasks.

    The decorated function must be called with an "env" argument pointing to the dir
    where the 'env' pickle object is/should be stored, and a "exp" argument if
    new is not True to recieve the loaded experiment instance.

    Usage:
    ```python
    # Creating an experiment
    @e2ctask(new=True)
    def new_init_task(...) -> Experiment:
        exp = Experiment(...)
        return exp


    # Retrieving the experiment
    @e2ctask()
    def new_task(exp):
        # call your Experiment method
        exp.task()
    ```

    Then you can call your tasks from the cli per exmple:
    ```python
    import e2clab.tasks as task

    task.new_init_task(env="path/to/dir")
    task.new_task(env="path/to/dir")
    ```

    Args:
        new (bool, optional): Creates a new environment.
            If True decorated function must return an `e2clab.Experiment` instance.
            Defaults to False.
    """

    def decorator(fn):
        # Disable specific enoslib task logger
        logging.getLogger("enoslib.task").setLevel(logging.ERROR)

        @env_loader_handler()
        @enostask(new=new, symlink=False)
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # env is not passed to the function
            env = kwargs.pop("env")
            if not new:
                try:
                    # Must retrieve exp from env
                    exp: Experiment = env[EXPERIMENT]
                    check_is_exp(exp)
                    # Pass experiment object to kwargs
                    kwargs["exp"] = exp
                except KeyError as e:
                    # Checking we get the particular key error above
                    # and not another random one
                    if e.args[0] == "experiment":
                        logger.error(EXP_ERROR_MSG)

            try:
                r = fn(*args, **kwargs)
            except Exception as e:
                # TODO: add checkpointing ?
                logger.exception(e)
                raise TaskError()

            if new:
                # Function must return new exp instance
                check_is_exp(r)
                exp = r
            # Storing after
            env[EXPERIMENT] = exp
            return r

        def check_is_exp(exp):
            # Using Experiment type like this because of testing
            # https://stackoverflow.com/questions/11146725/isinstance-and-mocking
            if not isinstance(exp, e2c_exp.Experiment):
                logger.error(f"Error: {exp} is not instance of Experiment. Exiting ...")
                raise TaskError()

        return wrapper

    return decorator


@e2ctask(new=True)
def infra(
    scenario_dir: Path,
    artifacts_dir: Path,
    optimization_config=None,
    optimization_id: Optional[UUID] = None,
) -> Experiment:
    exp = Experiment(
        scenario_dir=scenario_dir,
        artifacts_dir=artifacts_dir,
        optimization_config=optimization_config,
        optimization_id=optimization_id,
    )
    exp.infrastructure()
    return exp


@e2ctask()
def network(exp: Experiment) -> None:
    exp.network()


@e2ctask()
def app(exp: Experiment, task: WorkflowTasks, app_conf: Optional[str] = None) -> None:
    exp.application(task=task, app_conf=app_conf)


@e2ctask()
def finalize(exp: Experiment, app_conf: Optional[str] = None, destroy: bool = False):
    exp.finalize(app_conf=app_conf, destroy=destroy)


@e2ctask()
def destroy(exp: Experiment):
    exp.destroy()


@e2ctask()
def destroy_network(exp: Experiment):
    exp.destroy_network()


# TODO: improve handling of env, maybe store ssh in env ?
def ssh(env: Path, **kwargs):
    SSH.load(dir_name=env).ssh(**kwargs)


@e2ctask()
def get_output_dir(exp: Experiment):
    exp.get_output_dir()


@e2ctask(new=True)
def deploy(
    scenario_dir: Path,
    artifacts_dir: Path,
    duration: int,
    repeat: int = 0,
    app_conf_list: list[str] = [],
    is_prepare: bool = True,
    optimization_id: Optional[UUID] = None,
    destroy_on_finish: bool = False,
    destroy_on_fail: bool = False,
    pause: bool = False,
) -> Experiment:
    for current_repeat in range(repeat + 1):
        exp = Experiment(
            scenario_dir=scenario_dir,
            artifacts_dir=artifacts_dir,
            optimization_id=optimization_id,
            app_conf_list=app_conf_list,
            repeat=current_repeat,
        )
        exp.deploy(
            duration=duration,
            is_prepare=is_prepare,
            destroy_on_finish=destroy_on_finish,
            destroy_on_fail=destroy_on_fail,
            pause=pause,
        )
    return exp
