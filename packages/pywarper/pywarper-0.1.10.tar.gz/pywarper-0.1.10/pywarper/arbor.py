"""
pywarper.arbor
==============
Spatial warping and profiling utilities for **neuronal arbor reconstructions**.

This module takes a neuronal tree (nodes+edges) and the previously‑computed
ON/OFF Starburst Amacrine Cell (SAC) surface mapping in order to

1. **Warp the arbor into the flattened SAC coordinate frame** (`warp_arbor`).
   Each node is locally re‑registered with a polynomial least‑squares fit
   (`local_ls_registration`) that references both SAC layers so that depth is
   preserved relative to the curved retina.
2. **Compute depth (z) profiles** (`get_zprofile`).  Edge lengths are first binned
   directly (histogram) and then re‑estimated with a Kaiser–Bessel gridding
   kernel to obtain a smooth 1‑D density across the inner plexiform layer.
3. **Compute planar (xy) density maps** (`get_xyprofile`).  Dendritic length is
   accumulated on a user‑defined 2‑D grid and optionally Gaussian‑smoothed for
   visualisation or group statistics.

Key algorithms
--------------
* **Polynomial local registration** – For every node we fit a 2‑D polynomial
  basis (up to a configurable `max_order`) to the positions of neighbouring
  SAC‑band sample points, solving three separate least‑squares systems in one
  go with `numpy.linalg.lstsq`.  A single **KDTree** (SciPy) accelerates the
  neighbourhood queries.
* **Kaiser–Bessel gridding** – The 1‑D `gridder1d` function emulates the
  non‑uniform FFT gridding scheme used by older MATLAB code, yielding the exact
  same numerical output but in fully vectorised NumPy.
"""


import time
from typing import Optional, Union

import numpy as np
import trimesh
from numpy.linalg import lstsq
from scipy.ndimage import gaussian_filter
from scipy.spatial import KDTree
from scipy.special import i0
from skeliner.core import Skeleton, _bfs_parents


def poly_basis_2d(x: np.ndarray, y: np.ndarray, max_order: int) -> np.ndarray:
    """
    Return the full 2-D polynomial basis up to total order *max_order*
    for coordinates (x, y).  Shape:  (len(x), n_terms)

    Order layout ≡ original code:
        [1,
         x, y,
         x²,  x·y,  y²,      # order 2
         x³,  x²y, x y², y³, …]
    """
    cols = [np.ones_like(x), x, y]           # constant + linear
    for order in range(2, max_order + 1):
        for ox in range(order + 1):
            oy = order - ox
            cols.append(x**ox * y**oy)
    return np.stack(cols, axis=1)            # (N, n_terms)

def local_ls_registration(
    nodes: np.ndarray,
    top_input_pos: np.ndarray,
    bot_input_pos: np.ndarray,
    top_output_pos: np.ndarray,
    bot_output_pos: np.ndarray,
    window: float = 5.0,
    max_order: int = 2,
) -> np.ndarray:
    """
    Same algorithm as before, but a **single KDTree** stores both
    surfaces.  The neighbour search is therefore performed once.
    """
    transformed_nodes = np.zeros_like(nodes)

    # ------------------------------------------------------------------
    # 0.  merge the two bands  -----------------------------------------
    # ------------------------------------------------------------------
    in_all   = np.vstack((top_input_pos,  bot_input_pos))
    out_all  = np.vstack((top_output_pos, bot_output_pos))
    is_top   = np.concatenate((
        np.ones (len(top_input_pos), dtype=bool),
        np.zeros(len(bot_input_pos), dtype=bool)
    ))

    all_xy  = in_all[:, :2]                       # (Mtot, 2)

    # ------------------------------------------------------------------
    # 1.  one KD-tree and a *batched* query
    # ------------------------------------------------------------------
    query_r = window * np.sqrt(2.0)               # circumscribes rectangle
    tree    = KDTree(all_xy)
    idx_lists = tree.query_ball_point(nodes[:, :2], r=query_r, workers=-1)

    # ------------------------------------------------------------------
    # 2.  per-node loop (same math as before)
    # ------------------------------------------------------------------
    for k, (x, y, z) in enumerate(nodes):
        idx = np.array(idx_lists[k], dtype=int)   # neighbour indices

        # rectangular mask (identical criterion)
        lx, ux = x - window, x + window
        ly, uy = y - window, y + window
        mask_rect = (
            (all_xy[idx, 0] >= lx) & (all_xy[idx, 0] <= ux) &
            (all_xy[idx, 1] >= ly) & (all_xy[idx, 1] <= uy)
        )

        idx = idx[mask_rect]                      # inside the rectangle
        if idx.size == 0:
            print(f"[pywarper] Warning: no neighbours for node {k} at ({x:.2f}, {y:.2f}, {z:.2f})")
            transformed_nodes[k] = nodes[k]
            continue

        # split back into top / bottom — order preserved
        idx_top = idx[is_top[idx]]
        idx_bot = idx[~is_top[idx]]

        in_top,  out_top  = in_all[idx_top],  out_all[idx_top]
        in_bot,  out_bot  = in_all[idx_bot],  out_all[idx_bot]

        this_in  = np.vstack((in_top,  in_bot))
        this_out = np.vstack((out_top, out_bot))

        if this_in.shape[0] < 12:
            print(f"[pywarper] Warning: not enough neighbours for node {k} at ({x:.2f}, {y:.2f}, {z:.2f})")
            transformed_nodes[k] = nodes[k]
            continue

        # centre the neighbourhood
        shift_xy = this_in[:, :2].mean(axis=0)
        xin, yin, zin = (this_in[:, 0] - shift_xy[0],
                         this_in[:, 1] - shift_xy[1],
                         this_in[:, 2])

        xout, yout, zout = (this_out[:, 0] - shift_xy[0],
                            this_out[:, 1] - shift_xy[1],
                            this_out[:, 2])

        # polynomial basis
        base_terms = poly_basis_2d(xin, yin, max_order)          # (n_pts, n_terms)
        X = np.hstack((base_terms, base_terms * zin[:, None]))   # z-modulated


        # least-squares solve
        T, _, _, _ = lstsq(X, np.column_stack((xout, yout, zout)), rcond=None)

        # evaluate at the node
        nx, ny = nodes[k, 0] - shift_xy[0], nodes[k, 1] - shift_xy[1]
        basis_eval = poly_basis_2d(np.array([nx]), np.array([ny]), max_order).ravel()

        vec = np.concatenate((basis_eval, z * basis_eval))
        new_pos = vec @ T

        # undo shift
        new_pos[:2] += shift_xy
        transformed_nodes[k] = new_pos

    return transformed_nodes

def warp_nodes(
        nodes: np.ndarray,
        surface_mapping: dict,
        conformal_jump: int = 1,
        backward_compatible: bool = False,
) -> tuple[np.ndarray, float, float]:
    
    # Unpack mappings and surfaces
    mapped_on = surface_mapping["mapped_on"]
    mapped_off = surface_mapping["mapped_off"]
    on_sac_surface = surface_mapping["on_sac_surface"]
    off_sac_surface = surface_mapping["off_sac_surface"]

    if backward_compatible:
        sampled_x_idx = surface_mapping["sampled_x_idx"] + 1
        sampled_y_idx = surface_mapping["sampled_y_idx"] + 1
        # this is one ugly hack: thisx and thisy are 1-based in MATLAB
        # but 0-based in Python; the rest of the code is to produce exact
        # same results as MATLAB given the SAME input, that means thisx and 
        # thisy needs to be 1-based, but we need to shift it back to 0-based 
        # when slicing
    else:
        sampled_x_idx = surface_mapping["sampled_x_idx"]
        sampled_y_idx = surface_mapping["sampled_y_idx"]

    
    # Convert MATLAB 1-based inclusive ranges to Python slices
    # If thisx/thisy are consecutive integer indices:
    # x_vals = np.arange(thisx[0], thisx[-1] + 1)  # matches [thisx(1):thisx(end)] in MATLAB
    # y_vals = np.arange(thisy[0], thisy[-1] + 1)  # matches [thisy(1):thisy(end)] in MATLAB
    x_vals = np.arange(sampled_x_idx[0], sampled_x_idx[-1] + 1, conformal_jump)
    y_vals = np.arange(sampled_y_idx[0], sampled_y_idx[-1] + 1, conformal_jump)

    # Create a meshgrid shaped like MATLAB's [tmpymesh, tmpxmesh] = meshgrid(yRange, xRange).
    # This means we want shape (len(x_vals), len(y_vals)) for each array, with row=“x”, col=“y”:
    xmesh, ymesh = np.meshgrid(x_vals, y_vals, indexing="ij")
    # xmesh.shape == ymesh.shape == (len(x_vals), len(y_vals))

    # Extract the corresponding subregion of the surfaces so it also has shape (len(x_vals), len(y_vals)).
    # In MATLAB: tmpminmesh = thisVZminmesh(xRange, yRange)
    if backward_compatible:
        on_subsampled_depths =  on_sac_surface[x_vals[:, None]-1, y_vals-1]  # shape (len(x_vals), len(y_vals))
        off_subsampled_depths = off_sac_surface[x_vals[:, None]-1, y_vals-1]  # shape (len(x_vals), len(y_vals))
    else:
        on_subsampled_depths =  on_sac_surface[x_vals[:, None], y_vals]
        off_subsampled_depths = off_sac_surface[x_vals[:, None], y_vals]

    # Now flatten in column-major order (like MATLAB’s A(:)) to line up with tmpxmesh(:), etc.
    on_input_pts = np.column_stack([
        xmesh.ravel(order="F"),
        ymesh.ravel(order="F"),
        on_subsampled_depths.ravel(order="F")
    ]) # old topInputPos

    off_input_pts = np.column_stack([
        xmesh.ravel(order="F"),
        ymesh.ravel(order="F"),
        off_subsampled_depths.ravel(order="F")
    ]) # old botInputPos

    # Finally, the “mapped” output is unaffected by the flattening order mismatch,
    # but we keep it consistent with MATLAB’s final step:
    on_output_pts = np.column_stack([
        mapped_on[:, 0],
        mapped_on[:, 1],
        np.median(on_subsampled_depths) * np.ones(mapped_on.shape[0])
    ])

    off_output_pts = np.column_stack([
        mapped_off[:, 0],
        mapped_off[:, 1],
        np.median(off_subsampled_depths) * np.ones(mapped_off.shape[0])
    ])

    # return top_input_pos, bot_input_pos, top_output_pos, bot_output_pos

    # Apply local least-squares registration to each node
    warped = local_ls_registration(nodes, on_input_pts, off_input_pts, on_output_pts, off_output_pts)
    
    # Compute median Z-planes
    med_z_on = np.median(on_subsampled_depths)
    med_z_off = np.median(off_subsampled_depths)

    return warped, med_z_on, med_z_off

def normalize_nodes(
    nodes: np.ndarray,
    med_z_on: float,
    med_z_off: float,
    on_sac_pos: float = 0.0,
    off_sac_pos: float = 12.0,
) -> np.ndarray:
    """
    Normalize the z-coordinates of nodes based on the median z-values
    of the ON and OFF SAC surfaces.
    This function rescales the z-coordinates of the nodes to a normalized
    space where the ON SAC surface is at `on_sac_pos` and the OFF SAC
    surface is at `off_sac_pos`. The z-coordinates are adjusted based on
    the provided median z-values of the ON and OFF SAC surfaces.
    Parameters
    ----------
    nodes : np.ndarray
        (N, 3) array of [x, y, z] coordinates for the nodes to be normalized.
    med_z_on : float            
        Median z-value of the ON SAC surface.
    med_z_off : float
        Median z-value of the OFF SAC surface.
    on_sac_pos : float, default=0.0
        Desired position of the ON SAC surface in the normalized space (µm).
    off_sac_pos : float, default=12.0
        Desired position of the OFF SAC surface in the normalized space (µm).
    z_res : float, default=1.0
        Spatial resolution along z (µm / voxel) after warping.
    Returns
    -------
    np.ndarray
        (N, 3) array of [x, y, z] coordinates with normalized z-coordinates.
    """ 
    normalized_nodes = nodes.copy().astype(float)

    # Compute the relative depth of each node
    rel_depth = (nodes[:, 2] - med_z_on) / (med_z_off - med_z_on)  # 0→ON, 1→OFF

    # Rescale the z-coordinates to the normalized space
    z_phys = on_sac_pos + rel_depth * (off_sac_pos - on_sac_pos)  # µm in global frame
    normalized_nodes[:, 2] = z_phys  # update the z-coordinate to the flattened space

    return normalized_nodes


def warp_arbor(
    skel: Skeleton,
    surface_mapping: dict,
    voxel_resolution: Union[float, list] = [1., 1., 1.],
    conformal_jump: int = 1,
    on_sac_pos: float = 0.0,
    off_sac_pos: float = 12.0,
    zprofile_extends: list[float] | None = None, # [z_min, z_max]
    zprofile_nbins: int = 120,
    xyprofile_extends: list[float] | None = None, # [x_min, x_max, y_min, y_max]
    xyprofile_nbins: int = 20,
    xyprofile_smooth: float = 1.0,
    skeleton_nodes_scale: float = 1.0,
    backward_compatible: bool = False,
    verbose: bool = False,
) -> Skeleton:
    """
    Applies a local surface flattening (warp) to a neuronal arbor using the results
    of previously computed surface mappings.

    Parameters
    ----------
    nodes : np.ndarray
        (N, 3) array of [x, y, z] coordinates for the arbor to be warped.
    edges : np.ndarray
        (E, 2) array of indices defining connectivity between nodes.
    radii : np.ndarray
        (N,) array of radii corresponding to each node.
    surface_mapping : dict
        Dictionary containing keys:
          - "mapped_min_positions" : np.ndarray
              (X*Y, 2) mapped coordinates for one surface band (e.g., "min" band).
          - "mapped_max_positions" : np.ndarray
              (X*Y, 2) mapped coordinates for the other surface band (e.g., "max" band).
          - "thisVZminmesh" : np.ndarray
              (X, Y) mesh representing the first surface (“min” band) in 3D space.
          - "thisVZmaxmesh" : np.ndarray
              (X, Y) mesh representing the second surface (“max” band) in 3D space.
          - "thisx" : np.ndarray
              1D array of x-indices (possibly downsampled) used during mapping.
          - "thisy" : np.ndarray
              1D array of y-indices (possibly downsampled) used during mapping.
    conformal_jump : int, default=1
        Step size used in the conformal mapping (downsampling factor).
    verbose : bool, default=False
        If True, prints timing and progress information.

    Returns
    -------
    dict
        Dictionary containing:
          - "nodes": np.ndarray
              (N, 3) warped [x, y, z] coordinates after applying local registration.
          - "edges": np.ndarray
              (E, 2) connectivity array (passed through unchanged).
          - "radii": np.ndarray
              (N,) radii array (passed through unchanged).
          - "medVZmin": float
              Median z-value of the “min” surface mesh within the region of interest.
          - "medVZmax": float
              Median z-value of the “max” surface mesh within the region of interest.

    Notes
    -----
    1. The function extracts a subregion of the surfaces according to thisx/thisy and
       conformal_jump, matching the flattening step used in the mapping.
    2. Each node in `nodes` is then warped via local least-squares registration
       (`local_ls_registration`), referencing top (min) and bottom (max) surfaces.
    3. The median z-values (medVZmin, medVZmax) are recorded, which often serve as
       reference planes in further analyses.
    """

    nodes = skel.nodes.astype(float) * skeleton_nodes_scale  # scale to the surface unit, which is often μm

    # if not backward_compatible:
    #     nodes[:, :2] -= 1

    if verbose:
        print("[pywarper] Warping arbor...")
        start_time = time.time()
    warped_nodes, med_z_on, med_z_off = warp_nodes(
        nodes,
        surface_mapping,
        conformal_jump=conformal_jump,
        backward_compatible=backward_compatible,
    )

    normalized_nodes = normalize_nodes(
        warped_nodes,
        med_z_on=med_z_on,
        med_z_off=med_z_off,
        on_sac_pos=on_sac_pos,
        off_sac_pos=off_sac_pos,
    )

    normalized_nodes /= skeleton_nodes_scale

    if verbose:
        print(f"    done in {time.time() - start_time:.2f} seconds.")

    normalized_soma = skel.soma
    normalized_soma.centre = normalized_nodes[0] * voxel_resolution  # soma is at the first node

    skel_norm = Skeleton(
        soma   = normalized_soma,
        nodes  = normalized_nodes * voxel_resolution,
        edges  = skel.edges,      # same connectivity
        radii  = skel.radii,      # same radii dict
        ntype  = skel.ntype,      # same node types (if any) 
    )

    z_profile = get_zprofile(skel_norm, z_window=zprofile_extends, nbins=zprofile_nbins)
    xy_profile = get_xyprofile(
        skel_norm, xy_window=xyprofile_extends, nbins=xyprofile_nbins, sigma_bins=xyprofile_smooth
    )

    skel_norm.extra = {          
        "warped_nodes": warped_nodes * voxel_resolution, # keep the pre-normed nodes for reference
        "med_z_on":  float(med_z_on),
        "med_z_off": float(med_z_off),
        "z_profile": z_profile,
        "xy_profile": xy_profile,
        # "xy_shift": xy_shift,  # shift applied to the nodes
    }

    return skel_norm

def warp_mesh(
    mesh: trimesh.Trimesh, # mostly nm
    surface_mapping: dict, # mostly μm
    conformal_jump: int = 1,
    on_sac_pos: float = 0.0, # μm
    off_sac_pos: float = 12.0, # μm
    mesh_vertices_scale: float = 1.0, # scale factor for mesh vertices, e.g., 1e-3 for nm to μm
    backward_compatible: bool = False,
    verbose: bool = False,
) -> trimesh.Trimesh:
    """
    Applies a local surface flattening (warp) to a 3D mesh using the results
    of previously computed surface mappings.
    """

    vertices = mesh.vertices.astype(float) * mesh_vertices_scale # scale to the surface unit, which is often μm

    if verbose:
        print("[pywarper] Warping mesh...")
        start_time = time.time()
    warped_vertices, med_z_on, med_z_off = warp_nodes(
        vertices,
        surface_mapping,
        conformal_jump=conformal_jump,
        backward_compatible=backward_compatible,
    )

    normalized_vertices = normalize_nodes(
        warped_vertices,
        med_z_on=med_z_on,
        med_z_off=med_z_off,
        on_sac_pos=on_sac_pos,
        off_sac_pos=off_sac_pos,
    )

    if verbose:
        print(f"    done in {time.time() - start_time:.2f} seconds.")

    # Create a new mesh with the warped vertices
    warped_mesh = trimesh.Trimesh(
        vertices=normalized_vertices / mesh_vertices_scale, # rescale back to original units
        faces=mesh.faces,
        process=False,        # no processing
    )
    warped_mesh.metadata = mesh.metadata.copy()  # copy metadata
    warped_mesh.metadata["med_z_on"] = float(med_z_on)
    warped_mesh.metadata["med_z_off"] = float(med_z_off)
    warped_mesh.metadata["conformal_jump"] = conformal_jump
    warped_mesh.metadata["surface_mapping"] = surface_mapping
    warped_mesh.metadata["on_sac_pos"] = on_sac_pos
    warped_mesh.metadata["off_sac_pos"] = off_sac_pos

    return warped_mesh

# =====================================================================
# helpers for get_zprofile()
# =====================================================================

def segment_lengths(skel: Skeleton) -> tuple[np.ndarray, np.ndarray]:
    """Edge length at every non-root node & its mid-point."""
    # rebuild parent[] (BFS on undirected edges)
    parent = np.asarray(
        _bfs_parents(skel.edges, len(skel.nodes), root=0),
        dtype=np.int64,
    )
    child  = np.where(parent != -1)[0]           # (M,)
    vec    = skel.nodes[parent[child]] - skel.nodes[child]

    seglen = np.linalg.norm(vec, axis=1)

    density      = np.zeros(len(skel.nodes))
    density[child] = seglen

    mid = skel.nodes.copy()
    mid[child] += 0.5 * vec
    return density, mid

def gridder1d(
    z_samples: np.ndarray,
    density:   np.ndarray,
    n: int,
) -> np.ndarray:
    """
    Kaiser–Bessel gridding kernel in 1-D   (α=2, W=5)

    Vectorised patch-accumulation: identical output, ~2× faster.
    """
    if z_samples.shape != density.shape:
        raise ValueError("z_samples and density must have the same shape")

    # ------------------------------------------------------------------
    # Constants and lookup table (unchanged)
    # ------------------------------------------------------------------
    alpha, W, err = 2, 5, 1e-3
    S = int(np.ceil(0.91 / err / alpha))
    beta = np.pi * np.sqrt((W / alpha * (alpha - 0.5))**2 - 0.8)

    s = np.linspace(-1, 1, 2 * S * W + 1)
    F_kbZ = i0(beta * np.sqrt(1 - s**2))
    F_kbZ /= F_kbZ.max()

    # ------------------------------------------------------------------
    # Fourier transform of the 1-D kernel (unchanged)
    # ------------------------------------------------------------------
    Gz = alpha * n
    z = np.arange(-Gz // 2, Gz // 2)
    arg = (np.pi * W * z / Gz)**2 - beta**2

    kbZ = np.empty_like(arg, dtype=float)
    pos, neg = arg > 1e-12, arg < -1e-12
    kbZ[pos]      = np.sin (np.sqrt(arg[pos]))  / np.sqrt(arg[pos])
    kbZ[neg]      = np.sinh(np.sqrt(-arg[neg])) / np.sqrt(-arg[neg])
    kbZ[~(pos|neg)] = 1.0
    kbZ *= np.sqrt(Gz)

    # ------------------------------------------------------------------
    # Oversampled grid and *vectorised* accumulation
    # ------------------------------------------------------------------
    n_os = Gz
    out  = np.zeros(n_os, dtype=float)

    centre = n_os / 2 + 1                         # 1-based like MATLAB
    nz = centre + n_os * z_samples                # (N,)

    half_w = (W - 1) // 2
    lz_offsets = np.arange(-half_w, half_w + 1)   # (W,)

    # shape manipulations so that the first index is lz (to keep
    # addition order identical to the original loop)
    nz_mat   = nz[None, :] + lz_offsets[:, None]          # (W, N)
    nzt      = np.round(nz_mat).astype(int)               # (W, N)
    zpos_mat = S * ((nz[None, :] - nzt) + W / 2)          # (W, N)
    kw_mat   = F_kbZ[np.round(zpos_mat).astype(int)]      # (W, N)

    nzt_clipped = np.clip(nzt, 0, n_os - 1)               # (W, N)
    np.add.at(out,
              nzt_clipped.ravel(order="C"),               # lz-major order
              (density[None, :] * kw_mat).ravel(order="C"))

    out[0] = out[-1] = 0.0                                # edge artefacts

    # ------------------------------------------------------------------
    # myifft  →  de-apodise  →  abs(myfft3)  (unchanged)
    # ------------------------------------------------------------------
    u = n
    f = np.fft.ifftshift(np.fft.ifft(np.fft.ifftshift(out))) * np.sqrt(u)
    f = f[int(np.ceil((f.size - u) / 2)) : int(np.ceil((f.size + u) / 2))]
    f /= kbZ[u // 2 : 3 * u // 2]

    F = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(f))) / np.sqrt(f.size)
    return np.abs(F)

# =====================================================================
# helpers for get_zprofile() END
# =====================================================================

def get_zprofile(
    skel: Skeleton,
    z_window: Optional[list[float]] = None,
    nbins: int = 120, 
) -> dict:
    """
    Compute a 1-D depth profile (length per z-bin) from a warped arbor.

    Parameters
    ----------
    warped_arbor
        Dict returned by ``warp_arbor()``. Must contain
            'nodes'   – (N, 3) xyz coordinates in µm,
            'edges'   – (E, 2) SWC child/parent pairs (1-based),
            'medVZmin', 'medVZmax'  – median of the ON and OFF SAC surfaces.
    z_res
        Spatial resolution along z (µm / voxel) *after* warping. Depends on
        what unit the medvzmin/max were in. If they were already in µm, 
        then z_res = 1. If they were in pixels, then z_res = voxel_size.
    z_window
        Two floats ``[z_min, z_max]`` that define *one* common physical
        span (µm) for **all** cells *after* the ON/OFF anchoring.
        •  Default ``None`` means “just enough to cover the deepest /
           shallowest point of *this* cell” (original behaviour).  
        •  Example  ``z_window = (-6.0, 18.0)``  keeps a 6-µm margin on
           both sides of the SAC band while still centring it at 0–12 µm.
    on_sac_pos, off_sac_pos
        Desired positions of the starburst layers in the *final* profile
        (µm).  Defaults reproduce the numbers quoted in Sümbül et al. 2014.
    nbins
        Number of evenly-spaced output bins along z.

    Returns
    -------
    x_um
        Bin centres in micrometres (depth in IPL).
    z_dist
        Dendritic length contained in each bin (same units as input nodes).
    z_hist
        Histogram-based Dendritic length (same units as input nodes).
    z_window
        The actual z-window used for this cell, in the form
        ``[z_min, z_max]`` (µm).  If ``z_window`` was not specified,
        this will be the auto-computed span.
    """

    # 0) decide the common span
    if z_window is None:
        z_min, z_max = None, None                  # auto-span
    else:
        z_min, z_max = z_window                    # user-fixed span

    # 1) edge lengths and mid-point nodes   
    density, nodes = segment_lengths(skel)

    # 2) decide bin edges *once*
    z_phys = nodes[:, 2]                         # physical z-coordinates (µm)
    if z_min is None or z_max is None:
        # grow just enough to contain this cell, then round to one bin
        z_min = np.floor(z_phys.min())
        z_max = np.ceil(z_phys.max())

    bin_edges = np.linspace(z_min, z_max, nbins + 1)

    # 3) histogram-based z profile
    z_hist, _ = np.histogram(z_phys, bins=bin_edges, weights=density)
    z_hist *= density.sum() / (z_hist.sum())

    # 4) Kaiser–Bessel gridded version (needs centred –0.5…0.5 inputs) 
    centre = (z_min + z_max) / 2
    halfspan = (z_max - z_min) / 2
    z_samples = (z_phys - centre) / halfspan # now in [-1, 1]

    z_dist = gridder1d(z_samples / 2, density, nbins)  # /2 → [-0.5, 0.5]
    z_dist *= density.sum() / (z_dist.sum())

    # 5) bin centres & rescaled arbor
    x_um = 0.5 * (bin_edges[1:] + bin_edges[:-1])  # centre of each bin

    res = {
            "z_x": x_um,
            "z_dist": z_dist,
            "z_hist": z_hist,
            "z_window": [z_min, z_max],
        }

    return res

def get_xyprofile(
    skel: Skeleton,       
    xy_window: Optional[list[float]] = None,
    nbins: int = 20,
    sigma_bins: float = 1.0,
) -> dict:
    """
    2-D dendritic-length density on a fixed XY grid (no per-cell rotation).

    Parameters
    ----------
    warped_arbor   
        output of ``warp_arbor()`` (nodes in µm).
    xy_window      
        (xmin, xmax, ymin, ymax) in µm that *all* cells
                     share.  If ``None`` use this arbor's tight bounding box.
    nbins          
        number of bins along X **and** Y (default 20).

    Returns
    -------
    x_um:  (nbins,) µm 
        bin centres along X
    y_um: (nbins,) µm 
        bin centres along Y
    xy_dist: (nbins, nbins) µm  
        smoothed dendritic length per bin
    xy_hist: (nbins, nbins) µm
        histogram-based dendritic length per bin
    """

    # 1) edge lengths and mid-points (same helper you already have)
    density, mid = segment_lengths(skel)

    # 2) decide the common window
    if xy_window is None:
        xmin, xmax = mid[:, 0].min(), mid[:, 0].max()
        ymin, ymax = mid[:, 1].min(), mid[:, 1].max()
    else:
        xmin, xmax, ymin, ymax = xy_window

    # 3) 2-D histogram weighted by edge length and density
    xy_hist, x_edges, y_edges = np.histogram2d(
        mid[:, 0], mid[:, 1],
        bins=[nbins, nbins],
        range=[[xmin, xmax], [ymin, ymax]],
        weights=density
    )

    xy_dist = gaussian_filter(xy_hist, sigma=sigma_bins, mode='nearest')
    xy_dist *= density.sum() / xy_dist.sum()   # keep Σ = total length

    # 5) bin centres for plotting
    x = 0.5 * (x_edges[:-1] + x_edges[1:])
    y = 0.5 * (y_edges[:-1] + y_edges[1:])

    res = {
        "xy_x": x,
        "xy_y": y,
        "xy_dist": xy_dist,
        "xy_hist": xy_hist,
        "xy_window": [xmin, xmax, ymin, ymax],
        "xy_nbins": nbins,
        "xy_sigma_bins": sigma_bins,
    }

    return res