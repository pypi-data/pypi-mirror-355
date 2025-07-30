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

import json
import uuid
from collections.abc import KeysView, Mapping
from pathlib import Path

import numpy as np
from qm import QuantumMachine, QuantumMachinesManager, StreamingResultFetcher
from qm.jobs.running_qm_job import RunningQmJob
from qm.octave.octave_mixer_calibration import (
    AutoCalibrationParams,
    MixerCalibrationResults,
)
from qm.results.base_streaming_result_fetcher import BaseStreamingResultFetcher


def _deserialize_raw_data(data: str) -> dict[str, np.ndarray]:
    arrays = json.loads(data)
    return {key: np.array(value) for key, value in arrays.items()}


stub_data_queue: list[Path] = []


STUB_DATA_FILE_MAPPING: dict[str, list[str]] = {
    "resonator_spectroscopy": ["resonator_spectroscopy.json"],
    "resonator_spectroscopy_by_power": ["resonator_spectroscopy_by_power.json"],
    "resonator_spectroscopy_by_bias_1_bias": ["resonator_spectroscopy_by_bias_1_bias.json"],
    "resonator_spectroscopy_by_bias": ["resonator_spectroscopy_by_bias.json"],
    "ramsey": ["ramsey.json"],
    "power_rabi": ["power_rabi.json"],
}


class BaseStreamingResultFetcherStub(BaseStreamingResultFetcher):
    def __init__(self, key, stub_data, *_args, **_kwargs):
        self.key = key
        self._stub_data = stub_data

    def fetch_all(
        self,
        *_args,
        **_kwargs,
    ):
        return self._stub_data.get(self.key, None)

    def _validate_schema(self):
        pass


class StreamingResultFetcherStub(StreamingResultFetcher):
    def __init__(self, stub_data, *_args, **_kwargs):
        self._stub_data = stub_data
        self._all_results = {k: self.get(k) for k in self._stub_data}

    def keys(self) -> KeysView:
        return self._stub_data.keys()

    def is_processing(self):
        return False

    def wait_for_all_values(self, *_args, **_kwargs):
        return True

    def get(self, key: str, /, default=None) -> BaseStreamingResultFetcherStub:  # noqa: ARG002
        return BaseStreamingResultFetcherStub(key, self._stub_data)

    def items(self):
        return {k: self.get(k) for k in self._stub_data}.items()

    def __getattr__(self, item: str):
        if item in self._stub_data:
            return self.get(item)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{item}'",
        )


class RunningQmJobStub(RunningQmJob):
    def __init__(self, job_id, stub_data):
        self._id = job_id
        self._stub_data = stub_data

    @property
    def id(self) -> str:
        return self._id

    @property
    def result_handles(self) -> StreamingResultFetcherStub:
        return StreamingResultFetcherStub(self._stub_data)


class QuantumMachineStub(QuantumMachine):
    def __init__(self, qm_config, machine_id):
        self.qm_config = qm_config
        self._id = machine_id
        self.executions = []

    @property
    def id(self):
        return self._id

    def calibrate_element(
        self,
        qe: str,  # noqa: ARG002
        lo_if_dict: Mapping[float, tuple[float, ...]] | None = None,  # noqa: ARG002
        save_to_db: bool = True,  # noqa: ARG002
        params: AutoCalibrationParams | None = None,  # noqa: ARG002
    ) -> MixerCalibrationResults:
        return {}

    def execute(self, *_args, **_kwargs) -> RunningQmJobStub:
        job_id = str(uuid.uuid4())
        if stub_data_queue:
            file_path = stub_data_queue.pop(0)
            with file_path.open("rb") as f:
                stub_data = _deserialize_raw_data(f.read().decode("utf-8"))
        else:
            stub_data = {}

        running_job_stub = RunningQmJobStub(job_id, stub_data)
        self.executions.append(
            {"job": running_job_stub, "args": list(_args), "kwargs": _kwargs},
        )
        return running_job_stub

    def get_running_job(self):
        # Return None to indicate there's no running job.
        return None

    def close(self):
        return True


class QuantumMachinesManagerStub(QuantumMachinesManager):
    def __init__(
        self,
        qm_config,
        *_args,
        **_kwargs,
    ):
        self.qm_config = qm_config
        self.qm_id = str(uuid.uuid4())

    def open_qm(self, config, *_args, **_kwargs) -> QuantumMachineStub:
        return QuantumMachineStub(config, self.qm_id)

    def list_open_quantum_machines(self):
        return [self.qm_id]

    def load_experiment(self, experiment: str):
        stub_dir = Path(__file__).parent.parent.parent / "stub_data"
        file_paths = [stub_dir / file for file in STUB_DATA_FILE_MAPPING[experiment]]
        self.load_files(file_paths)

    def load_files(self, file_paths: list[Path]):
        _load_stub_data_files(file_paths)

    def load_file(self, file_path: Path):
        _load_stub_data_files([file_path])


def _load_stub_data_files(file_paths: list[Path]):
    stub_data_queue.clear()
    stub_data_queue.extend(file_paths)
