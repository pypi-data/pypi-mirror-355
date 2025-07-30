import argparse
from typing import Callable
from functools import partial

from iclearn.cli import train, preview


def get_default_parser(dataloader_func=Callable, model_func=Callable):

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        type=int,
        default=0,
        help="Do a minimal dry run without changing any state.",
    )

    subparsers = parser.add_subparsers(required=True, help="Runtime mode")
    train_parser = train.add_parser(subparsers)

    session_func = partial(train.setup_session, dataloader_func, model_func)
    train_parser.set_defaults(func=partial(train.cli_func, session_func))

    preview_parser = preview.add_parser(subparsers)
    preview_parser.set_defaults(func=partial(preview.cli_func, dataloader_func))

    return parser
