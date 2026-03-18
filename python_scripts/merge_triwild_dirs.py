"""
This file is extremely slow. do not use. Use the c++ executable
"""

import argparse
from alive_progress import alive_bar
import numpy as np
import meshio
from pathlib import Path
from numba import njit
from multiprocessing import Pool, Manager
from functools import partial
import os
import sys


@njit
def compute_winding_number_fast(C, A, B):
    num_tris = C.shape[0]
    num_edges = A.shape[0]
    wns = np.zeros(num_tris)
    
    for i in range(num_tris):
        q = C[i]
        total_angle = 0.0
        for j in range(num_edges):
            # Inline the math to avoid array overhead
            vax, vay = A[j, 0] - q[0], A[j, 1] - q[1]
            vbx, vby = B[j, 0] - q[0], B[j, 1] - q[1]
            
            cross = vax * vby - vay * vbx
            dot = vax * vbx + vay * vby
            total_angle += np.arctan2(cross, dot)
        wns[i] = total_angle / (2.0 * np.pi)
    return wns


"""Compute winding num at centroid of each triangle w.r.t. polyline"""
def compute_winding_number(V, F, V_poly, E_poly):
    C = np.mean(V[F], axis=1)
    A = V_poly[E_poly[:, 0]] # start point of each edge
    B = V_poly[E_poly[:, 1]] # end point of each edge
    return compute_winding_number_fast(C, A, B)


def read_obj_polyline(obj_path):
    """Read an OBJ file containing only 'v' (vertex) and 'l' (line/edge) entries."""
    verts = []
    edges = []
    with open(obj_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == 'v':
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'l':
                # OBJ edge indices are 1-based
                edges.append([int(parts[1]) - 1, int(parts[2]) - 1])
    return np.array(verts, dtype=float), np.array(edges, dtype=int)


def compute_write_out_msh(msh_path, obj_path, out_path):
    msh = meshio.read(msh_path)
    
    # Extract vertices and triangles from the .msh
    V_tri = msh.points
    if V_tri.shape[1] == 3:
        V_tri = V_tri[:, :2] # Make sure it's strictly 2D for winding number

    # Find the triangle blocks in the meshio object
    tri_cells = None
    cell_block_idx = -1
    for i, cell_block in enumerate(msh.cells):
        if cell_block.type == "triangle":
            tri_cells = cell_block.data
            cell_block_idx = i
            break
    if tri_cells is None:
        raise ValueError("No triangles found in the specified .msh file.")

    # Load the polyline from obj using igl (reads edges as 'faces')
    V_poly, E_poly = read_obj_polyline(obj_path)
    if V_poly.shape[1] == 3:
        V_poly = V_poly[:, :2]

    # Compute the robust winding number at each barycenter based on the polyline
    W = compute_winding_number(V_tri, tri_cells, V_poly, E_poly)
    IN = W < -0.5
    if np.sum(IN) == 0:
        IN = W > 0.5
    
    # Assign the winding numbers as cell data (tags) to the triangles
    # meshio stores cell_data as a dictionary of lists (one list per cell block)
    if msh.cell_data is None:
        msh.cell_data = {}
        
    # Initialize empty lists for all blocks if not present
    msh.cell_data["tag_0"] = [np.empty(0)] * len(msh.cells)

    # don't care about these, just to stop the warnings from being generated
    msh.cell_data["gmsh:physical"] = [np.zeros(len(c.data), dtype=int) for c in msh.cells]
    msh.cell_data["gmsh:geometrical"] = [np.zeros(len(c.data), dtype=int) for c in msh.cells]

    # Assign winding numbers as a 1D array to the triangle block
    # Ensure it's safely cast to floats
    msh.cell_data["tag_0"][cell_block_idx] = IN.astype(float)

    # Write the tagged mesh back to a new .msh file
    meshio.write(out_path, msh, file_format="gmsh22")


def process_single_pair(name, msh_dir, obj_dir, out_dir, active_dict):
    # update active mesh
    pid = os.getpid()
    active_dict[pid] = name

    # surpress everyting, want to retain progress bar
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    try:
        msh_path = msh_dir / f"{name}.msh"
        obj_path = obj_dir / f"{name}.obj"
        out_sub_dir = out_dir / f"data_{name}"
        out_sub_dir.mkdir(parents=False, exist_ok=True)
        out_path = out_sub_dir / f"{name}_tagged.msh"
        compute_write_out_msh(str(msh_path), str(obj_path), str(out_path))
    except Exception as e:
        pass  # NOTE: terminal comms are surpressed here, uncomment to debug if needed
    finally:
        if pid in active_dict:
            del active_dict[pid]

    return name


def merge_dirs(msh_dir_fpath, obj_dir_fpath, out_msh_dir_fpath):
    msh_dir = Path(msh_dir_fpath)
    obj_dir = Path(obj_dir_fpath)
    out_dir = Path(out_msh_dir_fpath)

    out_dir.mkdir(parents=True, exist_ok=True)
    msh_names = {f.stem for f in msh_dir.glob("*.msh") if f.stem.isdigit()}
    obj_names = {f.stem for f in obj_dir.glob("*.obj") if f.stem.isdigit()}
    matching_names = sorted(list(msh_names.intersection(obj_names)), key=int)

    if not matching_names:
        print("No matching file pairs found.")
        return
    
    print(f"Found {len(matching_names)} matching pairs. Processing...")

    with Manager() as manager:
        active_dict = manager.dict()
        func = partial(process_single_pair, msh_dir=msh_dir, obj_dir=obj_dir, out_dir=out_dir, active_dict=active_dict)
        with Pool(processes=None, maxtasksperchild=50) as pool:
            with alive_bar(len(matching_names), title="Processing meshes") as bar:
                for finished_name in pool.imap_unordered(func, matching_names):
                    current_tasks = [str(name) for name in active_dict.values()]
                    display_text = ", ".join(current_tasks)
                    bar.text(f"Active [{display_text}]")
                    bar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge triangulation (MSH) and curve (OBJ) files from triwild dataset")
    parser.add_argument("-m", "--meshesdir", required=True, help="Input .msh file directory (2D triangle meshes)")
    parser.add_argument("-c", "--curvesdir", required=True, help="Input .obj file directory (2D polylines)")
    parser.add_argument("-o", "--outputsdir", required=True, help="Output .msh file directory (tagged 2D triangle meshes)")
    args = parser.parse_args()
    merge_dirs(args.meshesdir, args.curvesdir, args.outputsdir)
