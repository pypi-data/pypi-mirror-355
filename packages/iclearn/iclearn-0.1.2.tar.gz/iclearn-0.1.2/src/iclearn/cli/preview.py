"""
Handle CLI arguments for the preview function
"""

from pathlib import Path
import logging
from typing import Callable

from iccore.data import Dataset
from iclearn.data import DataloaderCreate


logger = logging.getLogger(__name__)


def cli_func(dataloader_func: Callable, args):

    config = DataloaderCreate(dataset=Dataset())

    logger.info("Previewing dataset at: %s", args.dataset_dir.resolve())
    _ = dataloader_func(config, args.dataset_dir.resolve())

    logger.info("Doing dataset preview")


def add_parser(parent):

    parser = parent.add_parser("preview", help="Run in preview mode")
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
    return parser
