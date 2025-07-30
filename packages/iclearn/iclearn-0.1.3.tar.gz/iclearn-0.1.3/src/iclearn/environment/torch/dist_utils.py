"""
Utilities for running in a distributed setting with PyTorch
"""

import copy

from pydantic import BaseModel

import torch
import torch.distributed as dist


def sync_dict(input_dict: dict, device) -> dict:
    """
    Sync a dict across devices
    """

    dict_copy = copy.deepcopy(input_dict)
    dist.barrier()

    for outer_key, outer_value in dict_copy.items():
        for key, value in outer_value.items():
            value_tensor = torch.tensor(value, device=device)
            dist.all_reduce(value_tensor, op=dist.ReduceOp.AVG)  # type: ignore
            input_dict[outer_key][key] = value_tensor
    return input_dict


class TorchInfo(BaseModel, frozen=True):

    version: str
    dist_available: bool
    has_nccl: bool = False
    nccl_version: str = ""
    has_gloo: bool = False
    has_mpi: bool = False


def load_torch_info() -> TorchInfo:

    version = torch.__version__

    if not dist.is_available():
        return TorchInfo(version=version, dist_available=False)

    has_nccl = dist.is_nccl_available()
    if has_nccl:
        # Convert tuple to str
        nccl_version = ".".join(str(v) for v in torch.cuda.nccl.version())
    else:
        nccl_version = ""

    return TorchInfo(
        version=version,
        dist_available=True,
        has_nccl=has_nccl,
        nccl_version=nccl_version,
        has_gloo=dist.is_gloo_available(),
        has_mpi=dist.is_mpi_available(),
    )
