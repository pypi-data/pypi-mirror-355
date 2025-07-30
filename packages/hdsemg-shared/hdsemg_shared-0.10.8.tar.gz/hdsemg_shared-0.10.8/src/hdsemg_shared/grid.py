import logging
import os
import json
import time

import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

import re
import requests
import uuid

from .fileio.file_io import load_file

grid_data = None


def grid_json_setup():
    """
    Initialize the global grid_data variable by loading data from a JSON file.
    """
    global grid_data
    url = "https://drive.google.com/uc?export=download&id=1FqR6-ZlT1U74PluFEjCSeIS7NXJQUT-v"
    grid_data = load_grid_data(url)


def load_grid_data(url):
    """
    Load grid data from a JSON file on the internet or from a local cache.

    Args:
        url (str): URL to the JSON file containing grid data.

    Returns:
        list: A list of grid data from the file.
    """
    cache_dir = os.path.join(os.path.expanduser("~"), ".hdsemg_cache")
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists
    cache_file = os.path.join(cache_dir, "grid_data_cache.json")
    one_week_seconds = 7 * 24 * 60 * 60

    # Check if the cache file exists and is not older than 1 week
    if os.path.exists(cache_file):
        try:
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < one_week_seconds:
                with open(cache_file, 'r') as f:
                    return json.load(f)  # Load grid data from the cache file
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read cache file {cache_file}: {e}")

    # If cache file doesn't exist, is invalid, or is older than 1 week, fetch from URL
    try:
        response = requests.get(url, timeout=10)  # Set timeout to 10s
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        grid_data = response.json()  # Convert response to JSON

        # Save the fetched data to the cache file
        try:
            with open(cache_file, 'w') as f:
                json.dump(grid_data, f)
                logger.info(f"Grid data cached to {cache_file}")
        except IOError as e:
            logger.error(f"Failed to write cache file {cache_file}: {e}")

        return grid_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to load grid data from {url}: {e}")
        return []


def get_electrodes_from_grid_name(grid_name):
    """
    Search for the number of electrodes based on the grid name in the global grid data.

    Args:
        grid_name (str): The name of the grid.

    Returns:
        int: Number of electrodes if the grid is found; None otherwise.
    """
    global grid_data
    if grid_data is None:
        grid_json_setup()

    for grid in grid_data:
        if grid_name.upper() == grid["product"].upper():
            return grid["electrodes"]
    return None


def extract_grid_info(description):
    """
    Extract grid dimensions, indices, and reference signals from the description.
    Only assigns reference signals to the grid they immediately follow.

    Args:
        description (list): A list of descriptions containing grid information.

    Returns:
        dict: A dictionary containing detailed grid information.
    """
    global grid_data
    if grid_data is None:
        grid_json_setup()

    grid_info = {}
    current_grid_key = None

    # Pattern to match grid descriptions (e.g., HDxxMMxx)
    pattern = re.compile(r"HD(\d{2})MM(\d{2})(\d{2})")

    for idx, entry in enumerate(description):
        match = pattern.search(handle_entry(entry))
        if match:
            # Extract grid details
            scale_mm = int(match.group(1))
            rows = int(match.group(2))
            cols = int(match.group(3))
            grid_key = f"{rows}x{cols}"

            # Initialize grid entry if not already present
            if grid_key not in grid_info:
                # Search for electrodes in the grid data
                electrodes = get_electrodes_from_grid_name(match.group(0))
                if electrodes is None:
                    electrodes = rows * cols

                grid_info[grid_key] = {
                    "rows": rows,
                    "cols": cols,
                    "indices": [],
                    "ied_mm": scale_mm,
                    "electrodes": electrodes,
                    "reference_signals": [],
                    "requested_path_idx": None,
                    "performed_path_idx": None
                }
            grid_info[grid_key]["indices"].append(idx)
            # Update current grid key
            current_grid_key = grid_key
        else:
            if "requested path" in entry[0][0]:
                grid_info[current_grid_key]["requested_path_idx"] = idx
            if "performed path" in entry[0][0]:
                grid_info[current_grid_key]["performed_path_idx"] = idx

            if current_grid_key:
                grid_info[current_grid_key]["reference_signals"].append({"index": idx, "name": entry[0][0]})

    return grid_info


def load_single_grid_file(file_path):
    """
    Load and process a single .mat file to extract grid information.

    Args:
        file_path (str): Path to the .mat file.

    Returns:
        list: A list of dictionaries, each representing a grid from the file.

    Raises:
        Exception: If any error occurs during loading or processing.
    """
    data, time, description, sf, fn, fs = load_file(file_path)
    grid_info = extract_grid_info(description)

    grids = []
    for grid_key, gi in grid_info.items():
        grid_data = {
            'file_path': file_path,
            'file_name': fn,
            'data': data,
            'time': time,
            'description': description,
            'sf': sf,
            'emg_indices': gi['indices'],
            'ref_indices': [ref['index'] for ref in gi['reference_signals']],
            'rows': gi['rows'],
            'cols': gi['cols'],
            'ied_mm': gi['ied_mm'],
            'electrodes': gi['electrodes'],
            'grid_key': grid_key,
            'grid_uid': str(uuid.uuid4())
        }
        grids.append(grid_data)
    return grids


def handle_entry(entry):
    """
    Since entry can either be a array or a string, this function handles both cases and returns the entry as a string.
    Args:
        entry: input data from desc array

    Returns: str of the entry

    """
    if isinstance(entry, str):
        return entry
    elif isinstance(entry, np.ndarray):
        try:
            return str(entry[0][0])
        except IndexError:
            raise ValueError("Entry is an empty numpy array or does not contain expected data.")
    else:
        raise ValueError(f"Unsupported entry type: {type(entry)}. Expected str or np.ndarray containing str.")
