from pathlib import Path

from pydantic import BaseModel


class Split(BaseModel, frozen=True):
    """
    Attributes for an element of a dataset, e.g. the training split

    :cvar str name: Name of the split, e.g. 'train'
    :cvar Path path: Path of the split relative to the split collection root
    :cvar bool shuffle: If True shuffle the data when loading it
    :cvar bool use_sampler: If True and supported use a distributed data sampler
    :cvar float fraction: Fraction of total dataset for this split
    :cvar list[str] files: Explicit list of adopted files
    """

    name: str
    path: Path | None = None
    shuffle: bool = False
    use_sampler: bool = False
    fraction: float = 0.0
    files: list[str] = []


class Splits(BaseModel, frozen=True):
    """
    Description of how the dataset is split into subsets, e.g. test, train, val

    :cvar list[Split]: the actual splits
    :cvar bool use_fractions: whether to use split fraction attributes when loading data
    :cvar Path path: Optional root to search for splits in,
    can be different to dataset root
    """

    items: list[Split] = []
    use_fractions: bool = False
    path: Path | None = None

    def get_item(self, name: str):
        for item in self.items:
            if item.name == name:
                return item
        raise RuntimeError("Requested non existing split")


def get_default_splits() -> Splits:
    """
    Return basic/sensible defaults for split values. They assume a directory
    structure with the splits under 'train', 'val', 'test' subdirectories.
    """

    return Splits(
        items=[
            Split(name="train", path=Path("train"), shuffle=True),
            Split(name="val", path=Path("val"), shuffle=True),
            Split(name="test", path=Path("test"), shuffle=False),
        ]
    )


def get_fractional_splits(train: float, val: float):
    return Splits(
        items=[
            Split(name="train", fraction=train, shuffle=True),
            Split(name="val", fraction=val, shuffle=True),
            Split(name="test", fraction=(1.0 - train - val), shuffle=False),
        ]
    )
