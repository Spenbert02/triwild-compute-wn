from pathlib import Path
import subprocess


ALL = 0  # run every single model
# UNSUCCESSFUL = 1  # run every model that hasn't already succeeded
LOGGED = 1  # run every model that has already been run
UNLOGGED = 2  # run every model that hasn't already been run (based off logs)
# TIMEOUT_OOM = 3

mesh_dir = f"/scratch/seb9449/offsets_testing_triwild/tagged_mshs_under_10mb/"
run_list_fpath = f"/scratch/seb9449/offsets_testing_triwild/triwild-compute-wn/bash_scripts_hpc/wmtk_triwild_array/pending_jobs.txt"
slurm_script_fpath = f"/scratch/seb9449/offsets_testing_triwild/triwild-compute-wn/bash_scripts_hpc/wmtk_triwild_array/wmtk_triwild_submit_array.slurm"
logs_dir = f"/scratch/seb9449/offsets_testing_triwild/triwild-compute-wn/bash_scripts_hpc/wmtk_triwild_array/logs"

RUN_MODE = UNLOGGED
CHUNK_SIZE = 5000
MAX_CHUNKS = 1

def get_most_recent_log(model_id):
    ret_id = 0
    if not (Path(logs_dir) / f"model_{model_id}_(0).out").exists():
        return None
    else:
        while (Path(logs_dir) / f"model_{model_id}_({ret_id + 1}).out").exists():
            ret_id += 1
        return ret_id

def main():
    mesh_dir_path = Path(mesh_dir)
    if not (mesh_dir_path.exists() and mesh_dir_path.is_dir()):
        raise FileNotFoundError(f"{str(mesh_dir_path)} does not exist")
    
    # collect already run models
    log_dir_path = Path(logs_dir)
    already_run = set()
    if (log_dir_path.exists() and log_dir_path.is_dir()):
        for p in log_dir_path.iterdir():
            if not (p.is_file() and p.suffix.lower() == ".out"):
                continue
            try:
                model_id = int(p.stem.split("_")[1])
            except:
                print(f"WARNING: non-int-parseable log file at {str(log_dir_path)}")
                continue
            already_run.add(model_id)

    # collect jsons
    jsons_to_run = []
    print("0", end="")  # terminal comms
    for i, subdir in enumerate(mesh_dir_path.glob("model_*")):
        if i % 100 == 0:  # terminal comms
            print(f"\r{i}\t", end="")

        if not (subdir.exists() and subdir.is_dir()):
            continue

        try:
            model_id = int(subdir.name.split("_")[1])
        except:
            print(f"WARNING: non-int model id at {str(subdir)}")
            continue

        if (RUN_MODE == UNLOGGED) and (model_id in already_run):
            continue
        elif (RUN_MODE == LOGGED) and (model_id not in already_run):
            continue
        
        # input_obj_path = subdir / f"model_{model_id}.obj"
        # if not input_obj_path.exists():
        #     print(f"WARNING: no obj for model {model_id}")
        #     continue

        # output_msh_path = subdir / f"remeshing_test{REMESHING_TEST_NUM}" / f"model_{model_id}_out.msh"
        # if output_msh_path.exists() and (RUN_MODE != ALL):
        #     continue

        # if RUN_MODE == TIMEOUT_OOM:
        #     log_num = get_most_recent_log(model_id)
        #     if log_num is not None:
        #         err_path = Path(logs_dir) / f"model_{model_id}_({log_num}).err"
        #         with open(str(err_path), "r") as f:
        #             lines = f.readlines()
        #             include = False
        #             for line in lines:
        #                 if "DUE TO TIME LIMIT" in line:
        #                     include = True
        #                     break
        #                 if "OOM Killed" in line:
        #                     include = True
        #                     break
        #             if include:
        #                 json_path = subdir / f"remeshing_test{REMESHING_TEST_NUM}" / f"remeshing_test{REMESHING_TEST_NUM}_{model_id}.json"
        #                 if not json_path.exists():
        #                     print(f"WARNING: json {str(json_path)} does not exist")
        #                 else:
        #                     jsons_to_run.append(str(json_path))
        # else:
        json_path = subdir / f"wmtk_triwild" / f"wmtk_triwild_{model_id}.json"
        if not json_path.exists():
            print(f"WARNING: json {str(json_path)} does not exist")
        else:
            jsons_to_run.append(str(json_path))

    run_list_path = Path(run_list_fpath)
    
    num_jobs = len(jsons_to_run)
    print(f"Found {num_jobs} [wmtk_triwild] jobs to run")
    chunks = [jsons_to_run[i:i + CHUNK_SIZE] for i in range(0, num_jobs, CHUNK_SIZE)]
    for idx, chunk in enumerate(chunks):
        if MAX_CHUNKS:
            if idx > (MAX_CHUNKS - 1):
                continue
        chunk_file = run_list_path.with_name(f"pending_jobs_{idx}.txt")
        with open(chunk_file, "w") as f:
            for json_path in chunk:
                f.write(f"{json_path}\n")
        arr_max = len(chunk) - 1
        slurm_script_path = Path(slurm_script_fpath)
        sbatch_cmd = ["sbatch", f"--array=0-{arr_max}", "--mail-user=seb9449@nyu.edu", "--mail-type=BEGIN,END,FAIL,REQUEUE", str(slurm_script_path), str(chunk_file)]
        print(f"Submitting chunk {idx+1}/{len(chunks)}: {' '.join(sbatch_cmd)}")
        try:
            subprocess.run(sbatch_cmd, check=True)
            print(f"Chunk {idx+1}/{len(chunks)} successfully committed to queue")
        except subprocess.CalledProcessError as e:
            print(f"Failed to submit chunk {idx}. Error: {e}")
            break
        except FileNotFoundError:
            print("Error: 'sbatch' command not found. Are you running this on the HPC login node?")
            break


if __name__ == "__main__":
    main()