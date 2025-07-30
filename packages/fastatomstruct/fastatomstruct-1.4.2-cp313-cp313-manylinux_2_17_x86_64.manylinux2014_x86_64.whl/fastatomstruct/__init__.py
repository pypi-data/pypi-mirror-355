from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from time import time

import ase
import numpy as np
from .fastatomstruct import *
from scipy.integrate import simpson as simps
from scipy.fftpack import fft
from tidynamics import msd

# Compatibility for older numpy versions
if hasattr(np, "trapezoid"):
    trapezoid = np.trapezoid
else:
    trapezoid = np.trapz

rank = None


def is_root() -> bool:
    """Check if the current process is the root process."""
    if rank is None:
        return True
    return rank == 0


def chunks(indices: List[int], n: int):
    """Yield successive chunks from list of atoms."""
    for i in range(0, len(indices), n):
        yield indices[i : i + n]


def ipar(
    func: Callable, atoms: List[ase.Atoms], *args: List[Any], **kwargs: Dict[Any, Any]
) -> List[Any]:
    """Image-based parallelization.

    The calculation of many structural quantities is parallelized over atoms.
    However, image-based parallelization (or a mixture of both) can be more efficient
    in some cases. This function makes using this parallelization layer quite easy.
    You can just use it as a simple wrapper around other functions implemented in
    `fastatomstruct` (see example below). **This function needs a working installation
    of the MPI4Py package!** You can set the `RAYON_NUM_THREADS` enviroment variable
    to control the number of threads.

    Arguments:
        func (Callable): Some function from the `fastatomstruct` package
        atoms (List[ase.Atoms]): List of ASE configurations

    Returns:
        List of results; type depends on the output of func

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.
    The code below needs to be run e.g. with `mpirun -n 2 test.py`. In this case,
    two processes will be used.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> if fs.is_root():
       >>>     atoms = io.read("Sb-1.00-300-100.traj", index="::200")
       >>> q = fs.ipar(fs.q_tetrahedral, atoms, fs.CutoffMode.Fixed(3.2), 3)
       >>> if fs.is_root():
       >>>     plt.hist(q[0], bins=25, alpha=0.5)
       >>>     plt.hist(q[1], bins=25, color="C3", alpha=0.5)
    """
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    global rank
    rank = comm.Get_rank()

    if rank == 0:
        print("\nImage parallelization report\n" + "----------------------------")

    if rank == 0:
        res_full, t0_f = [], time()

    for i, c in enumerate(chunks(list(range(len(atoms))), comm.size)):
        while len(c) < comm.size:
            c.append(None)

        if rank == 0:
            per = (len(c) - np.count_nonzero([ci is None for ci in c])) / len(c)
            t0 = time()
        if c[rank] is not None:
            a = atoms[c[rank]]
            res = func(a, *args, **kwargs)
        else:
            res = None

        res = comm.gather(res, root=0)
        if rank == 0:
            t = time() - t0
            print(f"Chunk {i + 1}: {per * 100:03.2f}% | {t:.2f} s")
            res_full.extend(res)

    if rank == 0:
        for i in range(len(res_full) - 1, -1, -1):
            if res_full[i] is None:
                del res_full[i]
        print("----------------------------")
        print(f"Total: {(time() - t0_f):.2f} s\n")
    else:
        res_full = None

    return res_full


def static_structure_factor(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    q: np.ndarray,
    cutoff: CutoffMode,
    n_bins: int,
    filter: Optional[Union[FilterTag, FilterElement]] = None,
) -> np.ndarray:
    """Static structure factor, as calculated from the RDF.

    For isotropic systems, the static structure factor can be calculated using

    .. math::

        S(q) = q + 4 \\pi \\rho \\int_0^\\infty r (g(r) - 1) \\frac{\\sin{qr}}{q} dr,

    with :math:`q` the absolute value of the reciprocal vector and :math:`g(r)`
    the radial distribution function.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        q (np.ndarray): Array with values of :math:`q`
        r_max (float): Cutoff radius for calculating the radial distribution function
        n_bins (int): Number of bins for calculating the radial distribution function
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter applied to the atoms

    Returns:
        np.ndarray of floats with values of :math:`S(q)`

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index="-500::10")
       >>> q = np.linspace(1.1, 10, 100)
       >>> cutoff = fs.CutoffMode.Fixed(10)
       >>> s = fs.static_structure_factor(atoms, q, cutoff, 100)
       >>> plt.plot(q, s)
       >>> plt.xlabel(r"$q$ $(\\mathrm{\\AA^{-1}})$")
       >>> plt.ylabel(r"$S(q)$")
       >>> plt.xlim(0, 10)
       >>> plt.ylim(0)
    """
    if isinstance(atoms, list):
        rdf = []
        for a in atoms:
            r, rdf_i = radial_distribution_function(a, cutoff, n_bins, filter)
            rdf.append(rdf_i)
        rdf = np.mean(rdf, axis=0)
        rho = len(atoms[0]) / atoms[0].get_volume()
    else:
        r, rdf = radial_distribution_function(atoms, cutoff, n_bins)
        rho = len(atoms) / atoms.get_volume()

    integral = np.zeros(len(q))
    for i, qi in enumerate(q):
        integrand = r[1:] * np.sin(qi * r[1:]) * (rdf[1:] - 1)
        integral[i] = trapezoid(integrand, r[1:])
    return 1 + 4 * np.pi * rho / q * integral


def static_structure_factor_shells(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    q: np.ndarray,
    cutoff: CutoffMode,
    n_bins: int,
    n_shells: int,
    filter: Optional[Union[FilterTag, FilterElement]] = None,
) -> np.ndarray:
    """Static structure factor for each nearest-neighbour shell, as calculated from the shell-resolved RDF.

    For isotropic systems, the static structure factor can be calculated for each shell using

    .. math::

        S_i(q) = q + 4 \\pi \\rho \\int_0^\\infty r (g_i(r) - 1) \\frac{\\sin{qr}}{q} dr,

    with :math:`q` the absolute value of the reciprocal vector and :math:`g_i(r)`
    the radial distribution function for the i-th nearest-neighbour shell.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        q (np.ndarray): Array with values of :math:`q`
        cutoff (CutoffMode): Cutoff mode for calculating the radial distribution function
        n_bins (int): Number of bins for calculating the radial distribution function
        n_shells (int): Number of shells to calculate
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter applied to the atoms

    Returns:
        np.ndarray of floats with values of :math:`S_i(q)` for each shell, with shape (n_shells, len(q))

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index="-500::10")
       >>> q = np.linspace(1.1, 10, 100)
       >>> cutoff = fs.CutoffMode.Fixed(10)
       >>> s = fs.static_structure_factor_shells(atoms, q, cutoff, 100, 3)
       >>> for i in range(s.shape[0]):
       >>>     plt.plot(q, s[i], label=f"Shell {i+1}")
       >>> plt.xlabel(r"$q$ $(\\mathrm{\\AA^{-1}})$")
       >>> plt.ylabel(r"$S(q)$")
       >>> plt.xlim(0, 10)
       >>> plt.ylim(0)
       >>> plt.legend()
    """
    if isinstance(atoms, list):
        all_shells_rdf = []
        for a in atoms:
            r, rdf_shells = radial_distribution_function_shells(
                a, cutoff, n_bins, n_shells, filter
            )
            all_shells_rdf.append(rdf_shells)
        # Average the shell-resolved RDFs over all configurations
        rdf_shells = np.mean(all_shells_rdf, axis=0)
        rho = len(atoms[0]) / atoms[0].get_volume()
    else:
        r, rdf_shells = radial_distribution_function_shells(
            atoms, cutoff, n_bins, n_shells, filter
        )
        rho = len(atoms) / atoms.get_volume()

    # Calculate S(q) for each shell
    s_q = np.zeros((n_shells, len(q)))

    for shell in range(n_shells):
        for i, qi in enumerate(q):
            # Use the RDF for this specific shell
            shell_rdf = rdf_shells[shell]
            # Calculate the integrand: r * sin(qr) * (g(r) - 1)
            integrand = r[1:] * np.sin(qi * r[1:]) * (shell_rdf[1:] - 1)
            # Integrate and add the result to S(q)
            s_q[shell, i] = 1 + 4 * np.pi * rho / qi * trapezoid(integrand, r[1:])

    return s_q


def __convert_pos(atoms: List[ase.Atoms]) -> List[np.ndarray]:
    pos = []
    for i in range(len(atoms[0])):
        pos_temp = np.empty((len(atoms), 3))
        for j, a in enumerate(atoms):
            pos_temp[j, :] = a.positions[i, :]
        pos.append(pos_temp)
    return pos


def mean_squared_displacement(atoms: List[ase.Atoms], timestep: float) -> np.ndarray:
    """Mean squared displacment of a trajectory.

    The MSD is calculated using the `tidynamics` package. It is defined as

    .. math::

        \\mathrm{MSD} = \\frac{1}{N} \\sum_{i = 1}^N |\\vec{x}_i(t) - \\vec{x}_i(0)|^2,

    where the :math:`\\vec{x}_i(t)` are the atomic positions at time :math:`t`.

    Arguments:
        atoms (List[ase.Atoms]): Trajectory, atoms objects from ASE
        timestep (float): Time step

    Returns:
        Two NumPy arrays of floats containing the time and mean squared displacement

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
       >>> time, msd = fs.mean_squared_displacement(atoms, 200)
       >>> plt.loglog(time / 1000, msd)
       >>> plt.xlabel(r"$t$ (ps)")
       >>> plt.ylabel(r"Mean squared displacement ($\\mathrm{\\AA^2}$)")
    """
    time = np.arange(0, len(atoms)) * timestep
    return time, squared_displacement(atoms).mean(axis=0)


def squared_displacement(atoms: List[ase.Atoms]) -> np.ndarray:
    """Squared displacment of a trajectory.

    The SD is calculated using the `tidynamics` package. It is defined as

    .. math::

        \\mathrm{SD}_i = |\vec{x}_i(t) - \vec{x}_i(0)|^2,

    where the :math:`\vec{x}_i(t)` are the atomic positions at time :math:`t`.

    Arguments:
        atoms (List[ase.Atoms]): Trajectory, atoms objects from ASE

    Returns:
        NumPy Array of floats containing the mean squared displacement

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    >>> import fastatomstruct as fs
    >>> from ase import io
    >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
    >>> fs.mean_squared_displacement(atoms)
    array([[-2.91038305e-11,  8.38161177e-02,  1.25422533e-01, ...,
             6.15651363e-01,  5.27809637e-01,  6.19426924e-01],
           [ 0.00000000e+00,  9.27498088e-02,  1.52887610e-01, ...,
             1.07754904e+00,  1.10512104e+00,  1.46645886e+00],
           [-1.16415322e-10,  8.61089322e-02,  1.37081905e-01, ...,
             1.27085909e+00,  1.18840340e+00,  9.64727558e-01],
           ...,
           [-4.65661287e-10,  9.55223907e-02,  1.56593970e-01, ...,
             4.45991428e-01,  2.80684893e-01,  1.91919705e-01],
           [ 0.00000000e+00,  8.69368854e-02,  1.34933834e-01, ...,
             4.86719506e-01,  3.47152810e-01,  5.66086433e-01],
           [-9.31322575e-10,  8.86508557e-02,  1.46782934e-01, ...,
             6.20435820e-01,  7.15149704e-01,  1.23890466e+00]])
    """
    pos = __convert_pos(atoms)
    m = [msd(p) for p in pos]
    return np.array(m)


class VDOSMethod(Enum):
    DIRECT = 1
    VACF = 2


"""Large parts of the code below are taken from the pwtools package,
which is licensed under the BSD 3-Clause License.

The original code can be found here: https://github.com/elcorto/pwtools

The original license is as follows:

Copyright (c) Steve Schmerler <git@elcorto.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


def vibrational_dos(
    atoms: List[ase.Atoms],
    timestep: float,
    full_out: bool = False,
    method: VDOSMethod = VDOSMethod.DIRECT,
    area: float = 1.0,
    use_masses: bool = True,
    window: bool = True,
    mirror: bool = False,
    npad: Optional[int] = None,
    to_next: bool = False,
):
    """Phonon DOS by direct FFT of velocities, or FFT of the VACF.

    The vibrational density of states (DOS) :cite:`leeInitioStudiesStructural1993` is calculated using either the direct Fast Fourier Transform (FFT) of the velocities or the FFT of the Velocity Auto-Correlation Function (VACF). The method used is specified by the `method` argument.

    - If `method` is `VDOSMethod.DIRECT`, the DOS is calculated by performing an FFT on the velocity data directly.
    - If `method` is `VDOSMethod.VACF`, the DOS is calculated by first computing the VACF of the velocities and then performing an FFT on the VACF.

    The integral area under the frequency-PDOS curve is normalized to the value specified by the `area` argument. Zero-padding the velocities (specified by `npad`) is recommended.

    Welch windowing can be applied to the data before performing the FFT to reduce spectral leakage, which is controlled by the `window` argument. Additionally, the data can be mirrored before the FFT, controlled by the `mirror` argument.

    The function returns a tuple containing the frequency and the PDOS. If `full_out` is set to True, additional outputs may be included in the returned tuple. The PDOS is given in 1/meV.

    Arguments:
        atoms (List[ase.Atoms]): Atoms object(s) from ASE
        timestep (float): Time step
        full_out (bool): Whether all output should be given, or just frequency and PDOS
        method (fastatomstruct.VDOSMethod): Method for the DOS calculation (VDOSMethod.DIRECT or VDOSMethod.VACF). PDOSMethod.DIRECT is recommended.
        area (float): Normalize area under frequency-PDOS curve to this value
        use_masses (bool): Whether to use masses in the calculation (default: True)
        window (bool): Use Welch windowing on data before FFT (reduces leaking effect,
        recommended, default is True)
        mirror (bool): Mirror one-sided VACF at t=0 before FFT (default: False)
        to_next (bool): method=PDOSMethod.DIRECT only: Pad `vel` with zeros along `axis` up to the next power of two after the array length determined by `npad`. This gives you speed, but variable (better) frequency resolution. Default: False

    Returns
    -------
        if full_out = False
            | ``(faxis, pdos)``
            | faxis : 1d array [1/unit(dt)]
            | pdos : 1d array, the phonon DOS, normalized to `area`
        if full_out = True
            | if method == 'direct':
            |     ``(faxis, pdos, (full_faxis, full_pdos, split_idx))``
            | if method == 'vavcf':
            |     ``(faxis, pdos, (full_faxis, full_pdos, split_idx, vacf, fft_vacf))``
            |     fft_vacf : 1d complex array, result of fft(vacf) or fft(mirror(vacf))
            |     vacf : 1d array, the VACF

    Examples
    --------

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> freq, pdos = fs.vibrational_dos(atoms, 100)
       >>> freq *= 1000
       >>> plt.plot(freq, pdos, label="Direct")
       >>> freq, pdos = fs.vibrational_dos(atoms, 100, method=fs.VDOSMethod.VACF)
       >>> freq *= 1000
       >>> plt.plot(freq, pdos, color="C3", label="VACF")
       >>> plt.xlim(freq.min(), freq.max())
       >>> plt.xlim(0, 5)
       >>> plt.ylim(0, 350)
       >>> plt.xlabel("Frequency (THz)")
       >>> plt.ylabel("Phonon DOS")
       >>> plt.legend()
       >>> plt.tight_layout()
    """

    axis = 0
    if window:
        sl = [None] * 3
        sl[axis] = slice(None)  # ':'
        w = __welch(len(atoms))[tuple(sl)]
        atoms_old = atoms
        atoms = []

        for i, a in enumerate(atoms_old):
            vel = a.get_velocities()
            a = a.copy()
            a.set_velocities(vel * w[i])
            atoms.append(a)

    if method == VDOSMethod.DIRECT:
        vel2 = np.array([a.get_velocities() for a in atoms])
        mass_bc = atoms[0].get_masses()[None, :, None]

        if npad is not None:
            nadd = (vel2.shape[axis] - 1) * npad
            if to_next:
                vel2 = __pad_zeros(
                    vel2, tonext=True, tonext_min=vel2.shape[axis] + nadd, axis=axis
                )
            else:
                vel2 = __pad_zeros(vel2, tonext=False, nadd=nadd, axis=axis)

        full_fft_vel = np.abs(fft(vel2, axis=axis)) ** 2.0
        full_faxis = np.fft.fftfreq(vel2.shape[axis], timestep)
        split_idx = len(full_faxis) // 2
        faxis = full_faxis[:split_idx]
        # First split the array, then multiply by `mass` and average. If
        # full_out, then we need full_fft_vel below, so copy before slicing.
        arr = full_fft_vel.copy() if full_out else full_fft_vel
        fft_vel = __slicetake(arr, slice(0, split_idx), axis=axis, copy=False)
        if use_masses:
            fft_vel *= mass_bc
        # average remaining axes, summing is enough b/c normalization is done below
        # sums: (nstep, natoms, 3) -> (nstep, natoms) -> (nstep,)
        pdos = __enh_sum(fft_vel, axis=axis, keepdims=True)
        default_out = (faxis, __norm_int(pdos, faxis, area=area))
        if full_out:
            # have to re-calculate this here b/c we never calculate the full_pdos
            # normally
            if use_masses:
                full_fft_vel *= mass_bc
            full_pdos = __enh_sum(full_fft_vel, axis=axis, keepdims=True)
            extra_out = (full_faxis, full_pdos, split_idx)
            return default_out + extra_out
        else:
            return default_out

    elif method == VDOSMethod.VACF:
        _, v = vacf(atoms, timestep=timestep, use_masses=use_masses)
        if mirror:
            fft_vacf = fft(__mirror(v))
        else:
            fft_vacf = fft(v)
        full_faxis = np.fft.fftfreq(fft_vacf.shape[axis], timestep)
        full_pdos = np.abs(fft_vacf)
        split_idx = len(full_faxis) // 2
        faxis = full_faxis[:split_idx]
        pdos = full_pdos[:split_idx]
        default_out = (faxis, __norm_int(pdos, faxis, area=area))
        extra_out = (full_faxis, full_pdos, split_idx, v, fft_vacf)
        if full_out:
            return default_out + extra_out
        else:
            return default_out


def __pad_zeros(
    arr, axis=0, where="end", nadd=None, upto=None, tonext=None, tonext_min=None
):
    """Pad an nd-array with zeros. Default is to append an array of zeros of
    the same shape as `arr` to arr's end along `axis`.

    Parameters
    ----------
    arr :  nd array
    axis : the axis along which to pad
    where : string {'end', 'start'}, pad at the end ("append to array") or
        start ("prepend to array") of `axis`
    nadd : number of items to padd (i.e. nadd=3 means padd w/ 3 zeros in case
        of an 1d array)
    upto : pad until arr.shape[axis] == upto
    tonext : bool, pad up to the next power of two (pad so that the padded
        array has a length of power of two)
    tonext_min : int, when using `tonext`, pad the array to the next possible
        power of two for which the resulting array length along `axis` is at
        least `tonext_min`; the default is tonext_min = arr.shape[axis]

    Use only one of nadd, upto, tonext.

    Returns
    -------
    padded array

    Examples
    --------
    >>> # 1d
    >>> pad_zeros(a)
    array([1, 2, 3, 0, 0, 0])
    >>> pad_zeros(a, nadd=3)
    array([1, 2, 3, 0, 0, 0])
    >>> pad_zeros(a, upto=6)
    array([1, 2, 3, 0, 0, 0])
    >>> pad_zeros(a, nadd=1)
    array([1, 2, 3, 0])
    >>> pad_zeros(a, nadd=1, where='start')
    array([0, 1, 2, 3])
    >>> # 2d
    >>> a=arange(9).reshape(3,3)
    >>> pad_zeros(a, nadd=1, axis=0)
    array([[0, 1, 2],
           [3, 4, 5],
           [6, 7, 8],
           [0, 0, 0]])
    >>> pad_zeros(a, nadd=1, axis=1)
    array([[0, 1, 2, 0],
           [3, 4, 5, 0],
           [6, 7, 8, 0]])
    >>> # up to next power of two
    >>> 2**arange(10)
    array([  1,   2,   4,   8,  16,  32,  64, 128, 256, 512])
    >>> pydos.pad_zeros(arange(9), tonext=True).shape
    (16,)
    """
    if tonext == False:
        tonext = None
    lst = [nadd, upto, tonext]
    assert lst.count(None) in [2, 3], (
        "`nadd`, `upto` and `tonext` must be " + "all None or only one of them not None"
    )
    if nadd is None:
        if upto is None:
            if (tonext is None) or (not tonext):
                # default
                nadd = arr.shape[axis]
            else:
                tonext_min = arr.shape[axis] if (tonext_min is None) else tonext_min
                # beware of int overflows starting w/ 2**arange(64), but we
                # will never have such long arrays anyway
                two_powers = 2 ** np.arange(30)
                assert tonext_min <= two_powers[-1], (
                    "tonext_min exceeds " "max power of 2"
                )
                power = two_powers[np.searchsorted(two_powers, tonext_min)]
                nadd = power - arr.shape[axis]
        else:
            nadd = upto - arr.shape[axis]
    if nadd == 0:
        return arr
    add_shape = list(arr.shape)
    add_shape[axis] = nadd
    add_shape = tuple(add_shape)
    if where == "end":
        return np.concatenate((arr, np.zeros(add_shape, dtype=arr.dtype)), axis=axis)
    elif where == "start":
        return np.concatenate((np.zeros(add_shape, dtype=arr.dtype), arr), axis=axis)
    else:
        raise Exception("illegal `where` arg: %s" % where)


def __slicetake(a, sl, axis=None, copy=False):
    """The equivalent of numpy.take(a, ..., axis=<axis>), but accepts slice
    objects instead of an index array. Also by default, it returns a *view* and
    no copy.

    Parameters
    ----------
    a : numpy ndarray
    sl : slice object, list or tuple of slice objects
        axis=<int>
            one slice object for *that* axis
        axis=None
            `sl` is a list or tuple of slice objects, one for each axis.
            It must index the whole array, i.e. len(sl) == len(a.shape).
    axis : {None, int}
    copy : bool, return a copy instead of a view

    Returns
    -------
    A view into `a` or copy of a slice of `a`.

    Examples
    --------
    >>> from numpy import s_
    >>> a = np.random.rand(20,20,20)
    >>> b1 = a[:,:,10:]
    >>> # single slice for axis 2
    >>> b2 = slicetake(a, s_[10:], axis=2)
    >>> # tuple of slice objects
    >>> b3 = slicetake(a, s_[:,:,10:])
    >>> (b2 == b1).all()
    True
    >>> (b3 == b1).all()
    True
    >>> # simple extraction too, sl = integer
    >>> (a[...,5] == slicetake(a, 5, axis=-1))
    True
    """
    # The long story
    # --------------
    #
    # 1) Why do we need that:
    #
    # # no problem
    # a[5:10:2]
    #
    # # the same, more general
    # sl = slice(5,10,2)
    # a[sl]
    #
    # But we want to:
    #  - Define (type in) a slice object only once.
    #  - Take the slice of different arrays along different axes.
    # Since numpy.take() and a.take() don't handle slice objects, one would
    # have to use direct slicing and pay attention to the shape of the array:
    #
    #     a[sl], b[:,:,sl,:], etc ...
    #
    # We want to use an 'axis' keyword instead. np.r_() generates index arrays
    # from slice objects (e.g r_[1:5] == r_[s_[1:5] ==r_[slice(1,5,None)]).
    # Since we need index arrays for numpy.take(), maybe we can use that? Like
    # so:
    #
    #     a.take(r_[sl], axis=0)
    #     b.take(r_[sl], axis=2)
    #
    # Here we have what we want: slice object + axis kwarg.
    # But r_[slice(...)] does not work for all slice types. E.g. not for
    #
    #     r_[s_[::5]] == r_[slice(None, None, 5)] == array([], dtype=int32)
    #     r_[::5]                                 == array([], dtype=int32)
    #     r_[s_[1:]]  == r_[slice(1, None, None)] == array([0])
    #     r_[1:]
    #         ValueError: dimensions too large.
    #
    # The returned index arrays are wrong (or we even get an exception).
    # The reason is given below.
    # Bottom line: We need this function.
    #
    # The reason for r_[slice(...)] gererating sometimes wrong index arrays is
    # that s_ translates a fancy index (1:, ::5, 1:10:2, ...) to a slice
    # object. This *always* works. But since take() accepts only index arrays,
    # we use r_[s_[<fancy_index>]], where r_ translates the slice object
    # prodced by s_ to an index array. THAT works only if start and stop of the
    # slice are known. r_ has no way of knowing the dimensions of the array to
    # be sliced and so it can't transform a slice object into a correct index
    # array in case of slice(<number>, None, None) or slice(None, None,
    # <number>).
    #
    # 2) Slice vs. copy
    #
    # numpy.take(a, array([0,1,2,3])) or a[array([0,1,2,3])] return a copy of
    # `a` b/c that's "fancy indexing". But a[slice(0,4,None)], which is the
    # same as indexing (slicing) a[:4], return *views*.

    if axis is None:
        slices = sl
    else:
        # Note that these are equivalent:
        #   a[:]
        #   a[s_[:]]
        #   a[slice(None)]
        #   a[slice(None, None, None)]
        #   a[slice(0, None, None)]
        slices = [slice(None)] * a.ndim
        slices[axis] = sl
    # a[...] can take a tuple or list of slice objects
    # a[x:y:z, i:j:k] is the same as
    # a[(slice(x,y,z), slice(i,j,k))] == a[[slice(x,y,z), slice(i,j,k)]]
    slices = tuple(slices)
    if copy:
        return a[slices].copy()
    else:
        return a[slices]


def __enh_sum(arr, axis=None, keepdims=False, **kwds):
    """This numpy.sum() with some features implemented which can be found in
    numpy v1.7 and later: `axis` can be a tuple to select arbitrary axes to sum
    over.

    We also have a `keepdims` keyword, which however works completely different
    from numpy. Docstrings shamelessly stolen from numpy and adapted here
    and there.

    Parameters
    ----------
    arr : nd array
    axis : None or int or tuple of ints, optional
        Axis or axes along which a sum is performed. The default (`axis` =
        `None`) is to perform a sum over all the dimensions of the input array.
        `axis` may be negative, in which case it counts from the last to the
        first axis.
        If this is a tuple of ints, a sum is performed on multiple
        axes, instead of a single axis or all the axes as before.
    keepdims : bool, optional
        If this is set to True, the axes from `axis` are left in the result
        and the reduction (sum) is performed for all remaining axes. Therefore,
        it reverses the `axis` to be summed over.
    **kwds : passed to np.sum().

    Examples
    --------
    >>> a=rand(2,3,4)
    >>> num.sum(a)
    12.073636268676152
    >>> a.sum()
    12.073636268676152
    >>> num.sum(a, axis=1).shape
    (2, 4)
    >>> num.sum(a, axis=(1,)).shape
    (2, 4)
    >>> # same as axis=1, i.e. it inverts the axis over which we sum
    >>> num.sum(a, axis=(0,2), keepdims=True).shape
    (2, 4)
    >>> # numpy's keepdims has another meaning: it leave the summed axis (0,2)
    >>> # as dimension of size 1 to allow broadcasting
    >>> numpy.sum(a, axis=(0,2), keepdims=True).shape
    (1, 3, 1)
    >>> num.sum(a, axis=(1,)) - num.sum(a, axis=1)
    array([[ 0.,  0.,  0.,  0.],
           [ 0.,  0.,  0.,  0.]])
    >>> num.sum(a, axis=(0,2)).shape
    (3,)
    >>> num.sum(a, axis=(0,2)) - a.sum(axis=0).sum(axis=1)
    array([ 0.,  0.,  0.])
    """

    # Recursion rocks!
    def _sum(arr, tosum):
        if len(tosum) > 0:
            # Choose axis to sum over, remove from list w/ remaining axes.
            axis = tosum.pop(0)
            _arr = arr.sum(axis=axis)
            # arr has one dim less now. Rename remaining axes accordingly.
            _tosum = [xx - 1 if xx > axis else xx for xx in tosum]
            return _sum(_arr, _tosum)
        else:
            return arr

    axis_is_int = isinstance(axis, int)
    if axis is None:
        if keepdims:
            raise Exception("axis=None + keepdims=True makes no sense")
        else:
            return np.sum(arr, axis=axis, **kwds)
    elif axis_is_int and not keepdims:
        return np.sum(arr, axis=axis, **kwds)
    else:
        if axis_is_int:
            tosum = [axis]
        elif isinstance(axis, tuple) or isinstance(axis, list):
            tosum = list(axis)
        else:
            raise Exception("illegal type for axis: %s" % str(type(axis)))
        if keepdims:
            alldims = range(arr.ndim)
            tosum = [xx for xx in alldims if xx not in tosum]
        return _sum(arr, tosum)


def __mirror(arr, axis=0):
    """Mirror array `arr` at index 0 along `axis`.
    The length of the returned array is 2*arr.shape[axis]-1 ."""
    return np.concatenate((arr[::-1], arr[1:]), axis=axis)


def __welch(M, sym=1):
    """Welch window. Function skeleton shamelessly stolen from
    scipy.signal.windows.bartlett() and others."""
    if M < 1:
        return np.array([])
    if M == 1:
        return np.ones(1, dtype=float)
    odd = M % 2
    if not sym and not odd:
        M = M + 1
    n = np.arange(0, M)
    w = 1.0 - ((n - 0.5 * (M - 1)) / (0.5 * (M - 1))) ** 2.0
    if not sym and not odd:
        w = w[:-1]
    return w


def __norm_int(y, x, area=1.0, scale=True, func=simps):
    """Normalize integral area of y(x) to `area`.

    Parameters
    ----------
    x,y : numpy 1d arrays
    area : float
    scale : bool, optional
        Scale x and y to the same order of magnitude before integration.
        This may be necessary to avoid numerical trouble if x and y have very
        different scales.
    func : callable
        Function to do integration (like scipy.integrate.{simps,trapz,...}
        Called as ``func(y,x=x)``. Default: simps

    Returns
    -------
    scaled y

    Notes
    -----
    The argument order y,x might be confusing. x,y would be more natural but we
    stick to the order used in the scipy.integrate routines.
    """
    if scale:
        fx = np.abs(x).max()
        fy = np.abs(y).max()
        sx = x / fx
        sy = y / fy
    else:
        fx = fy = 1.0
        sx, sy = x, y
    # Area under unscaled y(x).
    _area = func(sy, x=sx) * fx * fy
    return y * area / _area
