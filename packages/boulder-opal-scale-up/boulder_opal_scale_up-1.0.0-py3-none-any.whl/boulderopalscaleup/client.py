# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.
"""
Client for the Boulder Opal Scale Up API.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import grpc
import numpy as np
import qm
from boulderopalscaleupsdk.agent import Agent, AgentSettings, TaskHandler
from boulderopalscaleupsdk.common.dtypes import ISO8601Datetime
from boulderopalscaleupsdk.device.config_loader import DeviceConfigLoader
from boulderopalscaleupsdk.device.controller.quantum_machines import QuantumMachinesControllerInfo
from boulderopalscaleupsdk.device.processor import (
    SuperconductingProcessor,
)
from boulderopalscaleupsdk.device.processor.superconducting_processor import Resonator, Transmon
from boulderopalscaleupsdk.experiments import Experiment
from boulderopalscaleupsdk.grpc_interceptors.auth import AuthInterceptor
from boulderopalscaleupsdk.plotting import Plot
from boulderopalscaleupsdk.protobuf.v1 import agent_pb2, device_pb2, device_pb2_grpc, task_pb2
from boulderopalscaleupsdk.routines.common import Routine
from boulderopalscaleupsdk.utils.serial_utils import convert_tuples_to_lists, sanitize_keys
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct
from qm.exceptions import (
    AnotherJobIsRunning,
    CantCalibrateElementError,
)
from qm.grpc import qua

from boulderopalscaleup.auth import get_default_api_key_auth
from boulderopalscaleup.constants import API_KEY_NAME, SERVER_URL
from boulderopalscaleup.plots import Plotter

from .utils import display_node_information

if TYPE_CHECKING:
    from qctrlclient import ApiKeyAuth

LOG = logging.getLogger(__name__)


class ScaleUpServerError(Exception):
    """
    Exception raised by client based on server behaviour.
    """

    def __init__(self, message: str):
        super().__init__(message)


class QctrlScaleUpClient:
    """
    Q-CTRL Scale Up client providing API access to experiments.
    """

    def __init__(  # noqa: PLR0913
        self,
        qmm: qm.QuantumMachinesManager,
        app_name: str,
        api_key: str | None = None,
        api_url: str = SERVER_URL,
        local_mode: bool = False,
        export_data: bool = False,
    ):
        """
        Initialize the client.

        Parameters
        ----------
        qmm : qm.QuantumMachinesManager
            The Quantum Machines manager instance used to manage quantum machines.
        app_name : str
            The name of the application using the Scale Up API.
        api_key : str or None, optional
            The API key for authenticating with the Q-CTRL server. If not provided,
            the key is retrieved from the environment variable `QCTRL_API_KEY`.
        api_url : str, optional
            The URL of the Boulder Opal Scale Up server. Defaults to the value of `SERVER_URL`.
        local_mode : bool, optional
            If True, uses a local unauthenticated server. Defaults to False.
        export_data : bool, optional
            If True, experiment data will be exported to files. Defaults to False.

        Raises
        ------
        RuntimeError
            If no API key is provided and the environment variable `QCTRL_API_KEY` is not set.
        """
        self.api_url = api_url
        self.qmm = qmm

        if api_key is None:
            try:
                api_key = os.environ[API_KEY_NAME]
            except KeyError as error:
                raise RuntimeError(
                    "No API key provided in environment or function call. "
                    "To call this function without arguments, "
                    f"save your API key's value in the {API_KEY_NAME} "
                    "environment variable.",
                ) from error
        self.auth: ApiKeyAuth | None = (
            (get_default_api_key_auth(api_key)) if not local_mode else None
        )
        self.channel = self._create_channel()
        self.app_name = app_name

        self.agent_settings = AgentSettings(
            agent_id="dummy_agent_id",
            remote_url=self.api_url,
        )

        self.device_name: str | None = None

        self._export_data = export_data
        self._export_name: str = "experiment"

        self._processor: SuperconductingProcessor | None = None
        self._controller_info: QuantumMachinesControllerInfo | None = None

        self.qm: qm.QuantumMachine | None = None

    async def create_device(
        self,
        device_name: str,
        device_config_path: Path,
    ) -> None:
        """
        Create and initialize a device for experiments.

        Parameters
        ----------
        device_name : str
            The name of the device to be created.
        device_config_path : Path
            The file path to the device configuration file.

        Raises
        ------
        ScaleUpServerError
            If the device initialization fails on the server.
        """
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)

        device_info = DeviceConfigLoader(device_config_path).load_device_info()
        device_data = Struct()
        device_data.update(device_info.to_dict())

        request = device_pb2.CreateRequest(
            app_name=self.app_name,
            device_name=device_name,
            device_data=device_data,
        )
        response: device_pb2.CreateResponse = device_stub.Create(request)
        if not response.done:
            raise ScaleUpServerError("Failed to create device.")

    async def load_device(self, device_name: str | None) -> None:
        """
        Load the current state of the device.

        Returns
        -------
        device_pb2.LoadResponse
            The response object containing the device state.
        """
        if device_name is None:
            raise RuntimeError("Device name is not set.")

        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)

        request = device_pb2.LoadRequest(
            device_name=device_name,
        )
        response: device_pb2.LoadResponse = device_stub.Load(request)

        if response.processor_data is None or response.controller_data is None:
            raise ScaleUpServerError(f"Failed to load {device_name} device.")

        processor_data_dict = MessageToDict(response.processor_data)

        self._processor = SuperconductingProcessor.from_dict(processor_data_dict)

        controller_info_data_struct = response.controller_data
        controller_info_data_dict = MessageToDict(controller_info_data_struct)

        self._controller_info = QuantumMachinesControllerInfo.model_validate(
            controller_info_data_dict,
        )

        self.device_name = device_name

    def display_device_summary(
        self,
        device_name: str | None = None,
        node_name: str | None = None,
    ) -> None:
        """
        Displays a summary of resonator and transmon nodes in the specified device.

        Parameters
        ----------
        device_name : str or None, optional
            The name of the device to summarize. If None, the current device is summarized.
        node_name : str or None, optional
            The name of the node to summarize. If None, all applicable nodes are summarized.
        """
        if not device_name or device_name == self.device_name:
            return self._display_current_device_summary(node_name)
        raise NotImplementedError("Cannot retrieve summary of non-current devices")

    def _display_current_device_summary(self, node_name: str | None) -> None:
        """
        Displays a summary of resonator and transmon nodes in the current device.

        Parameters
        ----------
        node_name : str or None, optional
            The name of the node to summarize. If None, all applicable nodes are summarized.

        Raises
        ------
        RuntimeError
            If the device name is not set, the processor is not loaded,
            or the specified node does not exist.
        """
        # Check if device name and processor are set
        if not self.device_name:
            raise RuntimeError("Device name not set. Call create_device first.")

        if not self._processor:
            raise RuntimeError("Processor not loaded. Call load_device first.")

        if node_name and node_name not in self._processor.nodes:
            raise RuntimeError(f"Node {node_name} not found in processor.")

        if node_name is None:
            for n_name, n_value in self._processor.nodes.items():
                if isinstance(n_value, Resonator | Transmon):
                    display_node_information(n_name, n_value.get_summary_dict())
        else:
            n_value = self._processor.nodes[node_name]
            if isinstance(n_value, Resonator | Transmon):
                display_node_information(node_name, n_value.get_summary_dict())
            else:
                raise RuntimeError(
                    "Summary only displays nodes of type Resonator or Transmon, "
                    f"and node {node_name} is neither.",
                )

    async def update_device(self) -> None:
        """
        Update the device with updated data.

        Returns
        -------
        device_pb2.UpdateResponse
            The response object containing the updated device state.
        """
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)

        latest_processor = self._processor
        if latest_processor is None:
            raise RuntimeError("No processor found. Please load the device first.")

        processor_dict = latest_processor.to_dict()

        processor_struct = Struct()
        ParseDict(processor_dict, processor_struct)

        latest_controller_info = self._controller_info
        if latest_controller_info is None:
            raise RuntimeError("No controller info found. Please load the device first.")

        controller_info_dict = latest_controller_info.model_dump()
        controller_info_dict_sanitized = sanitize_keys(controller_info_dict)
        controller_info_dict_sanitized = convert_tuples_to_lists(controller_info_dict_sanitized)
        controller_info_struct = Struct()
        ParseDict(controller_info_dict_sanitized, controller_info_struct)

        request = device_pb2.UpdateRequest(
            device_name=self.device_name,
            processor_data=processor_struct,
            controller_data=controller_info_struct,
        )
        response: device_pb2.UpdateResponse = device_stub.Update(request)

        processor_data_struct = response.processor_data
        processor_data_dict = MessageToDict(processor_data_struct)

        self._processor = SuperconductingProcessor.from_dict(processor_data_dict)

        controller_info_data_struct = response.controller_data
        controller_info_data_dict = MessageToDict(controller_info_data_struct)

        self._controller_info = QuantumMachinesControllerInfo.model_validate(
            controller_info_data_dict,
        )

    async def delete_device(self, device_name: str | None = None) -> None:
        """
        Delete the specified device.

        Parameters
        ----------
        device_name : str or None, optional
            The name of the device to delete. If None, deletes current device.
        """
        if device_name is None:
            if self.device_name is None:
                raise RuntimeError("No current device to delete")
            device_name = self.device_name

        if not self._delete_device_from_server(device_name):
            raise ScaleUpServerError(f"Failed to delete f{device_name} device from server.")

        if self.device_name == device_name:
            self._clear_current_device()

    def _delete_device_from_server(self, device_name: str) -> bool:
        """
        Delete the device from the server.
        """
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)
        request = device_pb2.DeleteRequest(device_name=device_name)
        response: device_pb2.DeleteResponse = device_stub.Delete(request)
        if response is None:
            LOG.error("Invalid response from server when attempting to delete device")
            return False
        return response.done

    def _clear_current_device(self) -> None:
        self.device_name = None
        self._processor = None
        self._controller_info = None

    def get_processor(self) -> SuperconductingProcessor | None:
        """
        Return the current processor.

        Returns
        -------
        SuperconductingProcessor or None
            The current processor instance, or None if not set.
        """
        return self._processor

    def get_controller_info(self) -> QuantumMachinesControllerInfo | None:
        """
        Return the current controller information.

        Returns
        -------
        QuantumMachinesControllerInfo or None
            The current controller information instance, or None if not set.
        """
        return self._controller_info

    def _get_channel_interceptors(self) -> list:
        """
        Get the interceptors for the gRPC channel.
        """
        return [AuthInterceptor(self.auth)] if self.auth else []

    def _create_channel(self) -> grpc.Channel:
        """
        Create a gRPC channel.
        """
        host = self.api_url.split(":")[0]
        if host in ["localhost", "127.0.0.1", "0.0.0.0", "::"]:
            channel = grpc.insecure_channel(self.api_url)
        else:
            channel = grpc.secure_channel(self.api_url, grpc.ssl_channel_credentials())
        return grpc.intercept_channel(channel, *self._get_channel_interceptors())

    def set_api(self, api_url: str) -> None:
        """
        Configure the API URL for the client.

        Parameters
        ----------
        api_url : str
            The URL of the Boulder Opal Scale Up server.
        """
        self.api_url = api_url

    async def run_experiment(self, experiment: Experiment) -> None:
        """
        Execute an experiment.

        Parameters
        ----------
        experiment : Experiment
            The experiment object containing the routine and parameters to be executed.

        Raises
        ------
        RuntimeError
            If the device name is not set before running the experiment.
        """
        if not self.device_name:
            raise RuntimeError("Device name not set. Call create_device first.")

        # Update export file names to use in this experiment.
        timestamp = ISO8601Datetime(datetime.now(tz=timezone.utc)).strftime(
            "%Y%m%d_%H%M%S",
        )
        self._export_name = f"{experiment.experiment_name}_{timestamp}"

        experiment_dump = experiment.model_dump()
        self.export_experiment("parameters", experiment_dump)

        experiment_data = Struct()
        experiment_data.update(experiment_dump)

        self.agent = Agent(
            self.agent_settings,
            AgentTaskHandler(self),
            grpc_interceptors=self._get_channel_interceptors(),
        )

        await self.agent.start_session(
            app=self.app_name,
            device_name=self.device_name,
            routine=experiment.experiment_name,
            data=experiment_data,
        )

    async def run_routine(self, routine: Routine) -> None:
        """
        Execute a routine.
        Parameters
        ----------
        routine : Routine
            The routine object containing the procedure and parameters to be executed.
        """
        if not self.device_name:
            raise RuntimeError("Device name not set. Call create_device first.")

        # Update export file names to use in this experiment.
        timestamp = ISO8601Datetime(datetime.now(tz=timezone.utc)).strftime(
            "%Y%m%d_%H%M%S",
        )
        self._export_name = f"{routine.routine_name}_{timestamp}"

        experiment_dump = routine.model_dump()
        self.export_experiment("parameters", experiment_dump)

        routine_dump = routine.model_dump()

        routine_data = Struct()
        routine_data.update(routine_dump)

        self.agent = Agent(
            self.agent_settings,
            AgentTaskHandler(self),
            grpc_interceptors=self._get_channel_interceptors(),
        )

        await self.agent.start_session(
            app=self.app_name,
            device_name=self.device_name,
            routine=routine.routine_name,
            data=routine_data,
        )

    def export_experiment(self, label: str, data: dict[str, Any]) -> None:
        """
        Export data to a JSON file if `export_data` is enabled.

        Parameters
        ----------
        label : str
            A label to identify the exported data file.
        data : dict[str, Any]
            The data to be exported.

        Notes
        -----
        The exported file is saved in the current working directory with the format
        `<experiment_name>_<timestamp>_<label>.json`.
        """
        if not self._export_data:
            return

        export_dir = Path.cwd() / "exports" / f"{self._export_name}"
        export_dir.mkdir(exist_ok=True)

        timestamp = ISO8601Datetime(datetime.now(tz=timezone.utc)).strftime(
            "%Y%m%d_%H%M%S",
        )
        file_path = export_dir / f"{timestamp}_{label}.json"
        with file_path.open("w") as file:
            json.dump(data, file)

    def get_job_data(self, job_id: str) -> Struct | None:
        """
        Retrieves details about a specific job executed on the device, such as
        its status, execution results, and associated metadata.

        Parameters
        ----------
        job_id : str
            The ID of the job to retrieve.

        Returns
        -------
        Struct | None
            The response object containing the job data or None.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.

        """
        request = device_pb2.GetJobRequest(job_id=job_id)
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)
        response: device_pb2.GetJobResponse = device_stub.GetJob(request)

        if response is None:
            raise ScaleUpServerError("Invalid Response.")

        return response.job_data

    def get_job_history(self, device_name: str) -> RepeatedCompositeFieldContainer[Struct]:
        """
        Retrieves all the jobs that have been previously executed on the given device.

        Parameters
        ----------
        device_name : str
            The name of the device to retrieve the job history for.

        Returns
        -------
        RepeatedCompositeFieldContainer[Struct]
            The response object containing the job history.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.
        """
        request = device_pb2.ListJobsRequest(device_name=device_name)
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)
        response: device_pb2.ListJobsResponse = device_stub.ListJobs(request)

        if response is None:
            raise ScaleUpServerError("Invalid Response.")

        return response.jobs

    def get_job_summary(self, job_id: str) -> Struct | None:
        """
        Retrieves a summary of a specific job executed on the device.

        Parameters
        ----------
        job_id : str
            The ID of the job to retrieve.

        Returns
        -------
        Struct | None
            The response object containing the job summary.

        Raises
        ------
        ScaleUpServerError
            If the response is invalid.
        """
        request = device_pb2.GetJobSummaryRequest(job_id=job_id)
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(self.channel)
        response: device_pb2.GetJobSummaryResponse = device_stub.GetJobSummary(request)

        if response is None:
            raise ScaleUpServerError("Invalid Response.")

        return response.job_summary_data


class AgentTaskHandler(TaskHandler):
    def __init__(self, client: QctrlScaleUpClient) -> None:
        self._client = client

    async def handle(
        self,
        request: agent_pb2.RunQuaProgramRequest
        | agent_pb2.RunQuantumMachinesMixerCalibrationRequest
        | agent_pb2.DisplayResultsRequest,
    ) -> (
        agent_pb2.RunQuaProgramResponse
        | agent_pb2.RunQuantumMachinesMixerCalibrationResponse
        | agent_pb2.DisplayResultsResponse
        | task_pb2.TaskErrorDetail
    ):
        match request:
            case agent_pb2.RunQuaProgramRequest():
                return await _run_program(request, self._client)
            case agent_pb2.RunQuantumMachinesMixerCalibrationRequest():
                return await _run_mixer_calibration(request, self._client)
            case agent_pb2.DisplayResultsRequest():
                return await _display_results(request)


def _initialize_qm(client, config_json: str) -> qm.QuantumMachine:
    """
    Initialize a Quantum Machine from a config JSON string and export the config.
    """
    qua_config = json.loads(config_json)
    client.export_experiment("config", qua_config)
    return client.qmm.open_qm(qua_config)  # type: ignore[assignment]


async def _run_program(
    program_request: agent_pb2.RunQuaProgramRequest,
    client: QctrlScaleUpClient,
) -> agent_pb2.RunQuaProgramResponse:
    """
    Run an experiment on the device.
    """
    LOG.info("Running experiment task %s", program_request)

    LOG.info("Initializing QM.")
    client.qm = _initialize_qm(client, program_request.config)

    LOG.info("Executing program.")
    qua_program = json.loads(program_request.program)
    client.export_experiment("program", qua_program)
    program = qm.Program(program=qua.QuaProgram.from_dict(qua_program))
    qm_job = client.qm.execute(program)  # type: ignore[union-attr]

    LOG.info("Handling results.")
    handles = qm_job.result_handles
    measurement_data = {
        k: handles.get(k).fetch_all()  # type:ignore[union-attr]
        for k in handles.keys()  # noqa: SIM118
    }

    def _convert(array):
        return np.asarray(array).astype(float).tolist()

    raw_data = {k: _convert(v) for k, v in measurement_data.items()}
    client.export_experiment("raw_data", raw_data)

    raw_data_struct = Struct()
    raw_data_struct.update(raw_data)
    return agent_pb2.RunQuaProgramResponse(
        raw_data=raw_data_struct,
    )


async def _run_mixer_calibration(
    calibration_request: agent_pb2.RunQuantumMachinesMixerCalibrationRequest,
    client: QctrlScaleUpClient,
) -> agent_pb2.RunQuantumMachinesMixerCalibrationResponse:
    """
    Run a mixer calibration on the device.
    """
    LOG.info("Running mixer calibration task %s", calibration_request)

    LOG.info("Initializing QM.")
    client_qm = _initialize_qm(client, calibration_request.config)

    for element in calibration_request.elements:
        LOG.debug("Calibrating element %s", element)
        try:
            client_qm.calibrate_element(element)
        except CantCalibrateElementError as error:
            error_message = f"Failed to calibrate element {element}: {error}"
            print(error_message)  # noqa: T201
            return agent_pb2.RunQuantumMachinesMixerCalibrationResponse(
                success=False,
                error=error_message,
            )
        except AnotherJobIsRunning:
            error_message = (
                f"Failed to calibrate element {element}: another controller job is running."
            )
            print(error_message)  # noqa: T201
            return agent_pb2.RunQuantumMachinesMixerCalibrationResponse(
                success=False,
                error=error_message,
            )

    return agent_pb2.RunQuantumMachinesMixerCalibrationResponse(success=True)


async def _display_results(
    results: agent_pb2.DisplayResultsRequest,
) -> agent_pb2.DisplayResultsResponse:
    """
    Display results to the user.
    """

    LOG.info("Displaying results")

    if results.message is not None:
        print(results.message)  # noqa: T201

    if results.plots is not None:
        for plot in results.plots:
            Plotter(Plot.model_validate_json(plot)).figure.show()

    return agent_pb2.DisplayResultsResponse()
