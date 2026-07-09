from pathlib import Path
import json
import re

msh_dir_path = Path("/scratch/seb9449/offsets_testing_triwild/tagged_mshs_under_10mb/")
logs_dir_path = Path(f"/scratch/seb9449/offsets_testing_triwild/triwild-compute-wn/bash_scripts_hpc/wmtk_triwild_array/logs")

def get_most_recent_log(model_id):
    ret_id = 0
    if not (logs_dir_path / f"model_{model_id}_(0).out").exists():
        return None
    else:
        while (logs_dir_path / f"model_{model_id}_({ret_id + 1}).out").exists():
            ret_id += 1
        return ret_id

def main():
    ids = {}
    ids["success"] = []
    ids["other"] = []
    ids["not_run"] = []
    ids["critical_log"] = []
    ids["bad_energy"] = []
    ids["timeout"] = []
    ids["orientation"] = []

    count = 0
    print(f"progress: {count}\t", end="")
    for model_dir in msh_dir_path.glob("data_*"):
        count += 1
        if count % 100 == 0:
            print(f"\rprogress: {count}\t", end="", flush=True)

        if not model_dir.is_dir():
            continue

        try:
            model_id = int(model_dir.name.split('_')[1])
        except ValueError:
            print(f"\nWARNING: non-int model id at {str(model_dir)}")
            continue
    
        # if log doesn't exist, wasn't run
        log_id = get_most_recent_log(model_id)
        if log_id is None:
            ids["not_run"].append(model_id)
            continue

        # if output .msh exists, success
        out_msh_path = model_dir / f"wmtk_triwild" / f"model_{model_id}_out.msh"
        out_report_path = model_dir / f"wmtk_triwild" / f"model_{model_id}_report.json"
        if out_msh_path.exists() and out_report_path.exists():
            report = None
            with open(out_report_path, "r") as f:
                report = json.load(f)
            if report["max_energy"] < 10:
                ids["success"].append(model_id)
            else:
                ids["bad_energy"].append(model_id)
            continue

        # check log err file to see what happened
        err_path = logs_dir_path / f"model_{model_id}_({log_id}).err"
        with open(err_path, "r") as err_f:
            found = False
            for line in err_f.readlines():
                if "CRITICAL: Accessing uninitialized Logger instance" in line:
                    ids["critical_log"].append(model_id)
                    found = True
                    break
                if "DUE TO TIME LIMIT" in line:
                    ids["timeout"].append(model_id)
                    found = True
                    break
                if "Tets with different orientations in the input!" in line:
                    ids["orientation"].append(model_id)
                    found = True
                    break
            if found:
                continue
        
        # not sure. more detection needed
        ids["other"].append(model_id)
    
    # print output
    print()
    print(f"======= WMTK Triwild Results ========")
    for key, lst in ids.items():
        if key == "other":
            continue
        print(key, ":", len(lst))
        # if key in ["OOM", "timeout", "bad_energy"]:
        #     for id in ids[key]:
        #         print(f"\t{id},")
    print("other", ":", len(ids["other"]))
    print("\t", end="")
    for i, id in enumerate(ids["other"]):
        if i > 10:
            break
        print(f" {id},", end="")
    print()


if __name__ == "__main__":
    main()
