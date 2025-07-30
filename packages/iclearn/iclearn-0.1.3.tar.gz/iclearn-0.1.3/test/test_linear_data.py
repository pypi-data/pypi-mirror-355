import numpy as np
from pathlib import Path
import os
import shutil

from iccore.test_utils import get_test_output_dir

from iclearn.data.utils.linear_data import (
    get_mse,
    gradient_descent_iter,
    solve_analytical,
    get_rsquared,
    generate_basic,
    LinearData,
    generate,
)


# Test get_mse() function
def test_get_mse():
    y = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 4.0])

    mse = get_mse(y_pred, y)
    expected_mse = np.square(y - y_pred).mean()

    # Check if mse is close to expected_mse with tolerance 1e-8
    assert np.isclose(
        mse, expected_mse, atol=1e-8
    ), f"Expected {expected_mse}, but got {mse}"


# Test solve_analytical() function
def test_solve_analytical():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    w, b = solve_analytical(x, y)

    # Check if w is close to 2 and b to 0 with tolerance 1e-8
    assert np.isclose(w, 2.0, atol=1e-8), f"Expected w to be 2.0, but got {w}"
    assert np.isclose(b, 0.0, atol=1e-8), f"Expected b to be 0.0, but got {b}"


# Test gradient_descent_iter() function
def test_gradient_descent_iter():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    w, b = 0.0, 0.0
    lr = 0.1

    updated_w, updated_b, mse = gradient_descent_iter(w, b, x, y, lr)

    # Check if updated parameters is close to the initial ones
    assert not np.isclose(
        updated_w, w, atol=1e-8
    ), f"Expected w to be updated, but it stayed {updated_w}"
    assert not np.isclose(
        updated_b, b, atol=1e-8
    ), f"Expected b to be updated, but it stayed {updated_b}"
    # Check that mse is float
    assert isinstance(
        mse, float
    ), f"Expected mse to be of type 'float', but got {type(mse)}"


# Test get_rsquared() function
def test_get_rsquared():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    w, b = 2.0, 1.0

    rsquared = get_rsquared(w, b, x, y)

    # Check if rsquared is between 0 and 1
    assert (
        0 <= rsquared <= 1
    ), f"Expected rsquared to be between 0 and 1, but got {rsquared}"


# Test generate_basic() function
def test_generate_basic():
    w, b = 2.0, 1.0
    dim = 10
    x = np.linspace(0, 1, dim)

    y = generate_basic(w=w, b=b, dim=dim)
    expected_y = w * x + b

    # Checek output size
    assert len(y) == dim, f"Expected result length to be {dim}, but got {len(y)}"
    # Check if y is close to expected_y with tolerance 1e-8
    assert np.allclose(y, expected_y, atol=1e-8), f"Expected {expected_y}, but got {y}"


# Test LinearData class with split
def test_linear_data():

    # Test init()
    dim = 10
    data = LinearData(dim)

    # Check the length of the generated data and noise
    assert len(data.x) == dim - 1, f"Expected {dim - 1} x values, but got {len(data.x)}"
    assert len(data.y) == dim - 1, f"Expected {dim - 1} y values, but got {len(data.y)}"
    assert (
        len(data.noise) == dim - 1
    ), f"Expected noise of length {dim - 1}, but got {len(data.noise)}"

    # Test split()
    # Split the data into train, val and test
    training_bound = int(2 * len(data.x) / 3)
    val_bound = int((len(data.x) - training_bound) / 2)
    data.split(training_bound, val_bound)

    # Check the split data sizes
    assert (
        len(data.x_train) == training_bound
    ), f"Expected {training_bound} training samples, but got {len(data.x_train)}"
    assert (
        len(data.x_val) == val_bound
    ), f"Expected {val_bound} validation samples, but got {len(data.x_val)}"
    assert (
        len(data.x_test) == len(data.x) - training_bound - val_bound
    ), f"Expected {len(data.x) - training_bound - val_bound} test samples, but got {len(data.x_test)}"

    # Test save()
    work_dir = get_test_output_dir()
    save_dir = data.save(work_dir, full=True)

    # Check if the directories and files exist
    assert (
        save_dir / "train" / "train_data.csv"
    ).exists(), "Train data CSV was not saved"
    assert (
        save_dir / "val" / "val_data.csv"
    ).exists(), "Validation data CSV was not saved"
    assert (save_dir / "test" / "test_data.csv").exists(), "Test data CSV was not saved"
    assert (
        save_dir / "params" / "w_rand.csv"
    ).exists(), "Random weight CSV was not saved"
    assert (
        save_dir / "params" / "b_rand.csv"
    ).exists(), "Random bias CSV was not saved"
    assert (save_dir / "params" / "noise.csv").exists(), "Noise CSV was not saved"
    assert (
        save_dir / "complete" / "complete_dataset.csv"
    ).exists(), "Complete Dataset was not saved"

    # Test read()
    new_data = LinearData(dim)
    new_data.read(work_dir)

    # Compare the values with tolerance 1e-8
    assert np.allclose(
        new_data.x_train, data.x_train, atol=1e-8
    ), "Training x values do not match"
    assert np.allclose(
        new_data.y_train, data.y_train, atol=1e-8
    ), "Training y values do not match"
    assert np.allclose(
        new_data.x_val, data.x_val, atol=1e-8
    ), "Validation x values do not match"
    assert np.allclose(
        new_data.y_val, data.y_val, atol=1e-8
    ), "Validation y values do not match"
    assert np.allclose(
        new_data.x_test, data.x_test, atol=1e-8
    ), "Test x values do not match"
    assert np.allclose(
        new_data.y_test, data.y_test, atol=1e-8
    ), "Test y values do not match"
    assert np.allclose(
        new_data.w_rand, data.w_rand, atol=1e-8
    ), "Weight values do not match"
    assert np.allclose(
        new_data.b_rand, data.b_rand, atol=1e-8
    ), "Bias values do not match"
    assert np.allclose(
        new_data.noise, data.noise, atol=1e-8
    ), "Noise values do not match"

    # Test read() with no split
    dataset_dir = work_dir / "dataset"
    os.makedirs(dataset_dir, exist_ok=True)
    np.savetxt(
        dataset_dir / "dataset.csv",
        np.vstack((data.x, data.y)).T,
        delimiter=",",
        header="x,y",
    )

    new_data_nosplit = LinearData(dim)
    new_data_nosplit.read(work_dir, is_split=False)

    # Compare the values with tolerance 1e-8
    assert np.allclose(new_data_nosplit.x, data.x, atol=1e-8), "x values do not match"
    assert np.allclose(new_data_nosplit.y, data.y, atol=1e-8), "y values do not match"

    # Clean up after ourselves
    shutil.rmtree(work_dir)


# Test generate() function
def test_generate():
    dim = 10
    work_dir = get_test_output_dir()
    save_dir = generate(dim, work_dir)

    # Check if the directories and files exist
    assert (
        save_dir / "train" / "train_data.csv"
    ).exists(), "Train data CSV was not saved"
    assert (
        save_dir / "val" / "val_data.csv"
    ).exists(), "Validation data CSV was not saved"
    assert (save_dir / "test" / "test_data.csv").exists(), "Test data CSV was not saved"
    assert (
        save_dir / "params" / "w_rand.csv"
    ).exists(), "Random weight CSV was not saved"
    assert (
        save_dir / "params" / "b_rand.csv"
    ).exists(), "Random bias CSV was not saved"
    assert (save_dir / "params" / "noise.csv").exists(), "Random bias CSV was not saved"

    # Clean up after ourselves
    shutil.rmtree(work_dir)
