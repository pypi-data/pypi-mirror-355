import os
from abc import abstractmethod
from typing import Optional

import bugsnag
import toml
import typer
from atom.api import Atom

from cerebrium.defaults import (
    COMPUTE,
    COOLDOWN,
    CPU,
    DISABLE_AUTH,
    DOCKER_BASE_IMAGE_URL,
    ENTRYPOINT,
    EXCLUDE,
    GPU_COUNT,
    HEALTHCHECK_ENDPOINT,
    READYCHECK_ENDPOINT,
    INCLUDE,
    MAX_REPLICAS,
    MEMORY,
    MIN_REPLICAS,
    PORT,
    PRE_BUILD_COMMANDS,
    PROVIDER,
    PYTHON_VERSION,
    REGION,
    REPLICA_CONCURRENCY,
    SHELL_COMMANDS,
    RESPONSE_GRACE_PERIOD,
    DOCKERFILE_PATH,
    SCALING_METRIC,
    SCALING_TARGET,
    SCALING_BUFFER,
    ROLLOUT_DURATION_SECONDS,
)
from cerebrium.utils.logging import cerebrium_log


class TOMLConfig(Atom):
    @abstractmethod
    def __toml__(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def __json__(self) -> dict:
        raise NotImplementedError


class ScalingConfig(TOMLConfig):
    min_replicas: int = MIN_REPLICAS
    max_replicas: int = MAX_REPLICAS
    cooldown: int = COOLDOWN
    replica_concurrency: int = REPLICA_CONCURRENCY
    response_grace_period: int = RESPONSE_GRACE_PERIOD
    scaling_metric: str = SCALING_METRIC
    scaling_target: int = SCALING_TARGET
    scaling_buffer: int = SCALING_BUFFER
    roll_out_duration_seconds: int = ROLLOUT_DURATION_SECONDS

    def __toml__(self) -> str:
        return (
            "[cerebrium.scaling]\n"
            f"min_replicas = {self.min_replicas}\n"
            f"max_replicas = {self.max_replicas}\n"
            f"cooldown = {self.cooldown}\n"
            f"replica_concurrency = {self.replica_concurrency}\n"
            f"response_grace_period = {self.response_grace_period}\n"
            f'scaling_metric = "{self.scaling_metric}"\n'
            f"scaling_target = {self.scaling_target}\n"
            f"scaling_buffer = {self.scaling_buffer}\n"
            f"roll_out_duration_seconds = {self.roll_out_duration_seconds}\n\n"
        )

    def __json__(self) -> dict:
        return {
            "minReplicaCount": self.min_replicas,
            "maxReplicaCount": self.max_replicas,
            "cooldownPeriodSeconds": self.cooldown,
            "replicaConcurrency": self.replica_concurrency,
            "responseGracePeriodSeconds": self.response_grace_period,
            "scalingMetric": self.scaling_metric,
            "scalingTarget": self.scaling_target,
            "scalingBuffer": self.scaling_buffer,
            "rollOutDurationSeconds": self.roll_out_duration_seconds,
        }


class HardwareConfig(TOMLConfig):
    cpu: float = CPU
    memory: float = MEMORY
    compute: str = COMPUTE
    gpu_count: int = GPU_COUNT
    provider: str = PROVIDER
    region: str = REGION

    def __toml__(self) -> str:
        gpu_count_line = f"gpu_count = {self.gpu_count}\n" if self.compute != "CPU" else ""
        return (
            "[cerebrium.hardware]\n"
            f"cpu = {self.cpu}\n"
            f"memory = {self.memory}\n"
            f'compute = "{self.compute}"\n' + gpu_count_line + "\n"
        )

    def __json__(self) -> dict:
        if self.compute == "CPU":
            return {
                "cpu": self.cpu,
                "memory": self.memory,
                "compute": self.compute,
                "provider": self.provider,
                "region": self.region,
            }
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "compute": self.compute,
            "gpuCount": self.gpu_count,
            "provider": self.provider,
            "region": self.region,
        }


class CustomRuntimeConfig(TOMLConfig):
    entrypoint: list[str] = ENTRYPOINT
    port: int = PORT
    healthcheck_endpoint: str = HEALTHCHECK_ENDPOINT
    readycheck_endpoint: str = READYCHECK_ENDPOINT
    dockerfile_path: str = DOCKERFILE_PATH

    def __toml__(self) -> str:
        return (
            "[cerebrium.runtime.custom]\n"
            f"entrypoint = {self.entrypoint}\n"
            f'port = "{self.port}"\n'
            f'healthcheck_endpoint = "{self.healthcheck_endpoint}"\n'
            f'readycheck_endpoint = "{self.readycheck_endpoint}"\n'
            f'dockerfile_path = "{self.dockerfile_path}"\n\n'
        )

    def __json__(self) -> dict:
        return {
            "entrypoint": (
                self.entrypoint
                if isinstance(self.entrypoint, list)
                else self.entrypoint.split()
            ),
            "port": self.port,
            "healthcheckEndpoint": self.healthcheck_endpoint,
            "readycheckEndpoint": self.readycheck_endpoint,
            "dockerfilePath": self.dockerfile_path,
        }


class DeploymentConfig(TOMLConfig):
    name: str
    python_version: str = PYTHON_VERSION
    docker_base_image_url: str = DOCKER_BASE_IMAGE_URL
    include: list[str] = INCLUDE
    exclude: list[str] = EXCLUDE
    shell_commands: list[str] = SHELL_COMMANDS
    pre_build_commands: list[str] = PRE_BUILD_COMMANDS
    disable_auth: bool = DISABLE_AUTH
    # TODO: Remove/Deprecate this in favor of scaling_config
    roll_out_duration_seconds: int = ROLLOUT_DURATION_SECONDS

    def __toml__(self) -> str:
        shell_commands = (
            f"shell_commands = {self.shell_commands}\n" if self.shell_commands else ""
        )

        return (
            "[cerebrium.deployment]\n"
            f'name = "{self.name}"\n'
            f'python_version = "{self.python_version}"\n'
            f'docker_base_image_url = "{self.docker_base_image_url}"\n'
            f"disable_auth = {str(self.disable_auth).lower()}\n"
            f"include = {self.include}\n"
            f"exclude = {self.exclude}\n" + shell_commands + "\n"
        )

    def __json__(self) -> dict:
        return {
            "name": self.name,
            "pythonVersion": self.python_version,
            "baseImage": self.docker_base_image_url,
            "include": self.include,
            "exclude": self.exclude,
            "shellCommands": self.shell_commands,
            "preBuildCommands": self.pre_build_commands,
            "disableAuth": self.disable_auth,
            "rollOutDurationSeconds": self.roll_out_duration_seconds,
        }


class DependencyConfig(Atom):
    pip: dict[str, str] = {}
    conda: dict[str, str] = {}
    apt: dict[str, str] = {}

    paths: dict[str, str] = {"pip": "", "conda": "", "apt": ""}

    def __toml__(self) -> str:
        pip_strings = (
            "[cerebrium.dependencies.pip]\n"
            + "\n".join(f'"{key}" = "{value}"' for key, value in self.pip.items())
            + "\n"
            if self.pip
            else ""
        )
        conda_strings = (
            "[cerebrium.dependencies.conda]\n"
            + "\n".join(f'"{key}" = "{value}"' for key, value in self.conda.items())
            + "\n"
            if self.conda != {}
            else ""
        )
        apt_strings = (
            "[cerebrium.dependencies.apt]\n"
            + "\n".join(f'"{key}" = "{value}"' for key, value in self.apt.items())
            + "\n"
            if self.apt != {}
            else ""
        )
        if pip_strings or conda_strings or apt_strings:
            return pip_strings + conda_strings + apt_strings + "\n"
        return ""

    def __json__(self) -> dict:
        from cerebrium.utils.requirements import parse_requirements
        import os

        # Convert file paths to actual dependencies if files are specified
        pip_deps = self.pip.copy()
        conda_deps = self.conda.copy()
        apt_deps = self.apt.copy()

        # If file paths are specified, read and merge the contents
        if self.paths.get("pip") and os.path.exists(self.paths["pip"]):
            file_deps = parse_requirements(self.paths["pip"])
            pip_deps.update(file_deps)

        if self.paths.get("conda") and os.path.exists(self.paths["conda"]):
            file_deps = parse_requirements(self.paths["conda"])
            conda_deps.update(file_deps)

        if self.paths.get("apt") and os.path.exists(self.paths["apt"]):
            file_deps = parse_requirements(self.paths["apt"])
            apt_deps.update(file_deps)

        return {
            "pip": pip_deps,
            "conda": conda_deps,
            "apt": apt_deps,
            "pip_file": self.paths["pip"],
            "conda_file": self.paths["conda"],
            "apt_file": self.paths["apt"],
        }


class PartnerConfig(TOMLConfig):
    name: str

    def __toml__(self) -> str:
        return "[cerebrium.partner.service]\n" f'name = "{self.name}"\n\n'

    def __json__(self) -> dict:
        return {"partnerName": self.name}


class CerebriumConfig(Atom):
    deployment: DeploymentConfig
    hardware: HardwareConfig
    scaling: ScalingConfig
    dependencies: DependencyConfig
    custom_runtime: CustomRuntimeConfig | None = None
    partner_services: PartnerConfig | None = None

    def to_toml(self, file: str = "cerebrium.toml") -> None:
        with open(file, "w", newline="\n") as f:
            f.write(self.deployment.__toml__())
            f.write(self.hardware.__toml__())
            f.write(self.scaling.__toml__())
            if self.custom_runtime is not None:
                f.write(self.custom_runtime.__toml__())
            f.write(self.dependencies.__toml__())

    def to_payload(self) -> dict:
        payload = {
            **self.deployment.__json__(),
            **self.hardware.__json__(),
            **self.scaling.__json__(),
        }
        if self.custom_runtime is not None:
            payload.update(self.custom_runtime.__json__())
            payload["runtime"] = "custom"
        elif self.partner_services is not None:
            payload["partnerService"] = self.partner_services.name
            payload["runtime"] = self.partner_services.name
        else:
            payload["runtime"] = "cortex"
        return payload


def get_validated_config(config_file: str, name: Optional[str], quiet: bool) -> CerebriumConfig:
    try:
        toml_config = toml.load(config_file)["cerebrium"]
    except FileNotFoundError:
        if quiet:
            raise FileNotFoundError(f"Config file {config_file} not found")

        cerebrium_log(
            message="Could not find cerebrium.toml file. Please run `cerebrium init` to create one.",
            color="red",
        )
        bugsnag.notify(
            Exception(
                "Could not find cerebrium.toml file. Please run `cerebrium init` to create one."
            )
        )
        raise typer.Exit(1)
    except KeyError:
        cerebrium_log(
            message="Could not find 'cerebrium' key in cerebrium.toml file. Please run `cerebrium init` to create one.",
            color="red",
        )
        raise typer.Exit(1)
    except Exception as e:
        bugsnag.notify(e)
        cerebrium_log(message=f"Error loading cerebrium.toml file: {e}", color="red")
        raise typer.Exit(1)

    deployment_section = toml_config.get("deployment", {})
    hardware_section = toml_config.get("hardware", {})
    config_error = False

    if not deployment_section:
        cerebrium_log(
            message="Deployment section is required in cerebrium.toml file. Please add a 'deployment' section.",
            level="ERROR",
        )
        config_error = True
    if "name" not in deployment_section:
        cerebrium_log(
            message="`deployment.name` is required in cerebrium.toml file. Please add a 'name' field to the 'deployment' section.",
            level="ERROR",
        )
        config_error = True
    if "gpu" in hardware_section:
        cerebrium_log(
            message="`hardware.gpu` field is deprecated. Please use `hardware.compute` instead.",
            level="ERROR",
        )
        config_error = True
    if "cuda_version" in deployment_section:
        cerebrium_log(
            message="`deployment.cuda_version` field is deprecated. Please use `deployment.docker_base_image_url` instead.",
            level="ERROR",
        )
        config_error = True
    if hardware_section.get("provider", "aws") == "coreweave":
        cerebrium_log(
            message="Cortex V4 does not support Coreweave. Please consider updating your app to AWS.",
            level="ERROR",
        )
        config_error = True
    if config_error:
        raise typer.Exit(1)

    if name:
        deployment_section["name"] = name

    deployment_config = DeploymentConfig(**deployment_section)
    scaling_config = ScalingConfig(**toml_config.get("scaling", {}))
    hardware_config = HardwareConfig(**hardware_section)

    custom_runtime_config = None
    if "runtime" in toml_config and "custom" in toml_config["runtime"]:
        if "entrypoint" in toml_config["runtime"]["custom"] and isinstance(
            toml_config["runtime"]["custom"]["entrypoint"], str
        ):
            toml_config["runtime"]["custom"]["entrypoint"] = toml_config["runtime"]["custom"][
                "entrypoint"
            ].split()
        if (
            "dockerfile_path" in toml_config["runtime"]["custom"]
            and toml_config["runtime"]["custom"]["dockerfile_path"] != ""
            and not os.path.exists(toml_config["runtime"]["custom"]["dockerfile_path"])
        ):
            cerebrium_log(
                message="Dockerfile path does not exist. Please check the path in the toml file.",
                color="red",
            )
            raise typer.Exit(1)
        custom_runtime_config = CustomRuntimeConfig(**toml_config["runtime"]["custom"])

    dependency_config = DependencyConfig(**toml_config.get("dependencies", {}))

    partner_config = None
    for partner in ["deepgram", "rime"]:
        if "runtime" in toml_config and partner in toml_config["runtime"]:
            partner_config = PartnerConfig(name=partner)

    return CerebriumConfig(
        scaling=scaling_config,
        hardware=hardware_config,
        deployment=deployment_config,
        dependencies=dependency_config,
        custom_runtime=custom_runtime_config,
        partner_services=partner_config,
    )
