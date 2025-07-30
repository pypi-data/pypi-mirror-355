"""
Main experiment class to manage steps of the experimental workflows:
- Infrastructure
- Networking
- Workflow execution
"""

import pickle
import subprocess
import time
from pathlib import Path
from typing import Optional
from uuid import UUID

import questionary
from enoslib import Host, Roles

import e2clab.constants.default as default
from e2clab.app import App
from e2clab.constants import SSH_STATE_NAME, STATE_DIR, ConfFiles, WorkflowTasks
from e2clab.errors import (
    E2clabError,
    E2clabNetworkError,
    E2clabServiceError,
    E2clabSSHError,
    E2clabWorkflowError,
)
from e2clab.infra import Infrastructure
from e2clab.log import config_file_logger, get_logger
from e2clab.network import Network
from e2clab.objs import ExperimentMeta
from e2clab.probe import TaskProbe


class Experiment:
    def __init__(
        self,
        scenario_dir: Path,
        artifacts_dir: Path,
        repeat: Optional[int] = None,
        app_conf_list: list[str] = [],
        optimization_config=None,
        optimization_id: Optional[UUID] = None,
    ) -> None:
        self.id = time.strftime("%Y%m%d-%H%M%S")
        self.scenario_dir = scenario_dir.resolve()
        self.artifacts_dir = artifacts_dir.resolve()

        # 'Deploy' related
        self.app_conf_list = app_conf_list
        self.repeat = repeat

        # 'Optimization' related
        self.optimization_id = optimization_id
        self.optimization_config = optimization_config

        self.logger = get_logger(__name__, ["EXP"])

        # Experiment components
        self.infra: Optional[Infrastructure] = None
        self.net: Optional[Network] = None
        self.app: Optional[App] = None

        # Probing execution timestamp
        self.probe = TaskProbe()

        self.meta = ExperimentMeta(id=self.id, scenario=self.scenario_dir.stem)
        # FILE USED BY USERS TO DEPLOY THEIR APPLICATIONS
        self.experiment_dir = Path(f"{self.scenario_dir}/{self.id}")
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        # Outputing e2clab logs into experiment dir
        log_file, error_file = config_file_logger(self.experiment_dir)

        self.layers_services_val_file = (
            self.experiment_dir / default.LAYERS_SERVICES_VALIDATE_FILE
        )

        self.logger.info(f"Experiment directory is: {self.experiment_dir}")
        self.logger.info(f"Logging file at {log_file}")
        self.logger.info(f"Error file at {error_file}")

    def __setstate__(self, state):
        """Ran when unpickling"""
        self.__dict__.update(state)
        # re-configure loggers
        config_file_logger(self.experiment_dir)

    def infrastructure(self) -> int:
        """
        Deploy experiment infrastructure
        """
        self.logger.info("Deploying experiment inrastructure")

        conf_file = self.scenario_dir / ConfFiles.LAYERS_SERVICES

        # Infrastructure
        self.logger.debug("Init infrastructure")
        self.infra = Infrastructure(conf_file, self.optimization_id)
        self.logger.debug("Preparing infrastructure")
        self.infra.prepare()
        self.logger.debug("Deploying infrastructure")
        try:
            roles, networks = self.infra.deploy(
                artifacts_dir=self.artifacts_dir,
                meta=self.meta,
            )
        except E2clabServiceError as e:
            self.logger.error(e)
            raise E2clabError
        self.roles = roles
        self.networks = networks
        self.logger.info("Experiment infrastructure deployed")

        # Timestamp for infra deployment
        self.probe.set_start("infra")

        # Generate Layers Services validate file
        self._dump_application_parameters()
        # Recording user_roles
        user_roles = SSH(self.infra.get_ssh_data(), self.scenario_dir)
        user_roles.dump()

        return self.id

    def network(self) -> None:
        """
        Deploy experiment network emulation
        """
        if not self.infra:
            raise E2clabError(
                "Cannot deploy a network without a deployed infrastructure"
            )

        self.logger.info("Deploying experiment network")

        conf_file = self.scenario_dir / ConfFiles.NETWORK

        # Network
        self.logger.debug("Init network")
        self.net = Network(conf_file, self.roles, self.networks)
        self.logger.debug("Preparing network")
        self.net.prepare()
        self.logger.debug("Deploying network")
        self.net.deploy()
        self.logger.debug("Validating network")
        self.net.validate(self.experiment_dir)

        self.logger.info("Experiment network deployed")

    def application(self, task: WorkflowTasks, app_conf: Optional[str] = None) -> None:
        """
        Enforce workflow definition
        """
        if not self.infra:
            raise E2clabError("Cannot run a workflow without a deployed infrastructure")

        env_conf = None

        if app_conf:
            env_conf = self.scenario_dir / ConfFiles.WORKFLOW_ENV

        conf_file = self.scenario_dir / ConfFiles.WORKFLOW

        self.app = App(
            config=conf_file,
            experiment_dir=self.experiment_dir,
            scenario_dir=self.scenario_dir,
            artifacts_dir=self.artifacts_dir,
            roles=self.roles,
            all_serv_extra_inf=self.infra.get_all_services_extra_info(),
            app_conf=app_conf,
            env_config=env_conf,
            optimization_config=self.optimization_config,
        )

        # Enforce task
        self.logger.info(f"Enforcing workflow:{task.value}")
        self.run_task(task=task, current_repeat=self.repeat)
        self.logger.info(f"Done enforcing workflow:{task.value}")

    def run_task(self, task: WorkflowTasks, current_repeat: Optional[int] = None):
        """Wrapper for application run_task"""
        if not self.app:
            raise E2clabError("Failed initializing App")
        self.probe.set_start(record_name=task.value)
        self.app.run_task(task=task, current_repeat=current_repeat)
        self.probe.set_end(record_name=task.value)

    def finalize(self, app_conf: Optional[str] = None, destroy: bool = False) -> None:
        """
        Finalize experiment
        """
        if not self.infra or not self.app:
            raise E2clabError(
                "Cannot finalize an experiment without "
                "an infrastructure or before running 'workflow'"
            )

        output_dir = self.experiment_dir
        if app_conf:
            output_dir = self.experiment_dir / app_conf

        self.logger.info("Finalizing experiment")
        self.logger.info("Running workflow 'finalize'")
        self.run_task(WorkflowTasks.FINALIZE, current_repeat=self.repeat)
        self.logger.info("Finalizing layers and services")
        self.infra.finalize(output_dir=output_dir)
        self.logger.info("Done finalizing experiment")

        if destroy:
            self.logger.info("Destroying after successful finish")
            self.destroy()

    def deploy(
        self,
        duration: int,
        is_prepare: bool = True,
        destroy_on_finish: bool = False,
        destroy_on_fail: bool = False,
        pause: bool = False,
    ) -> None:
        """
        Deploy E2Clab experiment
        """
        self.logger.debug(f"[APPLICATION CONF LIST]: {self.app_conf_list}")

        failed = False

        self.logger.info("Starting experiment deployment")
        try:
            # layers_services
            self.infrastructure()
            # network
            self.network()
            # workflow
            self.logger.info("Starting experiment workflow")
            if self.app_conf_list:
                for app_conf in self.app_conf_list:
                    self.logger.info(f"Running experiment configuration '{app_conf}'")
                    is_prepare = self._run_deploy(duration, is_prepare, app_conf, pause)
            else:
                is_prepare = self._run_deploy(duration, is_prepare, None, pause)

            self.logger.info("Done experiment deployment")
        except E2clabServiceError as e:
            self.logger.error(f"Service deployment error: {e}")
            failed = True
        except E2clabNetworkError as e:
            self.logger.error(f"Network deployment error: {e}")
            failed = True
        except E2clabWorkflowError as e:
            self.logger.error(f"Workflow error: {e}")
            failed = True
        finally:
            if failed and destroy_on_fail:
                self.logger.info("Running destroy after failed workflow")
                self.destroy()
            elif destroy_on_finish:
                self.logger.info("Destroying after successful deploy")
                self.destroy()

    def _run_deploy(
        self,
        duration: int,
        is_prepare: bool,
        app_conf: Optional[str] = None,
        pause: bool = False,
    ):
        if is_prepare:
            # No app_conf during prepare stage
            self.application(WorkflowTasks.PREPARE)
            # We prepare our deployment only once
            is_prepare = False
        self.application(WorkflowTasks.LAUNCH, app_conf)

        self.logger.info(f"Waiting for duration: {duration} seconds")
        self.probe.set_start("wait")

        time.sleep(duration)

        self.probe.set_end("wait")
        self.logger.info(f"Finished waiting after {duration} seconds")

        if pause:
            self.logger.info("Pausing experiment")
            input("Press any key to continue...")

        self.logger.info("Finalizing experiment")
        self.finalize(app_conf=app_conf)
        return is_prepare

    def destroy(self) -> None:
        """
        Release (free) computing resources, e.g. kill G5k oar jobs
        """
        if not self.infra:
            raise E2clabError(
                "Can't destroy an uninstantiated infrastructure."
                "Have you run `e2clab layers_services` ?"
            )
        self.logger.info("Destroying provider computing resource")
        self.infra.destroy()
        self.logger.info("Destroyed computing resources")

        self.probe.set_end("infra")

    def destroy_network(self) -> None:
        """Destroy all network emulations currently deployed"""
        if self.net is None:
            self.logger.error("No network emulation currently deployed")
        else:
            self.net.destroy()

    def get_output_dir(self) -> None:
        """Prints experiment directory to stdout"""
        print(self.get_exp_dir())

    def get_exp_id(self) -> str:
        return self.id

    def get_exp_dir(self) -> Path:
        return self.experiment_dir

    def _dump_application_parameters(self) -> None:
        """
        Generates a file with a list of User-Defined Services to be used by the user in
        the network.yaml and workflow.yaml configuration files.
        """
        with open(self.layers_services_val_file, "w") as file:
            self.infra.dump_layers_validate_info(file)


class SSH:
    """User roles for SSH access"""

    def __init__(self, data: dict[str, Roles], dir_name: Path):
        self.data = data
        self.dir_name = dir_name
        self.logger = get_logger(__name__, ["SSH"])

    def dump(self):
        """Dumps self to a pickled file"""
        self.dir_name.mkdir(parents=True, exist_ok=True)
        filename = self.dir_name.joinpath(STATE_DIR).joinpath(SSH_STATE_NAME)
        with filename.open("wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, dir_name: Path) -> "SSH":
        """Load SSH state from a pickled file in the directory"""
        filename = dir_name.joinpath(STATE_DIR).joinpath(SSH_STATE_NAME)
        if not filename.is_file():
            raise E2clabError(
                f"SSH state file {filename} not found. "
                "Have you successfully deployed an infrastructure yet?"
            )

        with filename.open("rb") as f:
            return pickle.load(f)

    def ssh(
        self,
        forward: Optional[bool] = False,
        local_port: Optional[int] = None,
        remote_port: Optional[int] = None,
    ) -> None:
        """Runs a subprocess to ssh to selected remote host"""
        host = self._ask_ssh_host()
        ssh_target = f"{host.user}@{host.address}"
        identity = host.keyfile
        port = host.port
        command = ["ssh", ssh_target]
        # if we want to run ssh tunnelling
        if forward and local_port and remote_port:
            command += ["-NL", f"{local_port}:localhost:{remote_port}"]
        if port is not None:
            command += ["-p", str(port)]
        if identity is not None:
            command += ["-i", str(identity)]
        self.logger.debug(f"SSH COMMAND : {command}")
        # TODO: Get inspiration from G5K tunnel in enoslib, may be better
        try:
            if forward:
                self.logger.info(f"Access localhost:{local_port}")
            else:
                self.logger.info(f"Accessing {host.address}")
            subprocess.run(command)
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise E2clabSSHError

    def _ask_ssh_host(self) -> Host:
        """Queries user for host to ssh to

        Returns:
            Host: host to ssh to
        """
        self.logger.debug(f"SSH roles: {self.data}")

        layer_answer = questionary.select(
            "Select layer to ssh to", choices=self.data.keys()
        ).ask()

        roles_answer = questionary.select(
            "Select host to ssh to", choices=self.data[layer_answer]
        ).ask()

        host: Host = self.data[layer_answer][roles_answer][0]
        return host
