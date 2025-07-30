import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
import enoslib as en
import questionary

import e2clab.tasks as t
import e2clab.utils as utils
from e2clab.constants import (
    COMMAND_RUN_LIST,
    CONF_FILES_LIST,
    ENV_ARTIFACTS_DIR,
    ENV_AUTO_PREFIX,
    ENV_SCENARIO_DIR,
    PATH_SERVICES_PLUGINS,
    WORKFLOW_TASKS,
    Command,
    WorkflowTasks,
)
from e2clab.log import get_logger, init_logging
from e2clab.services import get_available_services, load_services
from e2clab.utils import run_init

from . import ENV_FILE, loaded_dotenv

ASCII_ART = r"""
███████╗██████╗  ██████╗██╗      █████╗ ██████╗
██╔════╝╚════██╗██╔════╝██║     ██╔══██╗██╔══██╗
█████╗   █████╔╝██║     ██║     ███████║██████╔╝
██╔══╝  ██╔═══╝ ██║     ██║     ██╔══██║██╔══██╗
███████╗███████╗╚██████╗███████╗██║  ██║██████╔╝
╚══════╝╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═╝╚═════╝
"""

logger = get_logger(__name__, ["CLI"])


def parse_comma_list(ctx, param, app_conf: str) -> list[str]:
    if app_conf == "":
        return []
    return [c for c in app_conf.strip().split(",")]


def e2c_scenario(func):
    return click.argument(
        "scenario_dir",
        required=True,
        envvar=ENV_SCENARIO_DIR,
        type=click.Path(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            path_type=Path,
        ),
    )(func)


def e2c_artifacts(func):
    return click.argument(
        "artifacts_dir",
        required=True,
        envvar=ENV_ARTIFACTS_DIR,
        type=click.Path(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            path_type=Path,
        ),
    )(func)


def e2c_app_conf(func):
    return click.option(
        "--app_conf",
        type=str,
        default="",
        callback=parse_comma_list,
        help="Application configurations separated by comma.",
    )(func)


class E2clabGroup(click.Group):
    """Subclass of click.Group to display pretty ascii art in helper"""

    def get_help(self, ctx):
        help = super().get_help(ctx)
        return f"{ASCII_ART}\n{help}"


@click.group(
    cls=E2clabGroup,
    help=(
        "Work with your ``e2clab`` experiment defined in `SCENARIO_DIR` "
        "and experiment artifacts in `ARTIFACTS_DIR`. "
        "You can also use environment variables like "
        f"`{ENV_AUTO_PREFIX}_<OPTION_NAME>` "
        "to set an option value e.g. ``E2C_DEBUG=true`` or ``E2C_SCENARIO_DIR=./`` "
        f"or define them in a ``{ENV_FILE}`` file at the root of your experiment."
    ),
    epilog=(
        "Check the documentation at "
        "https://e2clab.gitlabpages.inria.fr/e2clab/ for more details"
    ),
)
@click.version_option()
@click.option("-d", "--debug", is_flag=True, help="Enable debug logging.")
@click.option("-e", "--mute_enoslib", is_flag=True, help="Mute EnOSlib logging.")
@click.option(
    "-a", "--mute_ansible", is_flag=True, help="Mute Ansible spinning callback"
)
@click.option("--ansible_forks", type=int, help="Set Ansible forks level")
def cli(
    debug: bool, mute_enoslib: bool, mute_ansible: bool, ansible_forks: Optional[int]
):
    init_logging(
        level=logging.DEBUG if debug else logging.INFO,
        enable_enoslib=not mute_enoslib,
        mute_ansible=mute_ansible,
        file_handler=False,  # File handler set later in exp
        markup=True,
    )
    if ansible_forks:
        en.set_config(ansible_forks=ansible_forks)
    logger.debug(f"Loaded information from '{ENV_FILE}': {loaded_dotenv}")


@cli.command(
    help="""Deploys scenarios or list of scenarios.
    When using 'app_conf', 'prepare' task from the workflow is only enforced once,
    independently from the 'app_conf' parameter
    """
)
@e2c_scenario
@e2c_artifacts
@click.option(
    "--scenarios_name",
    type=str,
    default="",
    callback=parse_comma_list,
    help="Scenario names separated by comma.",
)
@e2c_app_conf
@click.option(
    "--repeat", default=0, type=int, help="Number of times to repeat the experiment."
)
@click.option(
    "--duration", default=0, type=int, help="Duration of each experiment in seconds."
)
@click.option("--destroy", is_flag=True, help="Run destroy after successful deploy")
@click.option(
    "--destroy-on-fail", is_flag=True, help="Run destroy if there is a workflow error"
)
@click.option(
    "--pause",
    "-p",
    is_flag=True,
    help="Pause after launch step and duration completed, waiting for user input.",
)
def deploy(
    scenario_dir: Path,
    artifacts_dir: Path,
    scenarios_name: list[str],
    app_conf: list[str],
    repeat: int,
    duration: int,
    destroy: bool,
    destroy_on_fail: bool,
    pause: bool,
):
    if scenarios_name:
        for scn in scenarios_name:
            loc_scenario_dir = scenario_dir / scn
            loc_scenario_dir = loc_scenario_dir.resolve()
            if utils.is_valid_setup(loc_scenario_dir, artifacts_dir, Command.DEPLOY):
                t.deploy(
                    loc_scenario_dir,
                    artifacts_dir,
                    duration,
                    repeat,
                    app_conf,
                    True,
                    destroy_on_finish=destroy,
                    destroy_on_fail=destroy_on_fail,
                    pause=pause,
                    env=loc_scenario_dir,
                )
            else:
                logger.error(f"Invalid setup in {scn}, scenario not deployed")
    else:
        if utils.is_valid_setup(scenario_dir, artifacts_dir, Command.DEPLOY):
            t.deploy(
                scenario_dir,
                artifacts_dir,
                duration,
                repeat,
                app_conf,
                True,
                destroy_on_finish=destroy,
                destroy_on_fail=destroy_on_fail,
                pause=pause,
                env=scenario_dir,
            )
        else:
            logger.error("Invalid setup, scenario not deployed.")
            sys.exit(1)


@cli.command(help="Enforce Layers & Services in experiment environment")
@e2c_scenario
@e2c_artifacts
def layers_services(scenario_dir: Path, artifacts_dir: Path):
    logger.info("Started layers-services")
    if utils.is_valid_setup(scenario_dir, artifacts_dir, Command.LYR_SVC):
        t.infra(scenario_dir, artifacts_dir, env=scenario_dir)
    else:
        logger.error("Invalid setup, layers and services not deployed.")
        sys.exit(1)


@cli.command(help="Enforce communication rules in experiment environment.")
@e2c_scenario
def network(scenario_dir: Path):
    if utils.is_valid_setup(scenario_dir, None, Command.NETWORK):
        t.network(env=scenario_dir)
    else:
        logger.error("Invalid setup, network not deployed.")
        sys.exit(1)


@cli.command(help="Enforce Workflow in experiment environment")
@e2c_scenario
@click.argument(
    "task", required=True, type=click.Choice(WORKFLOW_TASKS, case_sensitive=False)
)
@e2c_app_conf
@click.option(
    "--finalize",
    is_flag=True,
    help="Automatically run ``finalize`` after ``launch``",
)
def workflow(scenario_dir: Path, task: str, app_conf: list, finalize: bool):
    e_task = WorkflowTasks(task)
    # We don't check the validity of the 'workflow_env' file
    # because its existence is not mandatory.
    is_app_conf = True if app_conf else False
    if not utils.is_valid_setup(scenario_dir, None, Command.WORKFLOW, is_app_conf):
        logger.error("Invalid setup, workflow not launched")
        sys.exit(1)
    if is_app_conf:
        if e_task == WorkflowTasks.PREPARE:
            logger.error("Can't use an app configuration to prepare a workflow")
            sys.exit(1)
        for conf in app_conf:
            logger.info(f"Launching with configuration: {conf}")
            t.app(task=e_task, app_conf=conf, env=scenario_dir)
            # Finalize between app_confs automatically
            if e_task == WorkflowTasks.LAUNCH and finalize:
                logger.info(f"Finalizing configuration after conf: {conf}")
                t.finalize(app_conf=conf, env=scenario_dir)
    else:
        t.app(task=e_task, env=scenario_dir)
        if finalize and e_task == WorkflowTasks.LAUNCH:
            logger.info("Finalizing after launch completed")
            t.finalize(env=scenario_dir)


@cli.command(help="Frees experiment testbed resources")
@e2c_scenario
@click.option("--network", is_flag=True, help="To only destroy network emulation")
def destroy(scenario_dir: Path, network: bool):
    if network:
        t.destroy_network(env=scenario_dir)
    else:
        t.destroy(env=scenario_dir)


@cli.command(help="Finalize workflow and backup experiment data")
@e2c_scenario
@click.option("--destroy", is_flag=True, help="Run destroy after finalize")
def finalize(scenario_dir: Path, destroy: bool):
    if utils.is_valid_setup(scenario_dir, None, Command.FINALIZE):
        t.finalize(destroy=destroy, env=scenario_dir)
    else:
        logger.error("Invalid setup, scenario not finalized.")
        sys.exit(1)


@cli.command(help="Checks the connectivity to the various testbeds.")
def check_testbeds():
    ENOSLIB_PROVIDERS = ["Grid'5000", "IOT-lab", "Chameleon", "ChameleonEdge"]
    en.check(ENOSLIB_PROVIDERS)


@cli.command(help="Checks configuration files syntax")
@click.option(
    "-c",
    "--command",
    default="deploy",
    type=click.Choice(COMMAND_RUN_LIST, case_sensitive=False),
    help=(
        "Check the configuration files for the command you want to run,"
        "defaults to 'deploy'"
    ),
)
@click.option(
    "-a", "--app_conf", is_flag=True, help="Check ``workflow_env.yaml`` syntax"
)
@e2c_scenario
def check_configuration(command: str, app_conf: list, scenario_dir: Path):
    input_command = Command(command)
    if utils.is_valid_setup(scenario_dir, None, input_command, app_conf):
        logger.info(f"Valid configuration syntax for 'e2clab {command}'")
    else:
        logger.error(f"Invalid configuration syntax for 'e2clab {command}'")
        sys.exit(1)


@cli.command(help="Opens an editor for e2clab configuration files")
@e2c_scenario
def edit(scenario_dir: Path):
    file_type = questionary.select("Select file to edit", choices=CONF_FILES_LIST).ask()
    file = scenario_dir / file_type
    click.edit(filename=str(file), extension="yaml")


@cli.command(help="Utility command to ssh to experiment's remote host")
@click.option("-f", "--forward", is_flag=True, help="ssh tunneling")
@click.option("-l", "--local-port", type=click.INT, help="local port")
@click.option("-r", "--remote-port", type=click.INT, help="remote port")
@e2c_scenario
def ssh(forward: bool, local_port: int, remote_port: int, scenario_dir: Path):
    if forward and not (local_port or remote_port):
        logger.error('Set "--local-port" and "--remote-port" if you use "--forward"')
        sys.exit(1)
    t.ssh(
        env=scenario_dir,
        forward=forward,
        local_port=local_port,
        remote_port=remote_port,
    )


@cli.command(help=f"Initialise DIR to easily use with e2clab by creating a {ENV_FILE}")
@click.option("--scenario-dirname", type=str, prompt="Scenario dir name", default="")
@click.option("--artifacts-dirname", type=str, prompt="Artfacts fir name", default="")
@click.option(
    "--workflow-env",
    type=bool,
    prompt="Use workflow configurations (app_conf) ? ",
    default=False,
    help="Setup a `workflow_env.yaml` file",
)
@click.argument(
    "dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
    default=".",
)
def init(dir: Path, scenario_dirname: str, artifacts_dirname: str, workflow_env: bool):
    run_init(dir, scenario_dirname, artifacts_dirname, workflow_env)


@cli.command(help="Get latest output dir path")
@e2c_scenario
def get_output_dir(scenario_dir: Path):
    scenario_dirpath = Path(scenario_dir).resolve()
    t.get_output_dir(env=scenario_dirpath)


@cli.group(help="Manage E2clab services")
def services():
    pass


@services.command(name="list", help="Get list of installed services.")
def list_command():
    serv_list = get_available_services()
    logger.info(f"Availble services : {serv_list}")


@services.command(
    help="Remove SERVICE_NAME service. See available services: ``e2clab services list``"
)
@click.argument("service_name")
def remove(service_name):
    services = get_available_services()
    if service_name == "Default":
        logger.error("Default service can not be removed !")
        sys.exit(1)
    if service_name not in services:
        logger.error(f"{service_name} not in already available services.")
        sys.exit(1)
    service_file = PATH_SERVICES_PLUGINS / f"{service_name}.py"
    service_file.unlink()
    logger.info(f"Successfully removed {service_name}")


@services.command(help="Add NEW_SERVICE_FILE to E2clab user-defined services.")
@click.argument("new_service_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--copy/--link",
    default=True,
    help="Choose to use a copy of your e2clab service file or a symlink.",
)
def add(new_service_file: Path, copy: bool):
    dest_folder = PATH_SERVICES_PLUGINS
    if not new_service_file.is_file():
        logger.error(f"{new_service_file} is not a file")
        sys.exit(1)
    if not new_service_file.suffix == ".py":
        logger.error("A service file must be a python file")
        sys.exit(1)
    future_service_name = new_service_file.stem
    dest_file = dest_folder / new_service_file.name
    dest_file = dest_file.resolve()
    new_service_file = new_service_file.resolve()
    print(dest_file)
    if dest_file.exists():
        logger.error(f"{new_service_file} already exists")
        sys.exit(1)
    if copy:
        # Copies service file to services/plugins
        shutil.copyfile(new_service_file, dest_file)
    else:
        # Links file to services/plugins
        os.symlink(new_service_file, dest_file)
    # Check that the service is correctly imported
    # i.e. that a service with the same name as the file can be imported
    try:
        load_services([future_service_name])
    except KeyError as e:
        err_msg = (
            f"Error importing new {future_service_name}. "
            f"Python file does not contain a correct e2clab service class: {e}."
        )
        logger.error(err_msg)
        dest_file.unlink()
        sys.exit(1)
    else:
        logger.info(f"Correctly imported: {future_service_name}.")


def main():
    """Importing env variables from .env file and running command line"""
    cli(auto_envvar_prefix=ENV_AUTO_PREFIX)
