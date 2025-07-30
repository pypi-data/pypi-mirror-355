from typing import Any

from iclearn.environment import has_pytorch

from .machine_learning_model import Optimizer


def load_optimizer(params: Any, opt: Optimizer):

    if has_pytorch():
        from .torch import load_optimizer as load_torch_optimizer

        return load_torch_optimizer(params, opt)

    return None
