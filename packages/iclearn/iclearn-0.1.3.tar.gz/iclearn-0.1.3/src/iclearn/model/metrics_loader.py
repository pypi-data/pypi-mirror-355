from iclearn.environment import has_pytorch

from .model import Metrics


def load_metrics(loss_func, metric_names: list[str], num_classes: int = 0):

    metrics = Metrics(loss_func=loss_func, num_classes=num_classes)

    if has_pytorch():
        from .torch.metrics import load_metrics_funcs

        metrics.metric_funcs |= load_metrics_funcs(metric_names, num_classes)

    return metrics
