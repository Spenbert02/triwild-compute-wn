from pathlib import Path
import re

msh_dir_path = Path("/scratch/seb9449/offsets_testing_triwild/tagged_mshs_under_10mb/")

def main():
    count = 0
    deleted_counts = {"files": 0, "dirs": 0}
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

        vtu_path = model_dir / f"model_{model_id}_out.vtu"
        surf_vtu_path = model_dir / f"model_{model_id}_out_surf.vtu"
        msh_path = model_dir / f"model_{model_id}_out.msh"
        if (vtu_path.exists() or surf_vtu_path.exists() or msh_path.exists()):
            deleted_counts["dirs"] += 1
        else:
            continue

        if vtu_path.exists():
            vtu_path.unlink(missing_ok=False)
            deleted_counts["files"] += 1
        if surf_vtu_path.exists():
            surf_vtu_path.unlink(missing_ok=False)
            deleted_counts["files"] += 1
        if msh_path.exists():
            msh_path.unlink(missing_ok=False)
            deleted_counts["files"] += 1
    
    print(f"Deleted {deleted_counts['files']} files across {deleted_counts['dirs']} directories.")
        

if __name__ == "__main__":
    main()
