"""
Module to support creating and launching a training session from the CLI
"""

import os
import logging
from pathlib import Path
from typing import Callable
from functools import partial

from iccore.serialization import read_yaml

import iclearn.session
from iclearn.session import TrainConfig
from iclearn.environment import has_pytorch
from iclearn.utils.profiler import TimerProfiler, ProfilerCollection

from iclearn.output import LoggingOutputHandler, PlottingOutputHandler

logger = logging.getLogger(__name__)


def setup_profilers(config: TrainConfig):
    profilers = ProfilerCollection()
    profilers.add_profiler("timer", TimerProfiler(config.result_dir))
    if config.with_profiling:
        if config.model.framework == "pytorch" and has_pytorch():
            from iclearn.utils.torch.profiler import TorchProfiler

            profilers.add_profiler("torch", TorchProfiler(config.result_dir))
    return profilers


def load_environment(config: TrainConfig):
    if config.model.framework == "pytorch" and has_pytorch():
        from iclearn.environment.torch import environment

        return environment.load(
            config.node_id, config.num_nodes, config.num_gpus, config.local_rank
        )
    else:
        from iccore.system.environment import environment  # type: ignore

        return environment.load(config.local_rank)


def write_environment(env, config: TrainConfig):
    if config.model.framework == "pytorch" and has_pytorch():
        from iclearn.environment.torch import environment

        return environment.write(env, config.result_dir)
    else:
        from iccore.system.environment import environment  # type: ignore

        return environment.write(env, config.result_dir)


def setup_session(dataloader_func: Callable, model_func: Callable, config: TrainConfig):

    logger.info("Starting session in: %s", config.result_dir)
    iclearn.session.train_config.write_config(config, config.result_dir)

    logger.info("Setting up profilers")
    profilers = setup_profilers(config)
    profilers.start()

    logger.info("Loading environment")
    env = load_environment(config)
    write_environment(env, config)

    logger.info("Loading dataset from: %s", config.dataset_dir)
    dataloader = dataloader_func(config.dataloader, config.dataset_dir)
    dataloader.load(env)

    logger.info("Creating Model with %s classes", dataloader.num_classes)
    model_config = config.model.model_copy(
        update={"num_classes": dataloader.num_classes}
    )
    model = model_func(model_config)

    logger.info("Creating Session")
    session = iclearn.session.Session(model, env, config.result_dir, dataloader)
    session.output_handlers.extend(
        [
            LoggingOutputHandler(config.result_dir),
            PlottingOutputHandler(config.result_dir),
        ]
    )
    return profilers, session


def load_config(args, local_rank: int) -> TrainConfig:

    config_yaml = read_yaml(args.config.resolve())
    config = TrainConfig(**config_yaml)

    overrides = {
        "local_rank": local_rank,
        "dataset_dir": args.dataset_dir.resolve(),
        "result_dir": args.result_dir.resolve(),
    }

    if args.num_epochs >= 0:
        overrides["num_epochs"] = args.num_epochs
    if args.num_batches >= 0:
        overrides["num_batches"] = args.num_batches
    if args.node_id >= 0:
        overrides["node_id"] = args.node_id
    if args.num_nodes >= 0:
        overrides["num_nodes"] = args.num_nodes
    if args.num_gpus >= 0:
        overrides["num_gpus"] = args.num_gpus

    return config.model_copy(update=overrides)


def worker(session_func: Callable, local_rank: int, args):
    """
    This is the entry point on each parallel worker
    """

    logger.info(
        "Starting worker with rank: %s and result dir: %s",
        local_rank,
        args.result_dir.resolve(),
    )

    config = load_config(args, local_rank)
    profilers, session = session_func(config)
    if args.dry_run == 1:
        return

    logger.info("Starting training stage")
    session.train(config.num_epochs)
    logger.info("Finished training stage")

    if session.runtime_ctx.is_master_process():
        logger.info("Doing inference on test set")
        session.infer()

    profilers.stop()
    logger.info(
        "Finised worker task. Runtime = %.2f minutes",
        profilers.profilers["timer"].get_runtime() / 60,
    )


def cli_func(session_func: Callable, args):

    if args.num_gpus > 1:
        os.environ["MASTER_ADDR"] = "localhost"  # Address for master node
        os.environ["MASTER_PORT"] = "9956"  # Port for comms with master node

        if has_pytorch():
            import torch

            torch.multiprocessing.spawn(
                partial(worker, session_func), nprocs=args.num_gpus, args=(args,)
            )
        else:
            raise RuntimeError("Multigpu launch currently only supported with PyTorch")
    else:
        # Single GPU or CPU execution
        worker(session_func, 0, args)


def add_parser(parent):

    parser = parent.add_parser("train", help="Run in training mode")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path() / "config.yaml",
        help="Path to a config file for the session",
    )
    parser.add_argument(
        "--dataset_dir",
        type=Path,
        default=Path(),
        help="Path to the directory containing datasets",
    )
    parser.add_argument(
        "--result_dir",
        type=Path,
        default=Path() / "results",
        help="Path to results directory",
    )
    parser.add_argument(
        "--num_epochs", type=int, default=-1, help="Number of epochs for training"
    )
    parser.add_argument(
        "--num-nodes", type=int, default=-1, help="Number of nodes to run on"
    )
    parser.add_argument(
        "--node-id", type=int, default=-1, help="ID of the current node"
    )
    parser.add_argument(
        "--num-gpus", type=int, default=-1, help="Number of GPUs per node"
    )
    parser.add_argument(
        "--num_workers", type=int, default=-1, help="Number of dataloader workers"
    )
    parser.add_argument(
        "--num_batches",
        type=int,
        default=-1,
        help="Max number of batches for training. Mostly for troubleshooting.",
    )

    return parser
