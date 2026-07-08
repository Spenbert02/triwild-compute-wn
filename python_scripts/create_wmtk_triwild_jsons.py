from pathlib import Path
import json

msh_dir_path = Path("/scratch/seb9449/offsets_testing_triwild/tagged_mshs_under_10mb")
data_dir_path = Path("/scratch/seb9449/out_fix")

def main():
    if not msh_dir_path.exists():
        raise FileNotFoundError(str(msh_dir_path))

    count = 0
    for subdir in msh_dir_path.glob("data_*"):
        if subdir.exists() and subdir.is_dir():
            try:
                model_id = int(subdir.name.split("_")[1])
            except:
                print(f"WARNING: non int dir name: {subdir.name}")
                continue

            obj_path = data_dir_path / f"{model_id}.obj"
            if not obj_path.exists():
                print(f"ERROR: obj for model {model_id} does not exist. Skipping")
                continue

            output_dir = subdir / "wmtk_triwild"
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"wmtk_triwild_{model_id}.json"
            json_data = {
                "application": "triwild",
                "input": [str(obj_path)],
                "output": str(subdir / f"model_{model_id}_out"),
                "num_threads": 0,
                "DEBUG_output": False,
                "throw_on_fail": True,
                "stop_energy": 10
            }
            with open(json_path, "w") as f:
                json.dump(json_data, f, indent=4)

            count += 1
    print(f"Created {count} jsons.")


if __name__ == "__main__":
    main()
