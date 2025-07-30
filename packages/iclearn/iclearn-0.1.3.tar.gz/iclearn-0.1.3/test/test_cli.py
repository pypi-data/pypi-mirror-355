import sys
from iclearn.cli import get_default_parser
from pathlib import Path


# Test for preview mode CLI
def test_preview_cli():
    # Simulate command line args
    sys.argv = [
        "script.py",
        "preview",
        "--dataset_dir",
        "dataset",
        "--result_dir",
        "results",
    ]

    # Get the default parser and parse the args
    parser = get_default_parser(dataloader_func=None)
    args = parser.parse_args()

    # Assertions to check if arguments were parsed correctly
    assert args.dataset_dir == Path("dataset")
    assert args.result_dir == Path("results")


# Test for training mode CLI
def test_train_cli():
    # Simulate command line args
    sys.argv = [
        "script.py",
        "train",
        "--num_epochs",
        "1",
        "--dataset_dir",
        "dataset",
        "--result_dir",
        "results",
    ]

    # Get the default parser and parse the args
    parser = get_default_parser(dataloader_func=None, model_func=None)
    args = parser.parse_args()

    # Assertions to check if arguments were parsed correctly
    assert args.num_epochs == 1
    assert args.dataset_dir == Path("dataset")
    assert args.result_dir == Path("results")
