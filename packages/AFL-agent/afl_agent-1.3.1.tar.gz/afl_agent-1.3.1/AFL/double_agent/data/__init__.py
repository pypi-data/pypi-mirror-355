"""
Datasets module for AFL.double_agent.

This module provides access to example datasets that can be used with AFL.double_agent.
"""

import os
import pathlib
import warnings

import xarray as xr


# Get the path to the data directory
def get_data_dir() -> pathlib.Path:
    """
    Get the path to the data directory.

    Returns
    -------
    pathlib.Path
        Path to the data directory.
    """
    # The data directory is now located in AFL/double_agent/data
    module_dir = pathlib.Path(__file__).parent
    data_dir = module_dir

    if not data_dir.exists():
        warnings.warn(f"Data directory not found at {data_dir}")

    return data_dir


def list_datasets() -> list[str]:
    """
    List all available datasets.

    Returns
    -------
    list
        List of available dataset names.
    """
    data_dir = get_data_dir()
    if not data_dir.exists():
        warnings.warn(f"Data directory not found at {data_dir}")
        return []

    return [f.stem for f in data_dir.glob("*.nc")]


def load_dataset(name: str, lazy: bool=False) -> xr.Dataset:

    """
    Load a dataset by name.

    Parameters
    ----------
    name : str
        Name of the dataset to load.

    Returns
    -------
    xarray.Dataset
        The loaded dataset.

    Raises
    ------
    FileNotFoundError
        If the dataset does not exist.
    """
    data_dir = get_data_dir()
    file_path = data_dir / f"{name}.nc"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset '{name}' not found at {file_path}. "
            f"Data directory: {data_dir}. "
            f"Available datasets: {list_datasets()}"
        )
        
    if lazy:
        return xr.open_dataset(file_path)
    else:
        return xr.load_dataset(file_path)


# Define specific dataset loaders
def example_dataset1() -> xr.Dataset:
    """
    Load the example dataset.

    Returns
    -------
    xarray.Dataset
        The example dataset.
    """
    return load_dataset("example_dataset")

  
# Define specific dataset loaders
def example_dataset2():
    """
    Load the example dataset.
    
    Returns
    -------
    xarray.Dataset
        The example dataset.
    """
    return load_dataset("synthetic_sans")

# Add all datasets as module-level variables
__all__ = ["load_dataset", "list_datasets", "example_dataset1", "example_dataset2"] 