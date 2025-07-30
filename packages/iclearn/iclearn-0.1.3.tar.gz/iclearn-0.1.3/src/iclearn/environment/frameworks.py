import logging

_TRIED_TORCH = False
_HAS_TORCH = False

logger = logging.getLogger(__name__)


def has_pytorch():

    global _TRIED_TORCH
    if not _TRIED_TORCH:
        _TRIED_TORCH = True
        global _HAS_TORCH
        try:
            import torch  # NOQA

            _HAS_TORCH = True
        except ImportError as e:
            logger.info("PyTorch not available. ImportError with message: %s", e)
            _HAS_TORCH = False
    return _HAS_TORCH
