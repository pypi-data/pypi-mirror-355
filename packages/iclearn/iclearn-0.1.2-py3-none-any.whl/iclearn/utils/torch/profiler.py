from pathlib import Path

from torch.profiler import profile, ProfilerActivity

from iclearn.utils.profiler import Profiler


class TorchProfiler(Profiler):
    def __init__(self, result_dir: Path):
        super().__init__(result_dir)

        self.torch_profiler = profile(
            activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
            profile_memory=True,
            record_shapes=True,
        )

    def start(self):
        self.torch_profiler.start()

    def stop(self):
        self.torch_profiler.stop()
