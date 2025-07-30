import json
from typing import Union

from esrf_pathlib import Path

from lima2mxh5master.api_dump_dict_to_nx import dump_dict_to_nx


def create_mx_master_h5(
    path_scan_run: Union[Path, str],
    name_h5master_file: str,
    path_schema: Union[Path, str] = "",
    predefined_schema: str = "lima2h5mx_default",
):
    """
    Create a NeXus master HDF5 file for a given MX scan run.

    This function validates the input paths, loads a JSON schema file (either user-provided or predefined),
    and generates the master HDF5 file by invoking `dump_dict_to_nx`. The default schema loads
    a custom class to compute necessary metadata define in :doc:`Custom Class <lima2mxh5master.custom>`.

    Parameters
    ----------
    path_scan_run : Union[Path, str]
        Path to the directory containing the MX scan run data.
        Must contain a valid `metadata.json` file.

    name_h5master_file : str
        Name of the output master HDF5 file to be created within the scan run directory.

    path_schema : Union[Path, str], optional
        Path to a JSON schema file describing the HDF5 structure.
        If not provided, the predefined schema will be used.

    predefined_schema : str, optional
        Name of a predefined schema JSON file located in the `h5_schema` directory.
        Defaults to `"lima2h5mx_default"`. Ignored if `path_schema` is provided.

    Example
    -------
    .. code-block:: python

        create_mx_master_h5(
            path_scan_run="/data/mx_scan_001",
            name_h5master_file="mx_master.h5",
            path_schema="custom_schema.json"
        )
    """

    # Inputs Validation

    if isinstance(path_scan_run, str):
        path_scan_run = Path(path_scan_run)

    if not path_scan_run.exists():
        raise FileNotFoundError(f"Scan Run directory not found: {path_scan_run}")

    path_metadata_json = path_scan_run / "metadata.json"
    if not path_metadata_json.exists():
        raise FileNotFoundError(f"metadata.json not found: {path_metadata_json}")

    if str(path_schema):
        if isinstance(path_schema, str):
            path_schema = Path(path_scan_run)

        if not path_schema.exists():
            raise FileNotFoundError(f"Schema File not found: {path_schema}")

    elif predefined_schema:
        base_dir = Path(__file__).resolve().parent
        path_schema = base_dir / "h5_schema" / predefined_schema

        if path_schema.suffix != "json":
            path_schema = path_schema.with_suffix(".json")

        if not path_schema.exists():
            raise FileNotFoundError(f"Predefined Schema File not found: {path_schema}")

    path_h5_master_file = path_scan_run / name_h5master_file

    # Openning Schema

    try:
        with open(path_schema, "r") as f:
            dict_h5 = json.load(f)

    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON from {path_schema}: {e}")
    except Exception as e:
        raise IOError(f"Error reading metadata file {path_schema}: {e}")

    dump_dict_to_nx(dict_h5, path_h5_master_file, filepath_metadata=path_metadata_json)
