import asyncio
import subprocess
from asyncio import Task
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Self, TypedDict, cast, overload

from ..logging.loggers import BaseLogger, SubConsoleLogger, get_console

ROLLING_AVERAGE_TIME = 300

_base_logger, console = get_console("HostMonitor")


class TaskChoice(StrEnum):
    """Enum for task choices."""

    CPU = "cpu"
    MEM = "mem"
    DISK = "disk"
    GPU = "gpu"


CPU = TaskChoice.CPU
MEM = TaskChoice.MEM
DISK = TaskChoice.DISK
GPU = TaskChoice.GPU

CPU_MEM: list[TaskChoice] = [CPU, MEM]
CPU_MEM_GPU: list[TaskChoice] = [CPU, MEM, GPU]
ALL_TASKS: list[TaskChoice] = [CPU, MEM, DISK, GPU]


def has_nvidia_gpu() -> bool:
    """Check if the system has an NVIDIA GPU."""
    try:
        result = subprocess.run(
            args=["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        console.error(f"Error checking for NVIDIA GPU: {e}", exc_info=True)
        return False


@dataclass(slots=True)
class GPUSamples:
    """GPU samples for monitoring."""

    gpu_usage: float = 0.0
    gpu_mem_usage: float = 0.0
    gpu_mem_total: float = 0.0
    gpu_mem_free: float = 0.0

    def __post_init__(self) -> None:
        if self.gpu_mem_total == 0:
            self.gpu_mem_total = self.gpu_mem_usage + self.gpu_mem_free

    @classmethod
    async def get_gpu_samples(cls) -> Self:
        """Get GPU samples using nvidia-smi."""
        try:
            result = subprocess.run(
                args=[
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,memory.free",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("nvidia-smi command failed")
            gpu_usage, gpu_mem_used, gpu_mem_total, gpu_mem_free = map(float, result.stdout.split(","))
            return cls(
                gpu_usage=gpu_usage,
                gpu_mem_usage=gpu_mem_used,
                gpu_mem_total=gpu_mem_total,
                gpu_mem_free=gpu_mem_free,
            )
        except Exception as e:
            console.error(f"Error getting GPU samples: {e}", exc_info=True)
            return cls()


@dataclass(slots=True)
class HostMonitorResult:
    # CPU
    cpu_usage_avg: float = 0.0
    cpu_max: float = 0.0
    cpu_min: float = 0.0

    mem_usage_avg: float = 0.0
    mem_max: float = 0.0
    mem_min: float = 0.0

    disk_usage_avg: float = 0.0

    gpu_usage_avg: float = 0.0
    gpu_usage_max: float = 0.0
    gpu_usage_min: float = 0.0

    gpu_mem_usage_avg: float = 0.0
    gpu_mem_usage_max: float = 0.0
    gpu_mem_usage_min: float = 0.0

    @property
    def empty(self) -> bool:
        """Check if the result is empty."""
        return not self.has_cpu_data and not self.has_mem_data and not self.has_disk_data and not self.has_gpu_data

    @property
    def has_cpu_data(self) -> bool:
        """Check if CPU data is available."""
        return self.cpu_usage_avg != 0.0 or self.cpu_max != 0.0 or self.cpu_min != 0.0

    @property
    def has_mem_data(self) -> bool:
        """Check if memory data is available."""
        return self.mem_usage_avg != 0.0 or self.mem_max != 0.0 or self.mem_min != 0.0

    @property
    def has_disk_data(self) -> bool:
        """Check if disk data is available."""
        return self.disk_usage_avg != 0.0

    @property
    def has_gpu_data(self) -> bool:
        """Check if GPU data is available."""
        return (
            self.gpu_usage_avg != 0.0
            or self.gpu_usage_max != 0.0
            or self.gpu_usage_min != 0.0
            or self.gpu_mem_usage_avg != 0.0
        )


class SampleStore(TypedDict):
    samples: deque[float | GPUSamples]
    getter: Callable[[], Awaitable[float | GPUSamples]]


class HostMonitor:
    def __init__(self, sample_interval: float = 1, tasks: list[TaskChoice] = [CPU, MEM]):
        self.console = console
        self.disk_path = "/"
        self.sample_stores: dict[TaskChoice, SampleStore] = {}
        self.tasks: list[TaskChoice] = tasks

        if self.is_task_enabled(GPU):
            if not has_nvidia_gpu():
                self.tasks.remove(TaskChoice.GPU)
                self.console.warning("No NVIDIA GPU detected, removing GPU task from monitoring.")

        self.sample_stores = {
            task: {
                "samples": deque(maxlen=int(ROLLING_AVERAGE_TIME // sample_interval)),
                "getter": getattr(self, f"get_{task.value}"),
            }
            for task in tasks
        }

        self.sampling_task: Task | None = None
        self.is_monitoring: bool = False
        self.sample_interval = sample_interval
        self.last_result = HostMonitorResult()

        self.console.verbose("HostMonitor initialized")

    def is_task_enabled(self, task: TaskChoice) -> bool:
        """Check if a specific task is enabled."""
        return task in self.tasks

    async def start(self) -> None:
        self.is_monitoring = True
        self.sampling_task = asyncio.create_task(self._collect_samples())

    async def stop(self) -> None:
        self.is_monitoring = False
        if self.sampling_task:
            self.sampling_task.cancel()
            try:
                await self.sampling_task
            except asyncio.CancelledError:
                pass
        self.sampling_task = None

    async def clear(self) -> None:
        for store in self.sample_stores.values():
            store["samples"].clear()

    @overload
    async def get(self, task: Literal[TaskChoice.CPU, TaskChoice.MEM, TaskChoice.DISK]) -> float: ...

    @overload
    async def get(self, task: Literal[TaskChoice.GPU]) -> GPUSamples: ...

    async def get(self, task: TaskChoice) -> float | GPUSamples:
        """Manually get a sample for the specified task."""
        getter_func = self.sample_stores[task]["getter"]
        if getter_func is None:
            self.console.error(f"Getter method for task {task} is None.")
            return 0.0
        result: float | GPUSamples | None = await getter_func()
        if result is not None:
            if isinstance(result, GPUSamples):
                return result
            return float(result)

    async def _collect_samples(self) -> None:
        await self.clear()
        while self.is_monitoring:
            await self._record_data()
            await asyncio.sleep(self.sample_interval)

    async def _record_data(self) -> None:
        for task in self.tasks:
            getter_func = self.sample_stores[task]["getter"]
            if getter_func is None:
                self.console.error(f"Getter method for task {task} is None.")
                continue
            result: float | GPUSamples | None = await getter_func()
            if result is not None:
                self.sample_stores[task]["samples"].append(result)

    @overload
    async def _get_samples(self, task: Literal[TaskChoice.CPU, TaskChoice.MEM, TaskChoice.DISK]) -> list[float]: ...

    @overload
    async def _get_samples(self, task: Literal[TaskChoice.GPU]) -> list[GPUSamples]: ...

    async def _get_samples(self, task: TaskChoice) -> list[float] | list[GPUSamples]:
        """Get collected samples for the specified task."""
        if not self.is_monitoring or not self.sample_stores.get(task):
            return [0.0]
        try:
            sample = list(self.sample_stores[task]["samples"])
            return cast(list[GPUSamples], sample) if task == GPU else cast(list[float], sample)
        except Exception as e:
            self.console.error(f"Error getting {task} samples: {e}", exc_info=True)
            return [0.0]

    async def get_sample(self, task: TaskChoice) -> float:
        """Get a single sample for the specified task."""
        if not self.is_monitoring or not self.sample_stores.get(task):
            return 0.0
        try:
            result: list[float] | list[GPUSamples] = await self._get_samples(task)
            if not result:
                return 0.0
            if task == GPU and isinstance(result[0], GPUSamples):
                first_result: GPUSamples = result[0]
                return first_result.gpu_usage if isinstance(first_result, GPUSamples) else 0.0
            else:
                return result[0] if isinstance(result[0], float) else 0.0
        except Exception as e:
            self.console.error(f"Error getting single {task} sample: {e}", exc_info=True)
        return 0.0

    @property
    def is_running(self) -> bool:
        """Check if the monitor is running."""
        return self.is_monitoring and self.sampling_task is not None and bool(self.sample_stores)

    async def get_current_samples(self) -> HostMonitorResult:
        result = HostMonitorResult()
        if not self.is_running:
            return result
        try:
            if self.is_task_enabled(CPU):
                cpu_samples: list[float] = await self._get_samples(TaskChoice.CPU)
                if cpu_samples:
                    result.cpu_usage_avg = round(sum(cpu_samples) / len(cpu_samples), 2)
                    result.cpu_max = max(cpu_samples)
                    result.cpu_min = min(cpu_samples)
            if self.is_task_enabled(MEM):
                mem_samples: list[float] = await self._get_samples(TaskChoice.MEM)
                if mem_samples:
                    result.mem_usage_avg = round(sum(mem_samples) / len(mem_samples), 2)
                    result.mem_max = max(mem_samples)
                    result.mem_min = min(mem_samples)
            if self.is_task_enabled(DISK):
                disk_samples: list[float] = await self._get_samples(TaskChoice.DISK)
                if disk_samples:
                    result.disk_usage_avg = round(sum(disk_samples) / len(disk_samples), 2)
            if self.is_task_enabled(GPU):
                gpu_samples: list[GPUSamples] = await self._get_samples(TaskChoice.GPU)
                if gpu_samples:
                    gpu_usage: list[float] = [sample.gpu_usage for sample in gpu_samples]
                    result.gpu_usage_avg = round(sum(gpu_usage) / len(gpu_usage), 2)
                    result.gpu_usage_max = max(gpu_usage)
                    result.gpu_usage_min = min(gpu_usage)
            self.last_result: HostMonitorResult = result
        except Exception as e:
            self.console.error(f"Error getting current samples: {e}", exc_info=True)
        return result

    async def get_avg_cpu_temp(self) -> float:
        if not self.is_monitoring or not self.sample_stores.get(CPU):
            return 0.0
        try:
            current_cpu_samples: list[float] = await self._get_samples(TaskChoice.CPU)
            if current_cpu_samples:
                average_cpu = round(sum(current_cpu_samples) / len(current_cpu_samples), 2)
                return average_cpu
        except Exception as e:
            print(f"Error getting CPU temperature: {e}")
        return 0.0

    async def get_avg_mem_usage(self) -> float:
        if not self.is_monitoring or not self.sample_stores.get(MEM):
            return 0.0
        try:
            current_mem_samples: list[float] = await self._get_samples(TaskChoice.MEM)
            if current_mem_samples:
                average_mem: float = round(sum(current_mem_samples) / len(current_mem_samples), 2)
                return average_mem
        except Exception as e:
            print(f"Error getting memory usage: {e}")
        return 0.0

    async def get_disk_usage(self) -> float:
        if not self.is_monitoring or not self.sample_stores.get(DISK):
            return 0.0
        try:
            current_disk_samples: list[float] = await self._get_samples(TaskChoice.DISK)
            if current_disk_samples:
                average_disk: float = round(sum(current_disk_samples) / len(current_disk_samples), 2)
                return average_disk
        except Exception as e:
            print(f"Error getting disk usage: {e}")
        return 0.0

    async def get_avg_gpu_usage(self) -> float:
        if not self.is_monitoring or not self.sample_stores.get(GPU):
            return 0.0
        try:
            current_gpu_samples: list[GPUSamples] = await self._get_samples(TaskChoice.GPU)
            if current_gpu_samples:
                average_gpu: float = round(
                    sum(sample.gpu_usage for sample in current_gpu_samples) / len(current_gpu_samples), 2
                )
                return average_gpu
        except Exception as e:
            print(f"Error getting GPU usage: {e}")
        return 0.0
