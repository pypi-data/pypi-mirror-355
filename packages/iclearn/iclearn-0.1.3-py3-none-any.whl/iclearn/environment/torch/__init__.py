from .environment import *  # NOQA

import torch


def as_tensors(cls) -> None:
    """Converts all datasets in the class instance.
    Changes numpy arrays into tensors.
    """
    for obj in vars(cls):
        setattr(cls, obj, torch.Tensor(getattr(cls, obj)))
        setattr(cls, obj, getattr(cls, obj).to(torch.float32))
