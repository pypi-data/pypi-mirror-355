"""
Info on the CUDA environment given by the PyTorch
CUDA API
"""

from pydantic import BaseModel

import torch


class CudaDevice(BaseModel, frozen=True):

    name: str
    properties: str = ""
    memory_use: int = 0
    processor_use: int = 0


class CudaInfo(BaseModel, frozen=True):

    available: bool
    devices: list[CudaDevice] = []
    arch_list: str = ""


def load_cuda_device(index: int) -> CudaDevice:
    """
    Get info on a single CUDA device

    :param index: The device index
    """
    return CudaDevice(
        name=torch.cuda.get_device_name(index),
        properties=str(torch.cuda.get_device_properties(index)),
        memory_use=torch.cuda.memory_usage(index),
        processor_use=torch.cuda.utilization(index),
    )


def load_cuda_info() -> CudaInfo:
    """
    Get info on the CUDA environment
    """

    return CudaInfo(
        available=torch.cuda.is_available(),
        arch_list=str(torch.cuda.get_arch_list()),
        devices=[load_cuda_device(idx) for idx in range(torch.cuda.device_count())],
    )
