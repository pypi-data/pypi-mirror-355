import json

from esrf_pathlib import Path

from lima2mxh5master import create_mx_master_h5
from lima2mxh5master import dumpdicttonx

if __name__ == "__main__":

    # Default usage for MX Master H5 creation

    path_scan = Path(
        "/home/broche/DataTest/visitor/mx2112/id23eh1/19880930/run_02_04_datacollection"
    )
    create_mx_master_h5(path_scan_run=path_scan, name_h5master_file="master.h5")

    # Custom nx schema usage

    path_schema = "./src/lima2mxh5master/h5_schema/lima2h5mx_default.json"
    path_h5_master_file = path_scan / "master_custom.h5"
    path_metadata_json = path_scan / "metadata.json"

    with open(path_schema, "r") as f:
        dict_h5 = json.load(f)

    dumpdicttonx(dict_h5, path_h5_master_file, filepath_metadata=path_metadata_json)
