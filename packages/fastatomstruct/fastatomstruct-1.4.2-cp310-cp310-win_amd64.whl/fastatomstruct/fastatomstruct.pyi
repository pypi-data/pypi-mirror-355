from typing import List, Tuple, Union, Optional

import ase
import fastatomstruct
import numpy as np

class FilterTag:
    """Filter atoms based on tags.

    On creation of a :code:`Filter`, you have to specify which atoms
    should be regarded as "center" atoms and as "other" atoms, respectively.
    Atoms that have a tag other than :code:`center` or :code:`other`
    will be disregarded. The last argument (:code:`center_is_other`, a boolean)
    specifies whether "center" atoms should also be regarded as "other" atoms.

    Examples
    --------

    Suppose that we have a NaCl system and want to calculate the **partial
    Na-Na, Na-Cl and Cl-Cl pair correlation functions**. This can be achieved
    by first tagging all Cl atoms with tag 1:

    >>> from ase.build import bulk
    >>> a = 5.64
    >>> nacl = bulk("NaCl", "rocksalt", a=a) * (5, 5, 5)
    >>> nacl.rattle()
    >>> tags = nacl.get_tags()
    >>> tags[nacl.numbers == 17] = 1
    >>> nacl.set_tags(tags)

    For the partial Na-Cl correlation function, we can then use
    :code:`Filter(0, 1, False)`:

    >>> import fastatomstruct as fs
    >>> r_na_cl, rdf_na_cl = fs.radial_distribution_function(
    >>>     nacl, 10, 200, fs.FilterTag(0, 1, False)
    >>> )

    Analogously, the Na-Na pair correlation function is

    >>> import fastatomstruct as fs
    >>> r_na_na, rdf_na_na = fs.radial_distribution_function(
    >>>     nacl, 10, 200, fs.FilterTag(0, 0, False)
    >>> )

    The :code:`center_is_other` argument will not matter in this case.

    Now suppose you want to calculate the **partial three-body correlation**
    around the Na atoms (including atoms of any kind around those atoms).
    This can be achieved as follows:

    >>> tbc = fs.tbc(nacl, 3, 10, 250, fs.Filter(0, 1, True)))
    """

    ...

class FilterElement:
    """Filter atoms based on elements.

    On creation of a `FilterElement`, you have to specify which atoms
    should be regarded as "center" atoms and as "other" atoms, respectively.
    Atoms that have an element other than `center` or `other`
    will be disregarded. The last argument (`center_is_other`, a boolean)
    specifies whether "center" atoms should also be regarded as "other" atoms.

    Examples
    --------

    Suppose that we have a NaCl system and want to calculate the **partial
    Na-Na, Na-Cl and Cl-Cl pair correlation functions**. This can be achieved
    as follows:

    >>> from ase.build import bulk
    >>> a = 5.64
    >>> nacl = bulk("NaCl", "rocksalt", a=a) * (5, 5, 5)
    >>> nacl.rattle()
    >>> filter = fs.FilterElement(fs.Element.Na, fs.Element.Cl, False)
    >>> r_na_cl, rdf_na_cl = fs.radial_distribution_function(
    >>>     nacl, 10, 200, filter
    >>> )
    >>> filter = fs.FilterElement(fs.Element.Na, fs.Element.Na, False)
    >>> r_na_na, rdf_na_na = fs.radial_distribution_function(
    >>>     nacl, 10, 200, filter
    >>> )

    The `center_is_other` argument will not matter in this case.

    Now suppose you want to calculate the **partial three-body correlation**
    around the Na atoms (including atoms of any kind around those atoms).
    This can be achieved as follows:

    >>> tbc = fs.tbc(nacl, 3, 10, 250, fs.FilterElement(fs.Element.Na, fs.Element.Cl, True))
    """

    ...

from enum import Enum

class Element(Enum):
    """Enum representing chemical elements.

    The :code:`Element` enum represents chemical elements. It can be used
    to filter atoms based on their element. All chemical elements can be accessed
    (e.g. :code:`Element.H`, :code:`Element.He`, etc.). There is also a special element
    :code:`Element.Undefined` that can be used to filter atoms with an undefined element.
    """

    ...

class Atom:
    """Represents an atom with its position, element, velocity, and tag.

    An Atom object contains all the information about a single atom, including its position,
    element type, velocity (if available), and tag.

    Arguments:
        position (np.ndarray): Array of shape (3,) representing the position of the atom
        element (Element): Chemical element of the atom
        velocity (np.ndarray, optional): Array of shape (3,) representing the velocity of the atom
        tag (int, optional): Tag for the atom, can be used for filtering or grouping atoms

    Examples
    --------

    >>> import fastatomstruct as fs
    >>> import numpy as np
    >>> position = np.array([0.0, 0.0, 0.0])
    >>> element = fs.Element.H
    >>> velocity = np.array([1.0, 0.0, 0.0])
    >>> tag = 1
    >>> atom = fs.Atom(position, element, velocity, tag)
    """

    ...

class Atoms:
    """A collection of atoms with associated cell and properties.

    The `Atoms` class represents a collection of atoms with associated cell dimensions
    and optional properties like velocities and stress tensor. It provides methods for
    accessing and manipulating atomic positions, velocities, elements, and cell parameters.

    Examples
    --------

    Create a simple hydrogen molecule:

    >>> import fastatomstruct as fs
    >>> import numpy as np
    >>> positions = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.74]])
    >>> cell = np.eye(3) * 10.0
    >>> elements = [fs.Element.H, fs.Element.H]
    >>> atoms = fs.Atoms(positions, cell, elements)

    Get and set positions:

    >>> pos = atoms.get_positions()
    >>> pos[0] = [1.0, 0.0, 0.0]
    >>> atoms.set_positions(pos)

    Set velocities:

    >>> vel = np.zeros_like(positions)
    >>> vel[0] = [0.1, 0.0, 0.0]
    >>> atoms.set_velocities(vel)

    Get elements and cell:

    >>> elements = atoms.get_elements()
    >>> cell = atoms.get_cell()

    Calculate properties:

    >>> from fastatomstruct import FilterNone
    >>> filter_none = FilterNone()
    >>> temperature = atoms.temperature(filter_none)
    >>> volume = atoms.volume()
    >>> density = atoms.density(filter_none)
    """

    ...

class Element:
    """Element class representing chemical elements with their properties.

    This class provides methods to access the properties of elements such as their atomic number, mass, covalent radius, and van der Waals radius.
    It also includes methods for converting elements to strings and retrieving their Jmol colors.

    Examples
    --------

    .. plot::
       :include-source: True
       :context: reset

       >>> import fastatomstruct as fs
       >>> hydrogen = fs.Element.H
       >>> print(str(hydrogen))
       >>> print(hydrogen.get_covalent_radius())
       >>> print(hydrogen.get_vdw_radius())
       >>> print(hydrogen.get_jmol_color())
    """

class GenericParticle:
    """A generic particle implementation with custom name and mass.

    This struct provides a flexible way to represent particles that are not
    included in the predefined `Element` enum. It's useful for custom atom types,
    virtual sites, or other simulation entities.

    Examples
    --------

    >>> from fastatomstruct import Atoms, GenericParticle
    >>> custom_particle = GenericParticle("Dummy", 12.0)
    """

class TimeAxis:
    """An enum representing a time axis for iterating over items.

    The :code:`TimeAxis` enum represents a time axis for iterating over a slice of items.
    It can be either :code:`Linear` or :code:`Logarithmic`, with the latter increasing the
    time step exponentially with each iteration.

    Variants
    --------

    - `Linear(float)` - A linear time axis with a constant time step.
    - `Logarithmic(float)` - A logarithmic time axis with an initial time step.

    Examples
    --------

    >>> from fastatomstruct import TimeAxis
    >>> linear = TimeAxis.Linear(1.0)
    >>> log = TimeAxis.Logarithmic(1.0)
    """

    ...

class CutoffMode:
    """Represents the cutoff mode for distance calculations.

    This enum allows for different strategies to determine the cutoff distance
    between atoms based on their elements or tags.

    Attributes:

        Fixed (float): Single default cutoff for all atom pairs.
        Elements (dict): One cutoff per element, with a fallback.
        Tags (dict): One cutoff per tag, with a fallback.
        PairElements (dict): One cutoff per pair of elements, with a fallback.
        PairTags (dict): One cutoff per pair of tags, with a fallback.
        CovalentRadiiScaled (float): Covalent radii scaled by a factor.
        VdWRadiiScaled (float): Van der Waals radii scaled by a factor.

    Examples
    --------

    .. plot::

       >>> from fastatomstruct import Element
       >>> from fastatomstruct import CutoffMode
       >>> element_map = {Element.H: 1.0, Element.O: 1.5}
       >>> cutoff_mode = CutoffMode.Elements(map=element_map, fallback=2.0)
       >>> cutoff_mode = CutoffMode.Fixed(2.0)
       >>> cutoff_mode = CutoffMode.PairElements(map={(Element.H, Element.O): 1.0}, fallback=2.0)
    """

    ...

def convert_ase(atoms: ase.Atoms) -> fastatomstruct.Atoms:
    """Convert an ASE (Atomic Simulation Environment) atoms object to a fastatomstruct Atoms object.

    This function takes an ASE atoms object from Python and converts it into the
    internal PyAtoms representation used by this library. The conversion extracts
    atomic positions, velocities, forces, cell parameters, and other relevant
    properties from the ASE object and creates a corresponding PyAtoms instance.

    Arguments:
        atoms (ase.Atoms): An ASE atoms object containing atomic structure information.

    Returns:
        An Atoms object containing the converted atomic structure data.

    Raises
    ------

    If the conversion fails due to missing or invalid data in the ASE object.

    Examples
    --------

    .. plot::

       >>> import ase
       >>> from fastatomstruct import convert_ase
       >>> atoms = ase.Atoms('H2O', positions=[[0, 0, 0], [0, 0.757, 0.587], [0, -0.757, 0.587]])
       >>> fs_atoms = convert_ase(atoms)
       >>> print(fs_atoms)

    """
    ...

def get_num_threads() -> int:
    """Get the current number of threads used by the Rayon thread pool.

    This function returns the number of threads currently configured for
    parallel computation in the Rayon thread pool. This includes both
    active worker threads and the main thread. The thread count affects
    the parallelization of computational tasks throughout the library.

    Returns:
        The current number of threads in the Rayon thread pool.

    Examples
    --------

    .. plot::

       >>> from fastatomstruct import get_num_threads
       >>> num_threads = get_num_threads()
       >>> print(f"Current number of threads: {num_threads}")

    """
    ...

def set_num_threads(num_threads: int):
    """Set the number of threads for the Rayon thread pool.

    This function configures the number of threads used for parallel computation.
    If the global thread pool has not been initialized yet, it creates a new
    global thread pool with the specified number of threads.
    Note that once Rayon's global thread pool is initialized, it cannot be
    reconfigured. This means that this function must be called before
    any parallel computations are performed!

    Arguments:
        num_threads (int): The desired number of threads for parallel computation. Must be greater than 0. Typically set to the number of CPU cores available.

    Examples
    --------

    >>> from fastatomstruct import get_num_threads, set_num_threads
    >>> set_num_threads(4)  # Set the number of threads to 4
    >>> print(f"Number of threads set to: {get_num_threads()}")

    """
    ...

def q_l_global(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    l: int,
    cutoff: fastatomstruct.CutoffMode,
    p_1: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> float:
    """Implementation of the global bond orientational parameter.

    The global bond orientational parameter :math:`Q_l` (as first introduced
    in :cite:t:`steinhardtBondorientationalOrderLiquids1983`) is defined as :cite:`ronnebergerComputationalStudyCrystallization2016a`

    .. math::

        Q_l = \sqrt{\frac{4\pi}{2l + 1}} \sum_{m = -l}^l \left|\frac{1}{N} \sum_i q_{lm}(i)\right|^2,

    with :math:`q_{lm}(i)` the local average of spherical harmonics, which are in
    turn defined as

    .. math::

        q_{lm}(i) = \frac{1}{N_i} \sum_j f(\vec{r}_{ij}) Y_{lm}(\hat{\vec{r}}_{ij}),

    where :math:`\hat{r}_{ij}` denotes the normalized distance vector between
    atoms :math:`i` and :math:`j`. :math:`r_\mathrm{cut}`, :math:`p_1` and :math:`p_2` are parameters
    for the radial cutoff function :math:`f`, which is defined as

    .. math::

        f(r) = \frac{1 - (r / r_c)^{p_1}}{1 - (r / r_c)^{p_2}}.

    For :math:`p_1 \rightarrow \infty` and :math:`p_2 \rightarrow \infty`, this function
    becomes a sharp cutoff.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        l (int): Angular momentum index
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        p_1 (int): First exponent of the cutoff function (second exponent is double the first exponent)
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        float, value of :math:`Q_l`

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    >>> import fastatomstruct as fs
    >>> from ase import io
    >>> atoms = io.read("Sb540.traj")
    >>> fs.q_l_global(atoms, 4, 3.2, 48)
    15.470256244398556
    """
    ...

def q_l(
    atoms: ase.Atoms,
    l: int,
    cutoff: fastatomstruct.CutoffMode,
    p_1: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """The local bond orientational parameter is defined as :cite:`ronnebergerComputationalStudyCrystallization2016a`

    .. math::

        q_l(i) = \sqrt{\frac{4\pi}{2l + 1} \sum_{m=-l}^l \left|q_{lm}\right|^2},

    with :math:`q_{lm}(i)` the local average of spherical harmonics, which are in
    turn defined as

    .. math::

        q_{lm}(i) = \frac{1}{N_i} \sum_j f(r_{ij}) Y_{lm}(\hat{\vec{r}}_{ij}),

    where :math:`\hat{r}_{ij}` denotes the normalized distance vector between
    atoms :math:`i` and :math:`j`. :math:`r_\mathrm{cut}`, :math:`p_1` and :math:`p_2` are parameters
    for the radial cutoff function :math:`f`, which is defined as

    .. math::

        f(r) = \frac{1 - (r / r_c)^{p_1}}{1 - (r / r_c)^{p_2}}.

    For :math:`p_1 \rightarrow \infty` and :math:`p_2 \rightarrow \infty`, this function
    becomes a sharp cutoff.

    Arguments:
        atoms (ase.Atoms): Atoms object(s) from ASE
        l (int): Angular momentum index
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        p_1 (int): First exponent of the cutoff function (second exponent is double the first exponent)
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        np.typing.NDArray of floats, values of :math:`q_l`

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb540.traj")
       >>> cutoff = fs.CutoffMode.Fixed(3.2)
       >>> q_l = fs.q_l(atoms, 4, cutoff, 48)
       >>> plt.hist(q_l, bins=25)
       >>> plt.xlabel(r"$q_4$")
       >>> plt.ylabel("Frequency")

    """
    ...

def q_l_dot(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    l: int,
    cutoff: fastatomstruct.CutoffMode,
    p_1: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """ "Bond order correlation" here is a term for the correlation between
    bond orientional parameters. It is defined as :cite:`ronnebergerComputationalStudyCrystallization2016a`

    .. math::

        \dot{q}_l(i) = \frac{1}{N_i^\mathrm{eff}} \sum_{j} f(r_{ij}) C_{ij},

    where :math:`N_i^\mathrm{eff}` is the effective coordination number

    .. math::

        N_i^\mathrm{eff} = \sum_j f(r_{ij}).

    Here,

    .. math::

        C_{ij} = \sum_{m = -l}^l \frac{q_{lm}(i) \, q_{lm}^*(j)}{\sqrt{\sum_m \left|q_{lm}(i)\right|^2} \, \sqrt{\sum_m \left|q_{lm}(j)\right|^2}}

    are the bond order correlators :cite:`tenwoldeNumericalEvidenceBcc1995a`,
    with :math:`q_{lm}(i)` the local average of
    spherical harmonics. These are in turn defined as

    .. math::

        q_{lm}(i) = \frac{1}{N_i} \sum_j f(r_{ij}) Y_{lm}(\hat{\vec{r}}_{ij}),

    where :math:`\hat{r}_{ij}` denotes the normalized distance vector between
    atoms :math:`i` and :math:`j`. :math:`r_\mathrm{cut}`, :math:`p_1` and :math:`p_2` are parameters
    for the radial cutoff function :math:`f`, which is defined as

    .. math::

        f(r) = \frac{1 - (r / r_c)^{p_1}}{1 - (r / r_c)^{p_2}}.

    For :math:`p_1 \rightarrow \infty` and :math:`p_2 \rightarrow \infty`, this function
    becomes a sharp cutoff.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        l (int): Angular momentum index
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        p_1 (int): First exponent of the cutoff function (second exponent is double the first exponent)
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        np.typing.NDArray of floats, values of :math:`q_l`

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb540.traj")
       >>> cutoff = fs.CutoffMode.Fixed(3.2)
       >>> qdot = fs.q_l_dot(atoms, 4, cutoff, 48)
       >>> plt.hist(qdot, bins=25)
       >>> plt.xlabel(r"$\dot{q}_4$")
       >>> plt.ylabel("Frequency")

    """
    ...

def q_tetrahedral(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    cutoff: fastatomstruct.CutoffMode,
    n_neighbours: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """The tetrahedral order parameter is defined as :cite:`duboue-dijonCharacterizationLocalStructure2015a`

    .. math::

        q = 1 - \frac{3}{8} \sum_{i > k} \left(\frac{1}{3} + \theta_{ijk}\right)^2,

    where the sum runs over all pairs of atoms bonded to a central atom :math:`j` and
    forming a bond angle :math:`\theta_{ijk}`. The parameter is calculated
    for a fixed number of nearest neighbours.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        n_neighbours (int): Number of nearest neighbours
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        np.typing.NDArray of floats, values of :math:`q`

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb540.traj")
       >>> cutoff = fs.CutoffMode.Fixed(3.2)
       >>> q_tetrahedral = fs.q_tetrahedral(atoms, cutoff, 4)
       >>> plt.hist(q_tetrahedral, bins=25)
       >>> plt.xlabel(r"$q_\mathrm{tetrahedral}$")
       >>> plt.ylabel("Frequency")

    """
    ...

def bond_length_ratio(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    r_min: float,
    r_max: float,
    cutoff_angle: float,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """The angular limited bond length ratio is defined as :cite:`holleImportanceDensityPhaseChange2025`

    .. math::

        \mathrm{ALBLR} = \frac{\sum\limits_{i_1, i_2, i_3} \frac{\mathrm{max}(r_{12}, r_{23})}{\mathrm{min}(r_{12}, r_{23})} \, \Theta(\beta - \delta) \, \bar\Theta(r_{12}) \, \bar\Theta(r_{23})}{\sum\limits_{i_1, i_2, i_3} \Theta(\beta - \delta) \, \bar\Theta(r_{12}) \, \bar\Theta(r_{23})},

    with :math:`i_1`, :math:`i_2` and :math:`i_3` distinct indices of atoms, and

    .. math::

        \cos\beta = \frac{\vec{r}_{i_1 i_2} \cdot \vec{r}_{i_2 i_3}}{r_{i_1 i_2} r_{i_2 i_3}}

    the alignment angle and :math:`\delta` and angular threshold (typically 25° in
    phase-change materials).

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object from ASE
        include_atoms (np.typing.NDArray): atoms to include, boolean array of length n
        only_atoms (bool): whether to include only the atoms indicated in
                           include_atoms. If False, the second and third atom
                           in the ALTBC calculation can be of any kind.
        r_min (float): Minimum radius to consider
        r_max (float): Maximum radius to consider
        cutoff_angle (float): Cutoff angle :math:`\delta` in degrees.
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        float, average bond length ratio

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    >>> import fastatomstruct as fs
    >>> from ase import io
    >>> atoms = io.read("Sb540.traj")
    >>> fs.bond_length_ratio(atoms, 2.5, 4, 25)
    1.1065865743550205
    """
    ...

def bond_length_ratio_list(
    atoms: ase.Atoms,
    r_min: float,
    r_max: float,
    cutoff_angle: float,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """(Angular limited) bond length ratio for each set of atoms.

    The angular limited bond length ratio for a triplet of atoms
    :math:`i_1`, :math:`i_2`, and :math:`i_3` is defined as :cite:`holleImportanceDensityPhaseChange2025`

    .. math::

        \mathrm{ALBLR} = \frac{\sum\limits_{i_1, i_2, i_3} \frac{\mathrm{max}(r_{12}, r_{23})}{\mathrm{min}(r_{12}, r_{23})} \, \Theta(\beta - \delta) \, \bar\Theta(r_{12}) \, \bar\Theta(r_{23})}{\sum\limits_{i_1, i_2, i_3} \Theta(\beta - \delta) \, \bar\Theta(r_{12}) \, \bar\Theta(r_{23})},

    with :math:`i_1`, :math:`i_2` and :math:`i_3` distinct indices of atoms, and

    .. math::

        \cos\beta = \frac{\vec{r}_{i_1 i_2} \cdot \vec{r}_{i_2 i_3}}{r_{i_1 i_2} r_{i_2 i_3}}

    the alignment angle and :math:`\delta` and angular threshold (typically 25° in
    phase-change materials).

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        r_min (float): Minimum radius to consider
        r_max (float): Maximum radius to consider
        cutoff_angle (float): Cutoff angle :math:`\delta` in degrees.
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        For each atom :math:`i_2`, a list of tuples
        :math:`(i_1, i_3, r_{i_1, i_2}, r_{i_2, i_3}, \frac{\mathrm{max}(r_{i_1, i_2}, r_{i_2, i_3})}{\mathrm{min}(r_{i_1, i_2}, r_{i_2, i_3})})`
        is returned (under the restrictions described above).

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb540.traj")
       >>> blr_list = fs.bond_length_ratio_list(atoms, 2.2, 3.6, 25.0)
       >>> blrs = []
       >>> for blr_temp in blr_list:
       >>>     if len(blr_temp) > 0:
       >>>         for blr in blr_temp:
       >>>             blrs.append(blr[-1])
       >>> plt.hist(blrs, bins=50)
       >>> plt.xlabel("Bond length ratio")
       >>> plt.ylabel("Frequency")

    """
    ...

def altbc(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    r_min: float,
    r_max: float,
    n_r: int,
    cutoff_angle: float,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """The Angular-limited three-body correlation (ALTBC) :cite:`bicharaPropertiesLiquidGroupV1993`
    is a higher-order correlation function that includes three atoms.
    It is defined as :cite:`ronnebergerComputationalStudyCrystallization2016a`

    .. math::

        g^{(3)}(r_1, r_2) = \frac{V}{\rho (N - 1)(N - 2)} \sum_{i_1, i_2, i_3} \langle\delta(r_1 - r_{i_1 i_2}) \delta(r_2 - r_{i_2 i_3}) \Theta(\beta - \delta)\rangle,

    with :math:`i_1`, :math:`i_2` and :math:`i_3` distinct indices of atoms, :math:`V` the unit cell
    volume, :math:`N` the number of particles, :math:`\rho = V/N`
    the atomic density, and

    .. math::

        \cos\beta = \frac{\vec{r}_{i_1 i_2} \cdot \vec{r}_{i_2 i_3}}{r_{i_1 i_2} r_{i_2 i_3}}

    the alignment angle and :math:`\delta` an angular threshold (typically
    25° in phase-change materials).

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        cell (np.typing.NDArray): unit cell array, shape is 3x3
        r_min (float): minimum radius / atomic distance
        r_max (float): maximum radius / atomic distance
        n_r (int): number of bins for each :math:`r`
        cutoff_angle (float): maximum bond angle in degrees
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        2D array of shape `(n_r, n_r)` containing the ALTBC

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":10")
       >>> altbc = fs.altbc(atoms, 2.5, 4.5, 100, 25)
       >>> plt.imshow(altbc, aspect="auto", origin="lower", extent=[2.5, 4.5, 2.5, 4.5], cmap="turbo")
       >>> plt.colorbar(label="ALTBC")
       >>> plt.xlabel(r"$r_1$ $(\mathrm{\AA})$")
       >>> plt.ylabel(r"$r_2$ $(\mathrm{\AA})$")

    """
    ...

def tbc(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    r_min: float,
    r_max: float,
    n_r: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """The three-body correlation (TBC) is a higher-order correlation function
    that includes three atoms. It is defined as :cite:`ronnebergerComputationalStudyCrystallization2016a`

    .. math::

        g^{(3)}(r_1, r_2) = \frac{V}{\rho (N - 1)(N - 2)} \sum_{i_1, i_2, i_3} \langle\delta(r_1 - r_{i_1 i_2}) \delta(r_2 - r_{i_2 i_3})\rangle,

    with :math:`i_1`, :math:`i_2` and :math:`i_3` distinct indices of atoms, :math:`V` the unit cell
    volume, :math:`N` the number of particles, and :math:`\rho = V/N` the atomic density.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        r_min (float): minimum radius / atomic distance
        r_max (float): maximum radius / atomic distance
        n_r (int): number of bins for each :math:`r`
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        2D array of shape (n_r, n_r) containing the TBC

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":10")
       >>> tbc = fs.tbc(atoms, 2.5, 4.5, 100)
       >>> plt.imshow(tbc, aspect="auto", origin="lower", extent=[2.5, 4.5, 2.5, 4.5], cmap="turbo")
       >>> plt.colorbar(label="ALTBC")
       >>> plt.xlabel(r"$r_1$ $(\mathrm{\AA})$")
       >>> plt.ylabel(r"$r_2$ $(\mathrm{\AA})$")

    """
    ...

def angular_three_body_correlation(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    central_selection: NeighbourSelectionCriteria,
    neighbour_cutoff: float,
    r_min: float,
    r_max: float,
    beta_min: float,
    beta_max: float,
    n_r: int,
    n_beta: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Computes the extended three-body correlation (ETBC) for a set of atoms.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        central_selection (NeighbourSelectionCriteria): Criteria for selecting neighbours of the central atom
        neighbour_cutoff (float): Cutoff distance for neighbours of the first neighbours
        r_min (float): Minimum radius to consider for histograms
        r_max (float): Maximum radius to consider for histograms
        beta_min (float): Minimum angle in degrees to consider
        beta_max (float): Maximum angle in degrees to consider
        n_r (int): Number of bins for the distance axis
        n_beta (int): Number of bins for the angle axis
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Tuple[np.typing.NDArray, np.typing.NDArray]: Two 2D arrays representing the ETBC histograms

    """
    ...

def temporal_altbc(
    atoms_series: List[ase.Atoms],
    r_min: float,
    r_max: float,
    n_bins: int,
    cutoff_angle: float,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> List[np.typing.NDArray]:
    """Computes the temporal angular-limited three-body correlation (TALTBC) for a set of atoms over time.

    This function calculates how angular-limited three-body correlations evolve over time
    relative to the initial structure at t0. It extends the ALTBC function to track temporal
    evolution, incorporating the angular limitation in both space and time.

    Arguments:
        atoms_series (List[ase.Atoms]): List of Atoms objects from ASE representing timesteps
        r_min (float): minimum radius / atomic distance
        r_max (float): maximum radius / atomic distance
        n_bins (int): number of bins for the histogram
        cutoff_angle (float): maximum bond angle in degrees
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        List[np.typing.NDArray]: List of 2D arrays with shape (n_bins, n_bins) containing the TALTBC at each timestep

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms_series = io.read("Sb-1.00-300-100.traj", index=":3")
       >>> taltbc_results = fs.temporal_altbc(atoms_series, 2.5, 4.5, 50, 25, None)
       >>> fig, axes = plt.subplots(1, len(taltbc_results), figsize=(15, 5))
       >>> for i, (ax, taltbc) in enumerate(zip(axes, taltbc_results)):
       >>>     im = ax.imshow(taltbc, aspect="auto", origin="lower", extent=[2.5, 4.5, 2.5, 4.5], cmap="turbo")
       >>>     ax.set_title(f"Timestep {i}")
       >>>     ax.set_xlabel(r"$r_1$ $(\mathrm{\AA})$")
       >>>     if i == 0:
       >>>         ax.set_ylabel(r"$r_2$ $(\mathrm{\AA})$")
       >>> plt.colorbar(im, ax=axes.ravel().tolist(), label="TALTBC")

    """
    ...

def temporal_tbc(
    atoms_series: List[ase.Atoms],
    r_min: float,
    r_max: float,
    n_r: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> List[np.typing.NDArray]:
    """Computes the temporal three-body correlation (TTBC) for a set of atoms over time.

    This function calculates how three-body correlations evolve over time relative to
    the initial structure at t0. For each timestep t, it computes correlations between
    atom triplets (i1, i2, i3) and compares with their initial configuration.

    Arguments:
        atoms_series (List[ase.Atoms]): List of Atoms objects from ASE representing timesteps
        r_min (float): minimum radius / atomic distance
        r_max (float): maximum radius / atomic distance
        n_r (int): number of bins for each :math:`r`
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        List[np.typing.NDArray]: List of 2D arrays with shape (n_r, n_r) containing the TTBC at each timestep

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> import numpy as np
       >>> atoms_series = io.read("Sb-1.00-300-100.traj", index=":3")
       >>> ttbc_results = fs.temporal_tbc(atoms_series, 2.5, 4.5, 50, None)
       >>> fig, axes = plt.subplots(1, len(ttbc_results), figsize=(15, 5))
       >>> for i, (ax, ttbc) in enumerate(zip(axes, ttbc_results)):
       >>>     im = ax.imshow(ttbc, aspect="auto", origin="lower", extent=[2.5, 4.5, 2.5, 4.5], cmap="turbo")
       >>>     ax.set_title(f"Timestep {i}")
       >>>     ax.set_xlabel(r"$r_1$ $(\mathrm{\AA})$")
       >>>     if i == 0:
       >>>         ax.set_ylabel(r"$r_2$ $(\mathrm{\AA})$")
       >>> plt.colorbar(im, ax=axes.ravel().tolist(), label="TTBC")

    """
    ...

def temporal_angular_three_body_correlation(
    atoms_series: List[ase.Atoms],
    central_selection: NeighbourSelectionCriteria,
    neighbour_cutoff: float,
    r_min: float,
    r_max: float,
    beta_min: float,
    beta_max: float,
    n_r: int,
    n_beta: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> Tuple[List[np.typing.NDArray], List[np.typing.NDArray]]:
    """Computes the temporal extended three-body correlation (TETBC) for a set of atoms over time.

    This function tracks how extended three-body correlations evolve over time relative to the
    initial structure. It builds upon the `angular_three_body_correlation` function to capture
    the temporal evolution of angular and distance relationships.

    Arguments:
        atoms_series (List[ase.Atoms]): List of Atoms objects from ASE representing timesteps
        central_selection (NeighbourSelectionCriteria): Criteria for selecting neighbours of the central atom
        neighbour_cutoff (float): Cutoff distance for neighbours of the first neighbours
        r_min (float): Minimum radius to consider for histograms
        r_max (float): Maximum radius to consider for histograms
        beta_min (float): Minimum angle in degrees to consider
        beta_max (float): Maximum angle in degrees to consider
        n_r (int): Number of bins for the distance axis
        n_beta (int): Number of bins for the angle axis
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Tuple[List[np.typing.NDArray], List[np.typing.NDArray]]: Two lists of 2D arrays representing the temporal evolution of ETBC histograms

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> from fastatomstruct import NeighbourSelectionCriteria
       >>> atoms_series = io.read("Sb-1.00-300-100.traj", index=":3")
       >>> criteria = NeighbourSelectionCriteria.NNearest(4)
       >>> hist_r2_time, hist_r2_prime_time = fs.temporal_angular_three_body_correlation(
       >>>     atoms_series, criteria, 3.5, 2.5, 4.5, 0.0, 180.0, 20, 18, None
       >>> )
       >>> # Plot first histogram type (angle vs r2) for first timestep
       >>> plt.figure(figsize=(10, 6))
       >>> plt.imshow(hist_r2_time[0], aspect="auto", origin="lower",
       >>>            extent=[2.5, 4.5, 0, 180], cmap="turbo")
       >>> plt.colorbar(label="TETBC (angle vs r2)")
       >>> plt.xlabel(r"Distance $r_2$ $(\mathrm{\AA})$")
       >>> plt.ylabel(r"Angle $\beta$ (degrees)")
       >>> plt.title("Temporal Extended Three-Body Correlation - Timestep 0")

    """
    ...

def distances(
    atoms: ase.Atoms,
    i: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Distances of one atom to all other atoms.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        i (int): Index of the atom
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Distances (array of floats) for this atom

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> from ase import io
       >>> atoms = io.read("Sb540.traj")
       >>> distances = fs.distances(atoms, 0)
       >>> plt.hist(distances, bins=25)
       >>> plt.xlabel(r"Distance ($\mathrm{\AA}$)")
       >>> plt.ylabel("Frequency")

    """
    ...

def all_distances(
    atoms: ase.Atoms,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.ndarray:
    """Distances of each atom to all other atoms.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        2D array containing all distances

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("Sb540.traj")
       >>> d = fs.all_distances(atoms)
       >>> plt.imshow(d, origin="lower")
       >>> plt.colorbar(label="Distance ($\mathrm{\AA}$)")
       >>> plt.xlabel("Atom index")
       >>> plt.ylabel("Atom index")

    """
    ...

def r_theta_phi(
    atoms: ase.Atoms,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> List[List]:
    """List of distances and angles of an atom to all other atoms.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        List of three lists (r, theta, and phi)

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb540.traj")
       >>> rtp = fs.r_theta_phi(atoms)
       >>> print(len(rtp))
       >>> fig, ax = plt.subplots(ncols=3)
       >>> ax[0].hist(rtp[0][0], bins=50)
       >>> ax[1].hist(rtp[0][1], bins=50, color="C2")
       >>> ax[2].hist(rtp[0][2], bins=50, color="C2")
       >>> ax[0].set_xlabel(r"$r$")
       >>> ax[1].set_xlabel(r"$\theta$")
       >>> ax[2].set_xlabel(r"$\phi$")
       >>> ax[1].set_ylabel("Frequency")

    """
    ...

def distance_vectors(
    atoms: ase.Atoms,
    i: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Distance vectors between one atom and all other atoms.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        i (int): Atom index
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Distance vectors (2D array of floats) for this atom

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> import matplotlib.pyplot as plt
       >>> atoms = io.read("Sb540.traj")
       >>> d = fs.distance_vectors(atoms, 0)
       >>> print(d)

    """
    ...

def all_distance_vectors(
    atoms: ase.Atoms,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> List[np.typing.NDArray]:
    """Distance vectors between all atoms and all other atoms.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Distance vectors (list of 2D arrays of floats) for all atoms

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> from ase import io
       >>> atoms = io.read("Sb540.traj")
       >>> d = fs.all_distance_vectors(atoms)
       >>> plt.plot([len(dist) for dist in d])
       >>> plt.xlabel("Atom index")
       >>> plt.ylabel("Number of distance vectors")

    """
    ...

def neighbour_lists(
    atoms: ase.Atoms,
    cutoff: fastatomstruct.CutoffMode,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> List[np.typing.NDArray]:
    """List of nearest neighbours for each atom.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        List of 1D arrays

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> from ase import io
       >>> from ase.visualize.plot import plot_atoms
       >>> atoms = io.read("Sb540.traj")
       >>> cutoff = fs.CutoffMode.Fixed(3.6)
       >>> n = fs.neighbour_lists(atoms, cutoff)
       >>> plot_atoms(atoms[0:1], colors=[(1, 0, 0, 1)] * len(atoms))
       >>> plot_atoms(atoms[n[0]], colors=[(0, 0, 0, 0)] * len(atoms))
       >>> plt.xlabel(r"$x$ $(\mathrm{\AA})$")
       >>> plt.ylabel(r"$y$ $(\mathrm{\AA})$")
       >>> plt.tight_layout()

    """
    ...

def find_bonds(
    atoms: ase.Atoms,
    cutoff: fastatomstruct.CutoffMode,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Find bonds between atoms for a given cutoff radius.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        2D array of shape (n_bonds, 2) containing the bonds (indices of the atoms)

    """
    ...

def find_bonds_with_vec(
    atoms: ase.Atoms,
    cutoff: fastatomstruct.CutoffMode,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Find bonds between atoms for a given cutoff radius.

    Arguments:
        atoms (ase.Atoms): Atoms object from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        2D array of shape (n_bonds, 6) containing the bonds (indices of the atoms, columns 1 and 2), distance vectors (columns 3, 4, 5), and absolute distance (column 6)

    """
    ...

def coordination_numbers(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    cutoff: fastatomstruct.CutoffMode,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Coordination number of each atom.

    Currently only supports one cutoff radius.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        1D array of length n containing the coordination numbers

    Examples
    --------

    The exemplary file "Sb540.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb540.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("Sb540.traj")
       >>> coordination_numbers = fs.coordination_numbers(atoms, fs.CutoffMode.Fixed(3.2))
       >>> hist = np.histogram(coordination_numbers, bins=range(1, 9))
       >>> plt.plot(hist[1][:-1], hist[0], "o-")
       >>> plt.xlabel("Coordination number")
       >>> plt.ylabel("Frequency")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def bond_angle_distribution(
    atoms: Union[ase.Atoms, List[ase.Atoms]],
    cutoff: fastatomstruct.CutoffMode,
    n_bins: int,
    filter: Optional[
        Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]
    ] = None,
) -> np.typing.NDArray:
    """Distribution of bond angles.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for neighbour search
        n_bins (int): Number of bins for the bond angle histogram
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        Two 1D arrays of length n_bins containing the bond angles and histogram of bond angles.

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":10")
       >>> cutoff = fs.CutoffMode.Fixed(3.2)
       >>> angles, bad = fs.bond_angle_distribution(atoms, cutoff, 180)
       >>> plt.plot(angles, bad)
       >>> plt.xlabel(r"Bond angle $(\mathrm{degrees})$")
       >>> plt.ylabel("Frequency")
       >>> plt.xlim(0, 180)
       >>> plt.ylim(0)

    """
    ...

def radial_distribution_function(
    atoms: List[ase.Atoms],
    cutoff: fastatomstruct.CutoffMode,
    n_bins: int,
    filter: Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]],
) -> tuple[np.ndarray, np.ndarray]:
    """Radial distribution function (RDF).

    Estimated using a rectangular window function. The RDF is defined as

    .. math::

        g(r) = \frac{d n_r}{4 \pi \rho r^2 dr}.

    Arguments:
        atoms (Union[ase.Atoms, List[ase.Atoms]]): Atoms object(s) from ASE or list of Atoms objects
        cutoff (fastatomstruct.CutoffMode): Cutoff mode defining the range for the RDF computation
        n_bins (int): Number of bins
        filter (Optional[Union[fastatomstruct.FilterTag, fastatomstruct.FilterElement]]): Filter instance

    Returns:
        (1D array of length n_bins containing the radii, 1D array of length n_bins containing the RDF)

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":10")
       >>> cutoff = fs.CutoffMode.Fixed(10.0)
       >>> r, rdf = fs.radial_distribution_function(atoms, cutoff, 100)
       >>> plt.plot(r, rdf)
       >>> plt.xlim(r.min(), r.max())
       >>> plt.ylim(0)
       >>> plt.xlabel(r"r $(\mathrm{\AA})$")
       >>> plt.ylabel(r"$g(r)$")
       >>> plt.tight_layout()

    """
    ...

def mean_squared_displacement_single(
    atoms: List[ase.Atoms], time_axis: fastatomstruct.TimeAxis
) -> np.typing.NDArray:
    """Mean squared displacement (MSD) without temporal averaging.

    The (non-averaged) MSD is defined as

    .. math::

        \mathrm{MSD} = \langle |\vec{x}(t) - \vec{x}(t_0)|^2 \rangle = \frac{1}{N} \sum_{i = 1}^N |\vec{x}^i(t) - \vec{x}^i(t_0)|^2.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two 1D arrays containing time and the MSD

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> t, msd = fs.mean_squared_displacement_single(atoms, fs.TimeAxis.Logarithmic(100))
       >>> plt.loglog(t / 1000, msd)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"Mean squared displacement ($\mathrm{\AA^2}$)")
       >>> plt.tight_layout()

    """
    ...

def squared_displacement_single(
    atoms: List[ase.Atoms], time_axis: fastatomstruct.TimeAxis
) -> np.typing.NDArray:
    """Squared displacement (SD) for each atom without temporal averaging.

    The (non-averaged) SD is defined as

    .. math::

        \mathrm{SD}_i = |\vec{x}^i(t) - \vec{x}^i(t_0)|^2 = |\vec{x}^i(t) - \vec{x}^i(t_0)|^2.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        1D array of length n_times containing the times, 2D array of shape (n_atoms, n_times) containing the SD

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
       >>> time, sd = fs.squared_displacement_single(atoms, fs.TimeAxis.Logarithmic(200))
       >>> for i in range(5):
       >>>     plt.loglog(time / 1000, sd[i])
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"Squared displacement ($\AA^2$)")

    """
    ...

def non_gaussian_alpha2(
    atoms: List[ase.Atoms], time_axis: fastatomstruct.TimeAxis
) -> tuple[np.typing.NDArray, np.typing.NDArray]:
    """(Temporally averaged) non-Gaussian parameter.

    It is defined as

    .. math::

        \alpha_2(t) = \left\langle \frac{3}{5} \frac{\sum_{i = 1}^N |\vec{x}^i(t) - \vec{x}^i(t_0)|^4}{(\sum_{i = 1}^N |\vec{x}^i(t) - \vec{x}^i(t_0)|^2)^2} \right\rangle_{t_0},

    and can be used to identify non-Gaussian behaviour in molecular dynamics.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two 1D arrays containing the times and the non-Gaussian parameter

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
       >>> time, alpha2 = fs.non_gaussian_alpha2(atoms, fs.TimeAxis.Logarithmic(50))
       >>> plt.semilogx(time / 1000, alpha2)
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def non_gaussian_alpha2_single(
    atoms: List[ase.Atoms], time_axis: fastatomstruct.TimeAxis
) -> tuple[np.typing.NDArray, np.typing.NDArray]:
    """(Non-averaged) non-Gaussian parameter.

    It is defined as

    .. math::

        \alpha_2(t) = \frac{3}{5} \frac{\sum_{i = 1}^N |\vec{x}^i(t) - \vec{x}^i(t_0)|^4}{(\sum_{i = 1}^N |\vec{x}^i(t) - \vec{x}^i(t_0)|^2)^2},

    and can be used to identify non-Gaussian behaviour in molecular dynamics.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        1D array of times, 2D array of shape (n_atoms, n_times) containing the non-Gaussian
        parameter each time and atom

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
       >>> time, alpha2 = fs.non_gaussian_alpha2_single(atoms, fs.TimeAxis.Logarithmic(200))
       >>> plt.semilogx(time, alpha2)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"Non-Gaussian parameter $\alpha_2$")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def incoherent_intermediate_scattering(
    atoms: List[ase.Atoms], q: np.typing.NDArray
) -> np.typing.NDArray:
    """This function computes the incoherent intermediate scattering function
    for a given set of atoms and a wave vector. The incoherent intermediate scattering function
    is a measure of the time-dependent density fluctuations in a system, which can be used to
    analyze the dynamics of atomic motion and structural relaxation in materials.
    It is defined as the Fourier transform of the density-density correlation function,
    which describes how the density of atoms at one point in time is correlated with the density
    at another point in time, modulated by a wave vector. In mathematical terms, it is given by:

    .. math::

       F_{\text {incoh }}(\boldsymbol{q}, t) = \frac{1}{N} \sum_i^N\left\langle\exp \left[i \boldsymbol{q} \cdot\left(\boldsymbol{r}_i(t)-\boldsymbol{r}_i(0)\right)\right]\right\rangle

    Arguments:
       atoms (List[ase.Atoms]): List of Atoms objects from ASE
       q (np.typing.NDArray): Wave vector

    Returns:
       1D array of the incoherent intermediate scattering function

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> q = np.array([0., 0., 1.])
       >>> f = fs.incoherent_intermediate_scattering(atoms, q)
       >>> time = np.arange(len(f)) * 100 / 1000
       >>> plt.semilogx(time, f)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Incoherent intermediate scattering function")
       >>> plt.ylim(0, 1)

    """
    ...

def coherent_intermediate_scattering(
    atoms: List[ase.Atoms], q: np.typing.NDArray
) -> np.typing.NDArray:
    """The coherent intermediate scattering function is a measure of the time-dependent
    density fluctuations in a system, specifically focusing on the coherent part of the scattering
    signal. It is defined as the Fourier transform of the coherent density-density correlation function,
    which describes how the density of atoms at one point in time is correlated with the density
    at another point in time, modulated by a wave vector. In mathematical terms, it is given by:

    .. math::

       F_{\text {coh }}(\boldsymbol{q}, t) = \frac{1}{N} \sum_{i \neq j}^N\left\langle\exp \left[i \boldsymbol{q} \cdot\left(\boldsymbol{r}_i(t)-\boldsymbol{r}_j(0)\right)\right]\right\rangle

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        q (np.typing.NDArray): Wave vector

    Returns:
        1D array of the coherent intermediate scattering function

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> q = np.array([0., 0., 1.])
       >>> f = fs.coherent_intermediate_scattering(atoms, q)
       >>> time = np.arange(len(f)) * 100 / 1000
       >>> plt.semilogx(time, f)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Coherent intermediate scattering function")
       >>> plt.ylim(0, 1)

    """
    ...

def overlap_q(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray, np.typing.NDArray, np.typing.NDArray]:
    """Time-averaged overlap parameter.

    It is defined as :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q(t) = \left\langle \sum_{i, j = 1}^N w(|\vec{r}_i(t_0) - \vec{r}_j(t)|) \right\rangle_{t_0}.

    Here, :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.
    The overlap parameter can be split into a self-part

    .. math::

        Q_\mathrm{s}(t) = \left\langle \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|) \right\rangle_{t_0}

    and a distinct part

    .. math::

        Q_\mathrm{d}(t) = \left\langle \sum_{i, j = 1, i \neq j}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|) \right\rangle_{t_0}.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Four arrays of length n_times (time, full q, self part, distinct part)

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":1000:2")
       >>> time, q_full, q_self, q_distinct = fs.overlap_q(atoms, 2, fs.TimeAxis.Logarithmic(200))
       >>> plt.semilogx(time / 1000, q_full, label=r"$q_\mathrm{full}$")
       >>> plt.semilogx(time / 1000, q_self, label=r"$q_\mathrm{self}$", color="C2")
       >>> plt.semilogx(time / 1000, q_distinct, label=r"$q_\mathrm{distinct}$", color="C3")
       >>> plt.legend()
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Overlap parameter")
       >>> plt.ylim(0)

    """
    ...

def overlap_q_self(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Self part of the overlap parameter.

    It is defined as :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q_\mathrm{s}(t) = \left\langle \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|) \right\rangle_{t_0},

    where :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two arrays of length n_times containing the self part of the overlap parameter (time, self part)

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import fastatomstruct as fs
       >>> import matplotlib.pyplot as plt
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index="::2")
       >>> time, q_self = fs.overlap_q_self(atoms, 2, fs.TimeAxis.Logarithmic(200))
       >>> plt.semilogx(time / 1000, q_self)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"$q_\mathrm{self}$")
       >>> plt.ylim(0, 1000)

    """
    ...

def overlap_q_self_atomic(atoms: List[ase.Atoms], a: float) -> np.typing.NDArray:
    """Self part of the overlap parameter for each individual atom.

    It is defined as

    .. math::

        Q_\mathrm{s}(i, t) = \left\langle w(|\vec{r}_i(0) - \vec{r}_i(t)|) \right\rangle_{t_0},

    where :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function

    Returns:
        Array of shape (n_atoms, n_times) containing the self part of the overlap parameter

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    >>> import fastatomstruct as fs
    >>> from ase import io
    >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
    >>> fs.overlap_q_self_atomic(atoms, 2)
    array([[0.        , 1.        , 1.        , ..., 1.        , 1.        ,
            1.        ],
           [0.        , 1.        , 1.        , ..., 1.        , 1.        ,
            0.99906716],
           [0.        , 1.        , 1.        , ..., 1.        , 1.        ,
            1.        ],
           ...,
           [0.        , 1.        , 1.        , ..., 1.        , 1.        ,
            1.        ],
           [0.        , 1.        , 1.        , ..., 1.        , 1.        ,
            1.        ],
           [0.        , 1.        , 1.        , ..., 0.98878505, 1.        ,
            0.9869403 ]])
    """
    ...

def overlap_q_distinct(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Distinct part of the overlap parameter.

    It is defined as :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q_\mathrm{d}(t) = \left\langle \sum_{i, j = 1, i \neq j}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|) \right\rangle_{t_0},

    where :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two arrays of length n_times containing the time and the distinct part of the overlap parameter

    Examples
    --------

    The exemplary file "Sb-1.00-300-100.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("Sb-1.00-300-100.traj", index=":")
       >>> time, q = fs.overlap_q_distinct(atoms, 2, fs.TimeAxis.Logarithmic(200))
       >>> plt.semilogx(time / 1000, q)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"$q_\mathrm{distinct}$")
       >>> plt.ylim(0, 70)
       >>> plt.tight_layout()

    """
    ...

def overlap_q_single(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray, np.typing.NDArray, np.typing.NDArray]:
    """Non-averaged overlap parameter.

    It is defined as :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q(t) = \sum_{i, j = 1}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|).

    Here, :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.
    The overlap parameter can be split into a self-part

    .. math::

        Q_\mathrm{s}(t) = \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|)

    and a distinct part

    .. math::

        Q_\mathrm{d}(t) = \sum_{i, j = 1, i \neq j}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|).

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Tuple of four arrays of length n_times (time, full q, self part, distinct part)

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, q_full, q_self, q_distinct = fs.overlap_q_single(atoms, 2, fs.TimeAxis.Logarithmic(100))
       >>> plt.semilogx(time / 1000, q_full, label=r"$q_\mathrm{full}$")
       >>> plt.semilogx(time / 1000, q_self, label=r"$q_\mathrm{self}$", color="C2")
       >>> plt.semilogx(time / 1000, q_distinct, label=r"$q_\mathrm{distinct}$", color="C3")
       >>> plt.legend()
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Overlap parameter")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def overlap_q_single_self(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Self part of the overlap parameter.

    It is defined as

    .. math::

        Q_\mathrm{s}(t) = \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|),

    where :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two arrays of length n_times containing the time and the self part of the overlap parameter

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, q = fs.overlap_q_single_self(atoms, 2, fs.TimeAxis.Logarithmic(100))
       >>> plt.semilogx(time / 1000, q)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"$q_\mathrm{self}$")
       >>> plt.ylim(0, 1000)
       >>> plt.tight_layout()

    """
    ...

def overlap_q_single_distinct(
    atoms: List[ase.Atoms], a: float, time_axis: fastatomstruct.TimeAxis
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Distinct part of the overlap parameter.

    It is defined as

    .. math::

        Q_\mathrm{d}(t) = \sum_{i, j = 1, i \neq j}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|),

    where :math:`w(x)` is an "overlap" function that is one for :math:`x \leq a` and zero otherwise.

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two arrays of length n_times containing the time and the distinct part of the overlap parameter

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> import numpy as np
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, q = fs.overlap_q_single_distinct(atoms, 2, fs.TimeAxis.Logarithmic(100))
       >>> plt.semilogx(time / 1000, q)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"$q_\mathrm{distinct}$")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def fourpoint_susceptibility(
    atoms: List[ase.Atoms],
    a: float,
    temperature: float,
    time_axis: fastatomstruct.TimeAxis,
) -> Tuple[
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
]:
    """    Four-point susceptibility.

    It is defined as

    .. math::

        \chi_4(t) = \frac{\beta V}{N^2} \left[\langle Q^2(t) \rangle - \langle Q(t) \rangle^2\right]

    and gives information about dynamical heterogeneities. It can be split into three different parts :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        \chi_4(t) = \chi_\mathrm{ss}(t) + \chi_\mathrm{dd}(t) + \chi_\mathrm{sd}(t),

    where

    .. math::

        \begin{split}
        \chi_\mathrm{ss}(t) &\propto \langle Q_\mathrm{s}^2(t)\rangle - \langle Q_\mathrm{s}(t) \rangle^2, \\
        \chi_\mathrm{dd}(t) &\propto \langle Q_\mathrm{d}^2(t)\rangle - \langle Q_\mathrm{d}(t) \rangle^2\mathrm{, and} \\
        \chi_\mathrm{sd}(t) &\propto \langle Q_\mathrm{s}(t) Q_\mathrm{d}(t) \rangle - \langle Q_\mathrm{s}(t) \rangle \langle Q_\mathrm{d}(t) \rangle.
        \end{split}

    :math:`Q(t)`, :math:`Q_\mathrm{s}(t)` and :math:`Q_\mathrm{d}(t)` are the overlap parameters defined as

    .. math::

        Q(t) = \sum_{i, j = 1}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|),

    with the self part :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q_\mathrm{s}(t) = \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|),

    and the distinct part :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q_\mathrm{d}(t) = \sum_{i, j = 1, i \neq j}^N w(|\vec{r}_i(0) - \vec{r}_j(t)|).

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        temperature (float): Temperature of the system (in K)
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Five arrays of length n_times containing the time, the four-point susceptibility (full, self part, distinct part, cross part)

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, chi_full, chi_self, chi_distinct, chi_cross = fs.fourpoint_susceptibility(atoms, 2, 300, fs.TimeAxis.Logarithmic(100))
       >>> plt.axhline(0, color="black", linestyle=":", linewidth=0.5, alpha=0.5)
       >>> plt.semilogx(time / 1000, chi_full, label=r"$\chi_4$")
       >>> plt.semilogx(time / 1000, chi_self, label=r"$\chi_\mathrm{ss}$", color="C2")
       >>> plt.semilogx(time / 1000, chi_distinct, label=r"$\chi_\mathrm{dd}$", color="C3")
       >>> plt.semilogx(time / 1000, chi_cross, label=r"$\chi_\mathrm{sd}$", color="C4")
       >>> plt.legend()
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Four-point susceptibility")
       >>> plt.tight_layout()

    """
    ...

def fourpoint_susceptibility_self(
    atoms: List[ase.Atoms],
    a: float,
    temperature: float,
    time_axis: fastatomstruct.TimeAxis,
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """Self part of the four-point susceptibility.

    It is defined as

    .. math::

        \chi_\mathrm{ss}(t) = \frac{\beta V}{N^2} \left[\langle Q_\mathrm{s}^2(t) \rangle - \langle Q_\mathrm{s}(t) \rangle^2\right].

    :math:`Q_\mathrm{s}(t)` is the self part of the overlap parameter, defined as :cite:`lacevicSpatiallyHeterogeneousDynamics2003`

    .. math::

        Q_\mathrm{s}(t) = \sum_{i = 1}^N w(|\vec{r}_i(0) - \vec{r}_i(t)|).

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        a (float): Cutoff for the overlap function
        temperature (float): Temperature of the system (in K)
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Two arrays of length n_times containing the time and the self part of the four-point susceptibility

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, chi = fs.fourpoint_susceptibility_self(atoms, 2, 300, fs.TimeAxis.Logarithmic(100))
       >>> plt.semilogx(time / 1000, chi)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel(r"$\chi_\mathrm{ss}$")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def vacf(
    atoms: List[ase.Atoms], time_axis: fastatomstruct.TimeAxis, use_masses: bool = True
) -> Tuple[np.typing.NDArray, np.typing.NDArray]:
    """The velocity autocorrelation function (VACF) is a measure of how the velocity of particles in a system correlates with their velocities at later times. It is defined as the time-dependent correlation of the velocity of particles in a system, which can be used to analyze the dynamics of atomic motion and structural relaxation in materials. The VACF is given by:

    .. math::

       V(t) = \frac{1}{N} \sum_{i=1}^{N} \langle \mathbf{v}_i(0) \cdot \mathbf{v}_i(t) \rangle

    Arguments:
        atoms (List[ase.Atoms]): List of Atoms objects from ASE
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic
        use_masses (bool): Whether masses are used in the calculation (default: True)

    Returns:
        Two arrays of length n_times containing the time and the velocity autocorrelation function

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/Sb-1.00-300-100.traj>`__.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> t, vacf = fs.vacf(atoms, 100)
       >>> plt.plot(t / 1000, vacf)
       >>> plt.xlim(0, 2)
       >>> plt.xlabel("Time (ps)")
       >>> plt.ylabel("Velocity autocorrelation")
       >>> plt.tight_layout()

    """
    ...

def viscosity(
    data: Union[List[ase.Atoms], List[np.ndarray], np.ndarray],
    time_axis: fastatomstruct.TimeAxis,
) -> Tuple[np.typing.NDArray, np.typing.NDArray, np.typing.NDArray]:
    """Viscosity calculation from the stress autocorrelation function. The viscosity is calculated
    from the stress autocorrelation function (SACF) using the Green-Kubo relation:

    .. math::

       \eta = \frac{1}{3 k_B T} \int_0^\infty \langle \sigma(t) \sigma(0) \rangle dt

    Arguments:
        data (Union[List[ase.Atoms], List[np.ndarray], np.ndarray]): List of Atoms objects from ASE, or list of (2D) stress arrays, or 3D stress array
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Three arrays of length n_times containing the time, the stress autocorrelation, and viscosity

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>__`.

    .. plot::

       >>> import matplotlib.pyplot as plt
       >>> import fastatomstruct as fs
       >>> from ase import io
       >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
       >>> time, acf, viscosity = fs.viscosity(atoms, 100)
       >>> plt.plot(time / 1000, viscosity)
       >>> plt.xlabel("Lag time (ps)")
       >>> plt.ylabel("Viscosity (Pa s)")
       >>> plt.ylim(0)
       >>> plt.tight_layout()

    """
    ...

def viscosity_average(
    data: List[Union[ase.Atoms, List[np.ndarray], np.ndarray]],
    time_axis: fastatomstruct.TimeAxis,
) -> Tuple[
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
    np.typing.NDArray,
]:
    """Average viscosity calculation from the stress autocorrelation function. As explained in the
    `viscosity` function, the viscosity is calculated from the stress autocorrelation function (SACF)
    using the Green-Kubo relation. This function averages the results of multiple viscosity calculations
    to provide a more robust estimate of the viscosity.

    .. math::

       \eta = \frac{1}{3 k_B T} \int_0^\infty \langle \sigma(t) \sigma(0) \rangle dt

    Arguments:
        data (List[Union[ase.Atoms, List[np.ndarray], np.ndarray]]): List of Atoms objects from ASE, or list of (2D) stress arrays
        time_axis (fastatomstruct.TimeAxis): Time axis, either linear or logarithmic

    Returns:
        Five arrays of length n_times containing the time, the stress autocorrelation, the error of the stress autocorrelation, the viscosity, and the error of the viscosity

    Examples
    --------

    The exemplary file "SbViscosity-1000K.traj" `can be found here <https://zivgitlab.uni-muenster.de/ag-salinga/fastatomstruct/-/raw/master/tests/structures/SbViscosity-1000K.traj>`.

    >>> import fastatomstruct as fs
    >>> from ase import io
    >>> atoms = io.read("SbViscosity-1000K.traj", index=":")
    >>> fs.viscosity_average([atoms, atoms], 100)

    """
    ...
