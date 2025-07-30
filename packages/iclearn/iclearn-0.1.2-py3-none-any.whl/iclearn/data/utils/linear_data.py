from pathlib import Path
import os

import numpy as np


def get_mse(y_pred, y):
    """
    A basic MSE implementation, useful for testing things out
    """

    return np.square(y - y_pred).mean()


def gradient_descent_iter(w, b, x, y, lr):

    f = y - (w * x + b)
    w -= lr * (-2.0 * x * f).mean()  # partial derivative dmse_dw
    b -= lr * (-2.0 * f).mean()  # partial derivative dmse_db
    mse = get_mse(y, w * x + b)
    return w, b, mse


def solve_analytical(x, y):

    x = np.column_stack([np.ones(len(x)), x])  # column of to represent b
    x_t = np.transpose(x)
    theta = np.linalg.inv(x_t @ x) @ x_t @ y

    return theta[1], theta[0]


def get_rsquared(w, b, x, y):
    y_pred = w * x + b
    ss_res = np.sum((y_pred - y) ** 2)
    ss_tot = np.sum((y - np.average(y)) ** 2)
    return 1.0 - ss_res / ss_tot


def gradient_descent(x, y, lr=0.2, num_epoch=50):

    w = 0.0
    b = 0.0
    for idx in range(num_epoch):
        w, b, mse = gradient_descent_iter(w, b, x, y, lr)
        print(f"gradient descent: epoch {idx}, w {w:0.3f}, b {w:0.3f}, mse {mse:0.5f}")


def generate_basic(w: float = 0.5, b: float = 0.5, dim: int = 10):
    x = np.linspace(0, 1, dim)
    return w * x + b


def gradient_descent_batch(x, y, lr=0.1, num_epochs=10, batch_size=10):

    w = 0.0
    b = 0.0

    num_batches = (len(x) + batch_size - 1) // batch_size

    for idx in range(num_epochs):
        for batch_idx in range(num_batches):
            start_idx, end_idx = batch_idx * batch_size, min(
                (batch_idx + 1) * batch_size, len(x)
            )
            batch_x, batch_y = x[start_idx:end_idx], y[start_idx:end_idx]
            w, b, mse = gradient_descent_iter(w, b, batch_x, batch_y, lr)

    return w, b


class LinearData:
    """
    A 2D dataset representing a line with random slope and offset
    and some noise.
    """

    def __init__(self, dim: int) -> None:
        """
        The noise is created using a normal distribution with mean 0 and s.d 1.
        The slope and intercept are generated from absolute values from a uniform
        distribution scaled by x2.
        The x values are generated uniformly over the interval [0, 10).
        The y values are generated from the above using a linear formula.
        """
        self.noise = np.random.normal(size=dim - 1)
        self.w_rand, self.b_rand = abs(np.random.normal(size=(2, 1))) * 2
        self.x = np.random.uniform(size=dim - 1) * 10
        self.y = (self.w_rand * (self.x + self.noise)) + self.b_rand

    def split(self, training_bound: int, val_bound: int) -> None:
        """Creates a dataset with training, testing, and validation splits.
        A user defined bounds splits the data.

        :param training_bound: Determines the length of the training subset.
        :type training_bound: int

        :param val_bound: Determines the length of the validation subset.
        :type val_bound: int
        """
        self.x_train = self.x[0:training_bound]
        self.y_train = self.y[0:training_bound]
        self.x_val = self.x[training_bound : training_bound + val_bound]
        self.y_val = self.y[training_bound : training_bound + val_bound]
        self.x_test = self.x[training_bound + val_bound : len(self.x)]
        self.y_test = self.y[training_bound + val_bound : len(self.y)]

    def save(self, dataset_dir: Path, params: bool = True, full: bool = False) -> Path:
        """Saves the dataset to a .csv file in the working path.
        Creates subfolders for the model parameters and the split datasets.
        Optionally allows for the entire dataset to be saved without splitting.

        :param dataset_dir: The path to the directory where the data will be saved.
        :type dataset_dir: Path

        :param full: User decides if the full dataset subfolder and file should be
        created.
        :type full: bool, optional

        :param params: Bool to check if the parameters for the data set can be saved.
            In the case where the data is read from a pre-existing csv these will not
            be known.
        :type params: bool, optional

        :return dataset_dir: Path to "data" parent directory that contains split
        subfolders.
        :rtype Path
        """

        data = [
            ("train", self.x_train, self.y_train),
            ("val", self.x_val, self.y_val),
            ("test", self.x_test, self.y_test),
        ]
        for label, x, y in data:
            working_path = dataset_dir / label
            os.makedirs(working_path, exist_ok=True)
            np.savetxt(
                working_path / f"{label}_data.csv",
                np.vstack((x, y)).T,
                header=("x, y"),
                delimiter=",",
            )

        if params:
            working_path = dataset_dir / "params"
            os.makedirs(working_path, exist_ok=True)
            pdata = [
                ("noise", self.noise),
                ("w_rand", self.w_rand),
                ("b_rand", self.b_rand),
            ]
            for label, x in pdata:  # type: ignore
                np.savetxt(
                    working_path / f"{label}.csv", x, header=label, delimiter=","
                )

        if full:
            working_path = dataset_dir / "complete"
            os.makedirs(working_path, exist_ok=True)
            np.savetxt(
                working_path / "complete_dataset.csv",
                np.vstack((self.x, self.y)).T,
                header=("x, y"),
                delimiter=",",
            )

        return dataset_dir

    def read(self, dataset_dir: Path, is_split=True) -> None:
        """Reads the dataset from saved local files.
        Follows the same structure as saved files: distinct folders for the parameters,
        test, training, and validation data.

        :param dataset_dir: The path to the directory containing the data.
        :type dataset_dir: Path
        """
        if not is_split:
            working_dir = dataset_dir / "dataset"
            self.x, self.y = np.genfromtxt(
                working_dir / "dataset.csv",
                delimiter=",",
                skip_header=0,
                unpack=True,
                dtype=float,
            )

        else:
            # params
            working_dir = dataset_dir / "params"
            self.w_rand = np.genfromtxt(  # type: ignore
                working_dir / "w_rand.csv", delimiter=",", skip_header=0
            )
            self.b_rand = np.genfromtxt(  # type: ignore
                working_dir / "b_rand.csv", delimiter=",", skip_header=0
            )
            self.noise = np.genfromtxt(
                working_dir / "noise.csv", delimiter=",", skip_header=0
            )

            # train
            working_dir = dataset_dir / "train"
            self.x_train, self.y_train = np.genfromtxt(
                working_dir / "train_data.csv",
                delimiter=",",
                skip_header=0,
                unpack=True,
                dtype=float,
            )

            # val
            working_dir = dataset_dir / "val"
            self.x_val, self.y_val = np.genfromtxt(
                working_dir / "val_data.csv",
                delimiter=",",
                skip_header=0,
                unpack=True,
                dtype=float,
            )

            # test
            working_dir = dataset_dir / "test"
            self.x_test, self.y_test = np.genfromtxt(
                working_dir / "test_data.csv",
                delimiter=",",
                skip_header=0,
                unpack=True,
                dtype=float,
            )


def generate(dim: int, work_dir: Path) -> Path:
    """A simple function to initialise and generate a LinearData class of points
        of size dim.

    Splits the data into 2/3 training, 1/6 validation, and 1/6 test.

    It saves the split data into the csv format specified in the
        LinearData class' save function.

    :param dim: Defines the dimension/length of the (x, y) data array.
    :type dim: int
    """
    data = LinearData(dim)
    train_bound = (2 * len(data.x)) // 3
    val_bound = (len(data.x) - train_bound) // 2
    data.split(train_bound, val_bound)
    return data.save(work_dir)
