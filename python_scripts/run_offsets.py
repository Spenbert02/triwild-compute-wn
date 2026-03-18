"""
NOT TESTED
"""

import argparse
import subprocess
import os
from pathlib import Path
import concurrent.futures
import time


def run_single_json(wmtk_app_exe, json_path):
    start_time = time.time()
    command = [wmtk_app_exe, "-j", str(json_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    duration = time.time() - start_time
    return json_path, result.returncode, result.stderr, duration


def run_offsets(meshes_dir, wmtk_app_exe, completed_nums_path):
    # collect completed nums
    completed_nums = set()
    try:
        with open(completed_nums_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    completed_nums.add(int(line))
    except FileNotFoundError:
        print(f"Error: completed pairs file [{completed_nums_path}] does not exist.")
        return
    
    # collect jsons
    meshes_path = Path(meshes_dir)
    json_files_to_run = []
    num_skipped = 0
    for data_dir in meshes_path.glob("data_*"):
        if not data_dir.is_dir():
            continue

        try:
            id = int(data_dir.name.split('_')[1])
        except ValueError:
            continue

        if id in completed_nums:
            num_skipped += 1
            continue
        
        singlebody_json = data_dir / "singlebody" / f"{id}_singlebody.json"
        if singlebody_json.exists():
            json_files_to_run.append(singlebody_json)
        else:
            print(f"Warning: json [{str(singlebody_json)}] does not exist")

        twobody_json = data_dir / "twobody" / f"{id}_twobody.json"
        if twobody_json.exists():
            json_files_to_run.append(twobody_json)
        else:
            print(f"Warning: json [{str(twobody_json)}] does not exist")
    print(f"Found {len(json_files_to_run)} total JSON configurations to process ({num_skipped} already completed)")

    # run in parallel
    max_workers = os.cpu_count()
    total_jobs = len(json_files_to_run)
    counts = [0, 0, 0]  # successes, fails, total
    glob_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_json, wmtk_app_exe, json_path): json_path
            for json_path in json_files_to_run
        }

        for future in concurrent.futures.as_completed(futures):
            json_path, returncode, stderr, duration = future.result()
            counts[2] += 1
            total_time = time.time() - glob_start_time
            time_stats = f"(took {duration:.2f}s | total elapsed: {total_time:.2f}s)"

            if returncode == 0:
                counts[0] += 1
                progress = f"[{counts[0] + counts[1]}/{total_jobs}] [{counts[0]} success|{counts[1]} fail]"
                print(f"{progress} [SUCCESS] {json_path.name} {time_stats}")
            else:
                counts[1] += 1
                progress = f"[{counts[0] + counts[1]}/{total_jobs}] [{counts[0]} success|{counts[1]} fail]"
                print(f"{progress} [FAILED] {json_path.name} (Return code: {returncode}) {time_stats}")
                print(f"\tError output: {stderr}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run offsets on tagged triwild dataset")
    parser.add_argument("-m", "--meshesdir", required=True, help="Input .msh file directory (subdirs each with tagged (0/1) 2D triangle meshes and subdir jsons)")
    parser.add_argument("-e", "--wmtk_app_exe", required=True, help="Path to wmtk_app executable")
    parser.add_argument("-c", "--completed_nums", required=True, help="Path to .txt file containing completed data nums (to be skipped)")
    args = parser.parse_args()
    run_offsets(args.meshesdir, args.wmtk_app_exe, args.completed_nums)