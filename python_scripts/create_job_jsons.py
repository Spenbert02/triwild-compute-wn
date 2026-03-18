"""
TESTED LOCALLY
"""

import argparse
from pathlib import Path
from alive_progress import alive_bar
import json


OFFSET_TARGET_DIST = 1.0  # NOTE: should compute this for each mesh or something.


def create_jsons(input_dir):
    base_dir = Path(input_dir)
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("data_")]

    if not subdirs:
        print(f"No input .MSH files found in {input_dir}")
        return

    with alive_bar(len(subdirs)) as bar:
        for subdir in subdirs:
            i_str = subdir.name.split("_")[1]
            msh_name = f"{i_str}_tagged.msh"
            msh_path = subdir / msh_name

            if not msh_path.exists():
                raise Exception(f"mesh {msh_path} does not exist")

            # offset around object
            json1_config = {
                "application": "topological_offset",
                "input": msh_name,
                "output": f"{i_str}_singlebody_out",
                "offset_tags": [[0, 1]],
                "offset_tag_val": [[0, 2]],
                "target_distance": OFFSET_TARGET_DIST,
                "relative_ball_threshold": 0.01,
                "sorted_marching": False,
                "check_manifoldness": True,
                "save_vtu": False,
                "DEBUG_output": False
            }
            json1_subdir = subdir / "singlebody"
            json1_subdir.mkdir(parents=False, exist_ok=True)
            json1_path = json1_subdir / f"{i_str}_singlebody.json"
            with open(json1_path, "w") as f:
                json.dump(json1_config, f, indent=4)

            # offset around boundary
            json2_config = {
                "application": "topological_offset",
                "input": msh_name,
                "output": f"{i_str}_twobody_out",
                "offset_tags": [[0, 0], [0, 1]],
                "offset_tag_val": [[0, 2]],
                "target_distance": OFFSET_TARGET_DIST,
                "relative_ball_threshold": 0.01,
                "sorted_marching": False,
                "check_manifoldness": True,
                "save_vtu": False,
                "DEBUG_output": False
            }
            json2_subdir = subdir / "twobody"
            json2_subdir.mkdir(parents=False, exist_ok=True)
            json2_path = json2_subdir / f"{i_str}_twobody.json"
            with open(json2_path, "w") as f:
                json.dump(json2_config, f, indent=4)

            bar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create jsons for tagged mshes from triwild dataset")
    parser.add_argument("-m", "--meshesdir", required=True, help="Input .msh file directory (subdirs each with tagged (0/1) 2D triangle meshes)")
    args = parser.parse_args()
    create_jsons(args.meshesdir)