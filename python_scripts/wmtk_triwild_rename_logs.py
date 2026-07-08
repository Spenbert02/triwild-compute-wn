from pathlib import Path
import re

REMESHING_TEST_NUM = 6

logs_dir = f"/scratch/seb9449/offsets_testing_triwild/triwild-compute-wn/bash_scripts_hpc/wmtk_triwild_array/logs"

def parse_job_stem(stem):
    job_re = re.compile(r"^job_(\d+)_(\d+)$")
    m = job_re.match(stem)
    if not m:
        return None
    else:
        return int(m.group(1)), int(m.group(2))

def parse_filename(s):
    pattern = r"^model_(\d+)_\((\d+)\)$"
    match = re.match(pattern, s)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def get_model_id_from_log(path):
    with open(str(path), "r") as f:
        for i, line in enumerate(f):
            if i == 2:
                return int(line.split(" ")[2].split(".")[0].split("_")[-1])

if __name__ == "__main__":
    logs_dir_path = Path(logs_dir)

    # scan, collect existing file nums
    existing_nums = {}
    for p in logs_dir_path.iterdir():
        if not (p.is_file() and p.suffix.lower() == ".out"):
            continue
        parse_res = parse_filename(p.stem)
        if parse_res:
            model_id, num = parse_res[0], parse_res[1]
            if model_id in existing_nums:
                existing_nums[model_id].append(num)
            else:
                existing_nums[model_id] = [num]
    
    num_tracker = {} # holds max existing num for each model
    for model_id, nums in existing_nums.items():
        num_tracker[model_id] = max(nums)

    job_outs = []
    for p in logs_dir_path.iterdir():
        if not (p.is_file() and p.suffix.lower() == ".out"):
            continue
        ij = parse_job_stem(p.stem)
        if ij is None:
            continue
        job_outs.append((ij[0], ij[1], p))
    
    # scan, actually renaming .out files
    for _, _, p in sorted(job_outs):
        model_id = get_model_id_from_log(p)
        new_num = None
        if model_id in num_tracker:
            new_num = num_tracker[model_id] + 1
        else:
            new_num = 0
        num_tracker[model_id] = new_num

        new_out_path = logs_dir_path / f"model_{model_id}_({new_num}).out"
        p.rename(new_out_path)
        old_err_path = p.with_suffix(".err")
        new_err_path = new_out_path.with_suffix(".err")
        old_err_path.rename(new_err_path)
