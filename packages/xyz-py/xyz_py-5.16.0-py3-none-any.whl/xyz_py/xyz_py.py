#! /usr/bin/env python3

'''
This is the main part of xyz_py
'''

import numpy as np
from numpy.typing import ArrayLike, NDArray
import numpy.linalg as la
from ase import neighborlist, Atoms
from ase.geometry.analysis import Analysis
import copy
import re
from scipy.optimize import least_squares
import sys
from collections import defaultdict

from . import version
from . import atomic

__version__ = version.__version__


class XYZError(Exception):
    '''
    Exception for malformatted xyz file
    '''
    pass


def load_xyz(f_name: str, atomic_numbers: bool = False,
             add_indices: bool = False,
             capitalise: bool = True,
             check: bool = True,
             missing_headers: bool = False) -> tuple[list, NDArray]:
    '''
    Load labels and coordinates from a .xyz file\n\n

    File assumes two header lines, first containing number of atoms\n
    and second containing a comment or blank, followed by actual data

    Parameters
    ----------
    f_name: str
        File name
    atomic_numbers: bool, default False
        If True, reads xyz file with atomic numbers and converts to labels
    add_indices: bool, default False
        If True, add indices to atomic labels\n
        (replacing those which may exist already)
    capitalise: bool, default True
        If True, capitalise atomic labels
    check: bool, default True
        If True, check xyz file before loading
    missing_headers: bool, default False
        If True, then will assume no NATOMS and COMMENT lines are present\n
        at the top of the xyz file.

    Returns
    -------
    list
        atomic labels
    np.ndarray
        (n_atoms,3) array containing xyz coordinates of each atom
    '''

    # Check xyz file formatting
    if check:
        check_xyz(
            f_name,
            allow_nonelements=atomic_numbers,
            allow_missing_headers=missing_headers
        )

    if missing_headers:
        skiprows = 0
    else:
        skiprows = 2

    if atomic_numbers:
        _numbers = np.loadtxt(
            f_name,
            skiprows=skiprows,
            usecols=0,
            dtype=int,
            ndmin=1
        )
        _labels = num_to_lab(_numbers.tolist())
    else:
        _labels = np.loadtxt(
            f_name,
            skiprows=skiprows,
            usecols=0,
            dtype=str,
            ndmin=1
        )
        _labels = _labels.tolist()

    # Set labels as capitals
    if capitalise:
        _labels = [lab.capitalize() for lab in _labels]

    if add_indices:
        _labels = remove_label_indices(_labels)
        _labels = add_label_indices(_labels)

    _coords = np.loadtxt(
        f_name,
        skiprows=skiprows,
        usecols=(1, 2, 3),
        ndmin=2
    )

    return _labels, _coords


def load_xyz_comment(f_name: str) -> str:
    '''
    Load comment line from an xyz file

    Parameters
    ----------
    f_name: str
        File name

    Returns
    -------
    str
        comment line of xyz file
    '''

    # Check xyz file formatting
    check_xyz(f_name)

    with open(f_name, 'r') as f:
        next(f)
        comment = next(f)

    comment = comment.rstrip()

    return comment


def detect_xyz_formatting(f_name: str) -> dict[str, bool]:
    '''
    Scans xyz file and detects formatting

    Parameters
    ----------
    f_name: str
        File name of .xyz file

    Returns
    -------
    dict[str, bool]
        Keys are 'atomic_numbers', 'non-elements', 'indices', \n
        'missing_headers'\n
        Values are bools
    '''

    # Load file without checks
    try:
        _labels, _ = load_xyz(f_name, capitalise=False, check=False)
    except (XYZError, ValueError):
        raise XYZError('.xyz file cannot be read!')

    formatting = {
        'missing_headers': False,
        'non-elements': False,
        'atomic_numbers': False,
        'indices': False
    }

    # Check for missing headers
    try:
        _check_xyz_headers(f_name)
    except XYZError:
        formatting['missing_headers'] = True

    # Remove indexing labels if present
    _labels_nn = remove_label_indices(_labels)

    # Check for atomic numbers
    if any([lab not in atomic.elements and lab.isdigit for lab in _labels_nn]):
        formatting['atomic_numbers'] = True

    # Check for non-elements
    if any([lab not in atomic.elements and not lab.isdigit for lab in _labels_nn]): # noqa
        formatting['non-elements'] = True

    # Check if indices are present
    if any([labnn != lab for labnn, lab in zip(_labels_nn, _labels)]):
        formatting['indices'] = True

    return formatting


def _check_xyz_headers(f_name: str):
    '''
    Checks if .xyz file has correct length and contains two header lines\n
    for the number of atoms and an optional comment

    Parameters
    ----------
    f_name: str
        File name

    Returns
    -------
    None

    Raises
    ------
    XYZError
        If the .xyz file has incorrect length or is missing the number\n
        of atoms and comment lines
    '''

    with open(f_name, 'r') as f:
        line = next(f)
        if len(line.split()) != 1:
            raise XYZError('.xyz file does not contain number of atoms')
        else:
            try:
                n_atoms = int(line)
            except ValueError:
                raise XYZError('.xyz file number of atoms is malformed')

            n_lines = len(f.readlines()) + 1  # + 1 for next
            if n_atoms + 2 != n_lines:
                raise XYZError('.xyz file length/format is incorrect')

    return


def check_xyz(f_name: str, allow_indices: bool = True,
              allow_nonelements: bool = False,
              allow_missing_headers: bool = False) -> None:
    '''
    Checks if .xyz file has correct length, contains two header lines\n
    for the number of atoms and an optional comment, and contains atomic
    numbers or non-elements instead of element labels.

    Parameters
    ----------
    f_name: str
        File name
    allow_indices: bool, default True
        If True, allows indexing numbers on atomic labels
    allow_nonelements, bool default False
        If True, allow atomic labels which are do not correspond to a \n
        chemical element
    allow_missing_headers, bool default False
        If True, allows missing NATOMS and COMMENT lines \n
        at the top of the xyz file.

    Returns
    -------
    None

    Raises
    ------
    XYZError
        If the .xyz file has incorrect length, is missing the number\n
        of atoms and comment lines, or contains atomic label indices
    '''

    # Check file contains number of atoms on first line
    # and comment on second
    if not allow_missing_headers:
        _check_xyz_headers(f_name)

    try:
        _labels, _ = load_xyz(f_name, capitalise=False, check=False)
    except (XYZError, ValueError):
        raise XYZError('.xyz file cannot be read!')

    # Remove indexing labels if present
    _labels_nn = remove_label_indices(_labels)

    # Check all entries are real elements
    if not allow_nonelements:
        if any([lab not in atomic.elements for lab in _labels_nn]):
            raise XYZError('.xyz file contains non-elements')

    # Check if indices are present
    if not allow_indices:
        if any([labnn != lab for labnn, lab in zip(_labels_nn, _labels)]):
            raise XYZError('.xyz file contains elements with indices')

    return


def save_xyz(f_name: str, labels: ArrayLike, coords: ArrayLike,
             with_numbers: bool = False, verbose: bool = True,
             mask: list = [], atomic_numbers: bool = False,
             comment: str = '') -> None:
    '''
    Save an xyz file containing labels and coordinates

    Parameters
    ----------
    f_name: str
        File name
    labels: array_like
        atomic labels
    coords: array_like
        list of 3 element lists containing xyz coordinates of each atom
    with_numbers: bool, default False
        If True, add/overwrite numbers to labels before printing
    verbose: bool, default True
        Print information on filename to screen
    mask: list, optional
        n_atom list of 0 (exclude) and 1 (include) indicating which
        atoms to print
    atomic_numbers: bool, default False
        If True, will save xyz file with atomic numbers
    comment: str, default ''
        Comment line printed to 2nd line of .xyz file

    Returns
    -------
    None
    '''

    coords = np.asarray(coords)

    # Option to have numbers added
    if with_numbers:
        # Remove and re-add numbers to be safe
        _labels = remove_label_indices(labels)
        _labels = add_label_indices(_labels)
    else:
        _labels = labels

    # Set up masks
    if mask:
        coords = np.delete(coords, mask, axis=0)
        _labels = np.delete(_labels, mask, axis=0).tolist()

    n_atoms = len(_labels)

    if atomic_numbers:
        _labels = remove_label_indices(_labels)
        _numbers = lab_to_num(_labels)
        _identifier = _numbers
    else:
        _identifier = _labels

    with open(f_name, 'w') as f:
        f.write(f'{n_atoms:d}\n')
        f.write(f'{comment}')
        for ident, trio in zip(_identifier, coords):
            f.write('\n{:5} {:15.7f} {:15.7f} {:15.7f}'.format(ident, *trio))

    if verbose:
        print('New xyz file written to {}'.format(f_name))

    return


def remove_label_indices(labels: ArrayLike | str) -> list[str]:
    '''
    Remove label indexing from atomic symbols\n
    indexing is either numbers or numbers followed by letters:\n
    e.g. H1, H2, H3\n
    or H1a, H2a, H3a

    Parameters
    ----------
    labels: array_like | str
        atomic labels

    Returns
    -------
    list[str] | str
        atomic labels without indexing, type depends on input type
    '''

    if isinstance(labels, str):
        _labels = [labels]
    else:
        _labels = labels

    labels_nn = []
    for label in _labels:
        no_digits = []
        for i in label:
            if not i.isdigit():
                no_digits.append(i)
            elif i.isdigit():
                break
        result = ''.join(no_digits)
        labels_nn.append(result)

    if isinstance(labels, str):
        return labels_nn[0]
    else:
        return labels_nn


def add_label_indices(labels: ArrayLike, style: str = 'per_element',
                      start_index: int = 1) -> list[str]:
    '''
    Add label indexing to atomic symbols - either element or per atom.

    Parameters
    ----------
    labels: array_like
        atomic labels
    style: str, optional
        {'per_element', 'sequential'}\n
            'per_element': Index by element e.g. Dy1, Dy2, N1, N2, etc.\n
            'sequential': Index the atoms 1->N regardless of element
    start_index: int, default 1
        integer at which indexing will start

    Returns
    -------
    list[str]
        atomic labels with indexing
    '''

    # remove numbers just in case
    labels_nn = remove_label_indices(labels)

    # Just number the atoms 1->N regardless of element
    if style == 'sequential':
        labels_wn = ['{}{:d}'.format(lab, it + start_index)
                     for (it, lab) in enumerate(labels_nn)]

    # Index by element Dy1, Dy2, N1, N2, etc.
    elif style == 'per_element':
        # Get list of unique elements
        atoms = set(labels_nn)
        # Create dict to keep track of index of current atom of each element
        atom_count = {atom: start_index for atom in atoms}
        # Create labelled list of elements
        labels_wn = []

        for lab in labels_nn:
            # Index according to dictionary
            labels_wn.append('{}{:d}'.format(lab, atom_count[lab]))
            # Then add one to dictionary
            atom_count[lab] += 1
    else:
        raise ValueError('Unknown label style requested')

    return labels_wn


def count_n_atoms(form_str: str) -> int:
    '''
    Count number of atoms in a chemical formula

    Parameters
    ----------
    form_str: str
        chemical formula string

    Returns
    -------
    int
        number of atoms in chemical formula
    '''

    form_dict = formstr_to_formdict(form_str)

    n_atoms = sum(form_dict.values())

    return n_atoms


def index_elements(labels: ArrayLike, shift: int = 0) -> dict[str, int]:
    '''
    Return dictionary of element (keys) and positional indices (values)
    from list of labels

    Parameters
    ----------
    labels: array_like
        atomic labels
    shift: int, default 0
        additive shift to apply to all indices

    Returns
    -------
    dict[str, int]
        element label (keys) and indices (values)
    '''

    labels_nn = remove_label_indices(labels)

    ele_index = {}

    for it, lab in enumerate(labels_nn):
        try:
            ele_index[lab].append(it + shift)
        except KeyError:
            ele_index[lab] = [it + shift]

    return ele_index


def count_elements(labels: ArrayLike) -> dict[str, int]:
    '''
    Count number of each element in a list of elements

    Parameters
    ----------
    labels: array_like
        atomic labels
    Returns
    -------
    dict[str, int]
        dictionary of elements (keys) and counts (vals)
    '''

    labels_nn = remove_label_indices(labels)

    ele_count = {}

    for lab in labels_nn:
        try:
            ele_count[lab] += 1
        except KeyError:
            ele_count[lab] = 1

    return ele_count


def get_formula(labels: ArrayLike) -> str:
    '''
    Generates empirical formula in alphabetical order given a list of labels

    Parameters
    ----------
    labels: array_like
        atomic labels

    Returns
    -------
    str
        Empirical formula in alphabetical order
    '''

    formdict = count_elements(labels)

    formula = formdict_to_formstr(formdict)

    return formula


def formstr_to_formdict(form_str: str) -> dict[str, int]:
    '''
    Converts formula string into dictionary of {atomic label:quantity} pairs

    Parameters
    ----------
    form_string: str
        Chemical formula as string

    Returns
    -------
    dict[str, int]
        dictionary of {atomic label:quantity} pairs
    '''

    form_dict = {}
    # Thanks stack exchange!
    s = re.sub
    f = s(
        "[()',]",
        '',
        str(
            eval(
                s(
                    r',?(\d+)',
                    r'*\1,',
                    s(
                        '([A-Z][a-z]*)',
                        r'("\1",),',
                        form_str
                    )
                )
            )
        )
    ).split()
    for c in set(f):
        form_dict[c] = f.count(c)

    return form_dict


def formdict_to_formstr(form_dict: dict[str, int],
                        include_one: bool = False) -> str:
    '''
    Converts dictionary of {atomic label:quantity} pairs into\n
    a single formula string in alphabetical order

    Parameters
    ----------
    form_dict: dict[str, int]
        dictionary of {atomic label:quantity} pairs
    include_one: bool, default False
        Include 1 in final chemical formula e.g. C1H4

    Returns
    -------
    str
        Chemical formula as string in alphabetical order
    '''

    # Formula labels and quantities as separate lists with same order
    form_labels = ['{:s}'.format(key) for key in form_dict.keys()]
    form_quants = [val for val in form_dict.values()]

    # Quantities of each element as a string
    if include_one:
        form_quants_str = ['{:d}'.format(quant)
                           for quant in form_quants]
    else:
        form_quants_str = ['{:d}'.format(quant)
                           if quant > 1 else ''
                           for quant in form_quants]

    # Sort labels in alphabetical order
    order = np.argsort(form_labels).tolist()
    form_labels_o = [form_labels[o] for o in order]
    # Use same ordering for quantities
    form_quants_str_o = [form_quants_str[o] for o in order]

    # Make list of elementquantity strings
    form_list = [el + quant
                 for el, quant in zip(form_labels_o, form_quants_str_o)]

    # Join strings together into empirical formula
    form_string = ''.join(form_list)

    return form_string


def standardise_formstr(form_str: str) -> str:
    '''
    Standardises a given formula string to alphabetical order

    Parameters
    ----------
    form_str: str
        String to standardise

    Returns
    -------
    str
        Standardised string
    '''

    fd = formstr_to_formdict(form_str)

    form_str = formdict_to_formstr(fd)

    return form_str


def contains_metal(form_string: str) -> bool:
    '''
    Indicates if a metal is found in a chemical formula string

    Parameters
    ----------
    form_string: str
        Chemical formula as string

    Returns
    -------
    bool
        True if metal found, else False
    '''
    metal_found = False

    for metal in atomic.metals:
        if metal in form_string:
            metal_found = True
            break

    return metal_found


def combine_xyz(labels_1: ArrayLike, labels_2: ArrayLike, coords_1: ArrayLike,
                coords_2: ArrayLike) -> tuple[list[str], NDArray]:
    '''
    Combine two sets of labels and coordinates

    Parameters
    ----------
    labels_1: array_like
        Atomic labels
    coords_1: array_like
        xyz coordinates as (n_atoms, 3) array
    labels_2: array_like
        Atomic labels
    coords_2: array_like
        xyz coordinates as (n_atoms, 3) array

    Returns
    -------
    list[str]
        Combined atomic labels
    ndarray of floats
        Combined xyz coordinates as (n_atoms, 3) array
    '''

    coords_1 = np.asarray(coords_1)
    coords_2 = np.asarray(coords_2)
    labels_1 = np.asarray(labels_1)
    labels_2 = np.asarray(labels_2)

    # Concatenate labels lists
    labels = np.concatenate(labels_1, labels_2, axis=0).tolist()

    # Concatenate coordinate lists
    coords = np.concatenate(coords_1, coords_2, axis=0)

    return labels, coords


def get_neighborlist(labels: ArrayLike, coords: ArrayLike,
                     adjust_cutoff: dict[str, float] = {}) -> neighborlist.NeighborList: # noqa
    '''
    Calculate ASE neighborlist based on covalent radii

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    adjust_cutoff: dict[str, float], optional
        dictionary of atoms (keys) and new cutoffs (values)

    Returns
    -------
    neighborlist.NeighborList
        Neighborlist for system
    '''

    coords = np.asarray(coords)

    # Remove labels if present
    labels_nn = remove_label_indices(labels)

    # Load molecule
    mol = Atoms(''.join(labels_nn), positions=coords)

    # Define cutoffs for each atom using atomic radii
    cutoffs = neighborlist.natural_cutoffs(mol)

    # Modify cutoff if requested
    if adjust_cutoff:
        for it, label in enumerate(labels_nn):
            if label in adjust_cutoff.keys():
                cutoffs[it] = adjust_cutoff[label]

    # Create neighborlist using cutoffs
    neigh_list = neighborlist.NeighborList(
        cutoffs=cutoffs,
        self_interaction=False,
        bothways=True
    )

    # Update this list by specifying the atomic positions
    neigh_list.update(mol)

    return neigh_list


def get_adjacency(labels: ArrayLike, coords: ArrayLike,
                  adjust_cutoff: dict[str, float] = {}) -> NDArray:
    '''
    Calculate adjacency matrix using ASE based on covalent radii.

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    adjust_cutoff: dict[str, float], optional
        dictionary of atoms (keys) and new cutoffs (values)

    Returns
    -------
    ndarray of floats
        Adjacency matrix with same order as labels/coords
    '''

    coords = np.asarray(coords)

    # Remove labels if present
    labels_nn = remove_label_indices(labels)

    # Get neighborlist.NeighborList
    neigh_list = get_neighborlist(
        labels_nn,
        coords,
        adjust_cutoff=adjust_cutoff
    )

    # Create adjacency matrix
    adjacency = neigh_list.get_connectivity_matrix(sparse=False)

    return adjacency


def get_bonds(labels: ArrayLike, coords: ArrayLike,
              neigh_list: neighborlist.NeighborList = None,
              verbose: bool = True,
              style: str = 'indices') -> list[list[int | str]]:
    '''
    Calculate list of atoms between which there is a bond.\n
    Using ASE. Only unique bonds are retained.\n
    e.g. 0-1 and not 1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array in Angstrom
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of bonds to screen
    style: str, {'indices','labels'}
        indices: Bond list contains atom number\n
        labels : Bond list contains atom label

    Returns
    -------
    list[list[int | str]]
        list of lists of unique bonds (atom pairs)
    '''

    coords = np.asarray(coords)

    bonds, _ = find_bonds(
        labels, coords, neigh_list=neigh_list, verbose=verbose, style=style
    )

    return bonds


def find_bonds(labels: ArrayLike, coords: ArrayLike,
               neigh_list: neighborlist.NeighborList = None,
               verbose: bool = True,
               style: str = 'labels') -> tuple[list[list[int | str]], NDArray]:
    '''
    Calculate list of atoms between which there is a bond.\n
    Using ASE. Only unique bonds are retained.\n
    e.g. 0-1 and not 1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array in Angstrom
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of bonds to screen
    style: str, {'indices','labels'}
        indices: Bond list contains atom number\n
        labels : Bond list contains atom label

    Returns
    -------
    list[list[int | str]]
        list of lists of unique bonds (atom pairs)
    ndarray of floats
        Bond length in Angstrom
    '''

    coords = np.asarray(coords)

    # Remove labels if present
    labels_nn = remove_label_indices(labels)

    # Create molecule object
    mol = Atoms(''.join(labels_nn), positions=coords)

    # Get neighborlist if not provided to function
    if not neigh_list:
        neigh_list = get_neighborlist(labels, coords)

    # Get object containing analysis of molecular structure
    ana = Analysis(mol, nl=neigh_list)

    # Get bonds from ASE
    # Returns: list of lists of lists containing UNIQUE bonds
    # Defined as
    # Atom 1: [bonded atom, bonded atom], ...
    # Atom 2: [bonded atom, bonded atom], ...
    # Atom n: [bonded atom, bonded atom], ...
    # Where only the right hand side is in the list
    is_bonded_to = ana.unique_bonds

    # Remove weird outer list wrapping the entire thing twice...
    is_bonded_to = is_bonded_to[0]
    # Create list of bonds (atom pairs) by appending lhs of above
    # definition to each element of the rhs
    bonds = []
    bonds = [
        [it, atom]
        for it, ibt in enumerate(is_bonded_to)
        for atom in ibt
    ]

    # Count bonds
    n_bonds = len(bonds)

    # Calculate actual values
    values = np.array([
        ana.get_bond_value(0, bond)
        for bond in bonds
    ])

    labels = add_label_indices(labels)

    # Set format and convert to atomic labels if requested
    if style == 'labels':
        bonds = [
            [labels[atom1], labels[atom2]]
            for atom1, atom2 in bonds
        ]
    elif style == 'indices':
        pass
    else:
        sys.exit('Unknown style specified')

    # Print number of bonds to screen
    if verbose:
        print('{:d} bonds'.format(n_bonds))

    return bonds, values


def get_angles(labels: ArrayLike, coords: ArrayLike,
               neigh_list: neighborlist.NeighborList = None,
               verbose: bool = True,
               style: str = 'indices') -> list[list[int | str | float]]:
    '''
    Calculate list of atoms between which there is a bond angle.
    Using ASE. Only unique angles are retained.
    e.g. 0-1-2 but not 2-1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of angles to screen
    style: str, {'indices','labels'}
            indices: Angle list contains atom number
            labels : Angle list contains atom label
            values : Angle list is values in degrees

    Returns
    -------
    list[list[int | str | float]]
        list of lists of unique angles (atom trios)
    '''

    coords = np.asarray(coords)

    angles, _ = find_angles(
        labels, coords, neigh_list=neigh_list, verbose=verbose, style=style
    )

    return angles


def find_angles(labels: ArrayLike, coords: ArrayLike,
                neigh_list: neighborlist.NeighborList = None,
                verbose: bool = True,
                style='labels') -> tuple[list[list[int | str]], NDArray]:
    '''
    Calculate all angles using ASE. Only unique angles are retained.
    e.g. 0-1-2 but not 2-1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of angles to screen
    style: str, {'indices','labels'}
            indices: Angle labels are atom number
            labels : Angle labels are atom label

    Returns
    -------
    list[list[int | str]]
        list of lists of unique angles (atom trios) as labels or indices
    np.ndarray
        Angles in degrees
    '''

    coords = np.asarray(coords)

    # Remove labels if present
    labels_nn = remove_label_indices(labels)

    # Create molecule object
    mol = Atoms(''.join(labels_nn), positions=coords)

    # Get neighborlist if not provided to function
    if not neigh_list:
        neigh_list = get_neighborlist(labels, coords)

    # Get object containing analysis of molecular structure
    ana = Analysis(mol, nl=neigh_list)

    # Get angles from ASE
    # Returns: list of lists of lists containing UNIQUE angles
    # Defined as
    # Atom 1: [[atom,atom], [atom,atom]], ...
    # Atom 2: [[atom,atom], [atom,atom]], ...
    # Atom n: [[atom,atom], [atom,atom]], ...
    # Where only the right hand side is in the list
    is_angled_to = ana.unique_angles

    # Remove weird outer list wrapping the entire thing twice...
    is_angled_to = is_angled_to[0]
    # Create list of angles (atom trios) by appending lhs of above
    # definition to each element of the rhs
    angles = []
    for it, ibt in enumerate(is_angled_to):
        for atoms in ibt:
            angles.append([it, *atoms])

    # Count angles
    n_angles = len(angles)

    # Calculate actual values
    values = np.array([
        ana.get_angle_value(0, angle)
        for angle in angles
    ])

    labels = add_label_indices(labels)

    # Set format and convert to atomic labels if requested
    if style == 'labels':
        angles = [
            [labels[atom1], labels[atom2], labels[atom3]]
            for atom1, atom2, atom3 in angles
        ]
    elif style == 'indices':
        pass
    else:
        sys.exit('Unknown style specified')

    # Print number of angles to screen
    if verbose:
        print('{:d} angles'.format(n_angles))

    return angles, values


def get_dihedrals(labels: ArrayLike, coords: ArrayLike,
                  neigh_list: neighborlist.NeighborList = None,
                  verbose: bool = True,
                  style: str = 'indices') -> list[list[int | str]]:
    '''
    Calculate and list of atoms between which there is a dihedral.
    Using ASE. Only unique dihedrals are retained.
    e.g. 0-1-2-3 but not 3-2-1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of dihedrals to screen
    style: str, {'indices','labels'}
            indices: Dihedral list contains atom number
            labels : Dihedral list contains atom label

    Returns
    -------
    list[list[int | str]]
        list of lists of unique dihedrals (atom quads)
    '''
    coords = np.asarray(coords)

    dihedrals, _ = find_dihedrals(
        labels, coords, neigh_list=neigh_list, verbose=verbose, style=style
    )

    return dihedrals


def find_dihedrals(labels: ArrayLike, coords: ArrayLike,
                   neigh_list: neighborlist.NeighborList = None,
                   verbose: bool = True,
                   style='labels') -> tuple[list[list[int | str]], NDArray]:
    '''
    Calculate and list of atoms between which there is a dihedral.
    Using ASE. Only unique dihedrals are retained.
    e.g. 0-1-2-3 but not 3-2-1-0

    Parameters
    ----------
    labels: array_like
        Atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    neigh_list: neighborlist.NeighborList, optional
        neighborlist of system, calculated if not provided
    verbose: bool, default True
        Print number of dihedrals to screen
    style: str, {'indices','labels'}
            indices: Dihedral list contains atom number
            labels : Dihedral list contains atom label

    Returns
    -------
    list[list[int | str]]
        list of lists of unique dihedrals (atom quads)
    np.ndarray
        Dihedral angles in degrees
    '''

    coords = np.asarray(coords)

    # Remove labels if present
    labels_nn = remove_label_indices(labels)

    # Create molecule object
    mol = Atoms(''.join(labels_nn), positions=coords)

    # Get neighborlist if not provided to function
    if not neigh_list:
        neigh_list = get_neighborlist(labels, coords)

    # Get object containing analysis of molecular structure
    ana = Analysis(mol, nl=neigh_list)

    # Get dihedrals from ASE
    # Returns: list of lists of lists containing UNIQUE dihedrals
    # Defined as
    # Atom 1: [[atom,atom,atom], [atom,atom,atom]], ...
    # Atom 2: [[atom,atom,atom], [atom,atom,atom]], ...
    # Atom n: [[atom,atom,atom], [atom,atom,atom]], ...
    # Where only the right hand side is in the list
    is_dihedraled_to = ana.unique_dihedrals

    # Remove weird outer list wrapping the entire thing twice...
    is_dihedraled_to = is_dihedraled_to[0]
    # Create list of dihedrals (atom quads) by appending lhs of above
    # definition to each element of the rhs
    dihedrals = []
    for it, ibt in enumerate(is_dihedraled_to):
        for atoms in ibt:
            dihedrals.append([it, *atoms])

    # Calculate actual values
    values = np.array([
        ana.get_dihedral_value(0, dihedral)
        for dihedral in dihedrals
    ])

    # Count dihedrals
    n_dihedrals = len(dihedrals)

    labels = add_label_indices(labels)

    # Set format and convert to atomic labels if requested
    if style == 'labels':
        dihedrals = [
            [
                labels[atom1],
                labels[atom2],
                labels[atom3],
                labels[atom4]
            ]
            for atom1, atom2, atom3, atom4 in dihedrals
        ]
    elif style == 'indices':
        pass
    else:
        sys.exit('Unknown style specified')

    # Print number of dihedrals to screen
    if verbose:
        print('{:d} dihedrals'.format(n_dihedrals))

    return dihedrals, values


def lab_to_num(labels: ArrayLike | str) -> list[int]:
    '''
    Convert atomic label to atomic number

    Parameters
    ----------
    labels: array_like | str
        Atomic labels

    Returns
    -------
    list[int] | int
        Atomic numbers
    '''

    if isinstance(labels, str):
        _labels = [labels]
    else:
        _labels = labels

    labels_nn = remove_label_indices(_labels)

    numbers = [atomic.lab_num[lab] for lab in labels_nn]

    if isinstance(labels, str):
        return numbers[0]
    else:
        return numbers


def num_to_lab(numbers: ArrayLike, numbered: bool = True) -> list[str]:
    '''
    Convert atomic number to atomic labels

    Parameters
    ----------
    numbers: array_like of integers
        Atomic numbers as integers
    numbered: bool, default True
        If True, adds indexing number to end of atomic labels

    Returns
    -------
    list[str]
        Atomic labels
    '''

    labels = [atomic.num_lab[int(num)] for num in numbers]

    if numbered:
        labels_wn = add_label_indices(labels)
    else:
        labels_wn = labels

    return labels_wn


def reflect_coords(coords: ArrayLike) -> NDArray:
    '''
    Reflect coordinates through xy plane

    Parameters
    ----------
    coords: array_like
        xyz coordinates as (n_atoms, 3) array

    Returns
    -------
    ndarray of floats
        reflected xyz coordinates as (n_atoms, 3) array

    '''

    # Calculate normal to plane
    x = [1, 0, 0]
    y = [0, 1, 0]
    normal = np.cross(x, y)

    # Set up transformation matrix
    # https://en.wikipedia.org/wiki/Transformation_matrix#Reflection_2
    trans_mat = np.zeros([3, 3])

    trans_mat[0, 0] = 1. - 2. * normal[0] ** 2.
    trans_mat[1, 0] = -2. * normal[0] * normal[1]
    trans_mat[2, 0] = -2. * normal[0] * normal[2]
    trans_mat[0, 1] = -2. * normal[0] * normal[1]
    trans_mat[1, 1] = 1. - 2. * normal[1] ** 2.
    trans_mat[2, 1] = -2. * normal[1] * normal[2]
    trans_mat[0, 2] = -2. * normal[0] * normal[2]
    trans_mat[1, 2] = -2. * normal[1] * normal[2]
    trans_mat[2, 2] = 1. - 2. * normal[2] ** 2.

    # Apply operations
    coords = coords @ trans_mat

    return coords


def find_entities(labels: ArrayLike, coords: ArrayLike,
                  adjust_cutoff: dict[str, float] = {},
                  non_bond_labels: list[str] = []) -> dict[str, list[list[int]]]: # noqa
    '''
    Finds formulae of entities given in labels and coords using adjacency
    matrix

    Parameters
    ----------
    labels: array_like
        atomic labels
    coords: array_like
        xyz coordinates of each atom as (n_atoms, 3) array
    adjust_cutoff: dict[str, float], optional
        dictionary of atoms (keys) and new cutoffs (values) used in generating
        \nadjacency matrix
    non_bond_labels: list[str], optional
        List of atomic labels specifying atoms to which no bonds will be
        allowed.\n
        e.g If a metal centre is provided this will result in single ligands\n
        being returned.\n
        Indices are optional and are used to select specific atoms

    Returns
    -------
    dict[str, list[list[int]]]
        keys = molecular formula\n
        vals = list of lists, where each list contains the indices of a single
        \noccurrence of the `key`, and the indices match the order given\n
        in `labels` and `coords`
    '''

    # Remove label numbers if present
    labels_nn = remove_label_indices(labels)

    # Generate adjacency matrix using ASE
    adjacency = get_adjacency(labels_nn, coords, adjust_cutoff=adjust_cutoff)

    no_bond_indices = [
        it for it, lab in enumerate(labels)
        if lab in non_bond_labels
        or remove_label_indices(lab) in non_bond_labels
    ]

    for nbi in no_bond_indices:
        adjacency[nbi, :] = 0
        adjacency[:, nbi] = 0

    # Find entities
    entities = find_entities_from_adjacency(labels_nn, adjacency)

    return entities


def find_entities_from_adjacency(labels_nn: ArrayLike, adjacency: ArrayLike):
    '''
    Finds formulae of entities given in labels and adjacency matrix

    Parameters
    ----------
    labels: array_like
        atomic labels
    adjacency: array_like
        Adjacency matrix (0,1) with same order as labels

    Returns
    -------
    dict[str:list[list[int]]]
        keys = molecular formula\n
        vals = list of lists, where each list contains the indices of a single
        \noccurrence of the `key`, and the indices match the order given\n
        in `labels` and `coords`
    '''

    adjacency = np.asarray(adjacency)

    # Count number of atoms
    n_atoms = len(labels_nn)

    # Set current fragment as start atom
    curr_frag = {0}

    # List of unvisited atoms
    unvisited = set(np.arange(n_atoms))

    # Dictionary of molecular_formula:[[indices_mol1], [indices_mol2]] pairs
    mol_indices = defaultdict(list)

    # Loop over adjacency matrix and trace out bonding network
    # Make a first pass, recording in a list the atoms which are bonded to the
    # first atom.
    # Then make another pass, and record in another list all the atoms bonded
    # to those in the previous list
    # and again, and again etc.
    while unvisited:
        # Keep copy of current fragment indices to check against for changes
        prev_frag = copy.copy(curr_frag)
        for index in prev_frag:
            # Find bonded atoms and add to current fragment
            indices = list(np.nonzero(adjacency[:, index])[0])
            curr_frag.update(indices)

        # If no changes in fragment last pass, then a complete structure must
        # have been found
        if prev_frag == curr_frag:

            # Generate molecular formula of current fragment
            curr_labels = [labels_nn[it] for it in curr_frag]
            curr_formula = count_elements(curr_labels)

            mol_indices[formdict_to_formstr(curr_formula)].append(
                list(curr_frag)
            )

            # Remove visited atoms
            unvisited = unvisited.difference(curr_frag)

            # Reset lists of labels and indices ready for next cycle
            curr_frag = {min(unvisited)} if unvisited else curr_frag

    mol_indices = dict(mol_indices)

    return mol_indices


def _calculate_rmsd(coords_1: ArrayLike, coords_2: ArrayLike) -> float:
    '''
    Calculates RMSD between two structures\n
    RMSD = sqrt(mean(deviations**2))\n
    Where deviations are defined as norm([x1,y1,z1]-[x2,y2,z2])

    Parameters
    ----------
    coords_1: array_like
        xyz coordinates as (n_atoms, 3) array
    coords_2: array_like
        xyz coordinates as (n_atoms, 3) array

    Returns
    -------
    float
        Root mean square of norms of deviation between two structures
    '''

    coords_1 = np.asarray(coords_1)
    coords_2 = np.asarray(coords_2)

    # Check there are the same number of coordinates
    assert len(coords_1) == len(coords_2)

    # Calculate difference between [x,y,z] of atom pairs
    diff = [trio_1 - trio_2 for trio_1, trio_2 in zip(coords_1, coords_2)]

    # Calculate square norm of difference
    norms_sq = [la.norm(trio)**2 for trio in diff]

    # Calculate mean of squared norms
    mean = np.mean(norms_sq)

    # Take square root of mean
    rmsd = np.sqrt(mean)

    return rmsd


def calculate_rmsd(coords_1: ArrayLike, coords_2: ArrayLike,
                   mask_1: ArrayLike = [], mask_2: ArrayLike = [],
                   order_1: ArrayLike = [], order_2: ArrayLike = []) -> float:
    '''
    Calculates RMSD between two structures\n
    RMSD = sqrt(mean(deviations**2))\n
    Where deviations are defined as norm([x1,y1,z1]-[x2,y2,z2])\n
    If coords_1 and coords_2 are not the same length, then a mask array can be
    \nprovided for either/both and is applied prior to the calculation\n
    coords_1 and coords_2 can also be reordered if new orders are specified
    - note this occurs BEFORE masking

    Parameters
    ----------
    coords_1: array_like
        xyz coordinates as (n_atoms, 3) array
    coords_2: array_like
        xyz coordinates as (n_atoms, 3) array

    mask_1: list
        list of 0 (exclude) and 1 (include) for each element in coords_1
    mask_2: list
        list of 0 (exclude) and 1 (include) for each element in coords_2
    order_1: list
        list of new indices for coords_1 - applied BEFORE masking
    order_2: list
        list of new indices for coords_2 - applied BEFORE masking

    Returns
    -------
    float
        Root mean square of norms of deviation between two structures
    '''

    coords_1 = np.asarray(coords_1)
    coords_2 = np.asarray(coords_2)

    # Set up new ordering
    if order_1:
        _order_1 = order_1
    else:
        _order_1 = range(len(coords_1))

    if order_2:
        _order_2 = order_2
    else:
        _order_2 = range(len(coords_2))

    # Apply new order
    _coords_1 = coords_1[_order_1]
    _coords_2 = coords_2[_order_2]

    # Set up masks
    if mask_1:
        _coords_1 = np.delete(_coords_1, mask_1, axis=0)

    # Set up masks
    if mask_2:
        _coords_2 = np.delete(_coords_2, mask_2, axis=0)

    # Calculate rmsd
    rmsd = _calculate_rmsd(_coords_1, _coords_2)

    return rmsd


def build_rotation_matrix(alpha: float, beta: float, gamma: float) -> NDArray:
    '''
    Creates rotation matrix using euler angles alpha, beta, gamma
    for the zyz convention\n
    https://easyspin.org/easyspin/documentation/eulerangles.html

    Parameters
    ----------
    alpha: float
        alpha angle in radians
    beta: float
        beta  angle in radians
    gamma: float
        gamma angle in radians

    Returns
    -------
    ndarray of floats
        Rotation matrix R which is applied to a vector x as R dot x
    '''
    r_mat = np.zeros([3, 3])

    # Build rotation matrix
    r_mat[0, 0] = np.cos(gamma) * np.cos(beta) * np.cos(alpha) - np.sin(gamma) * np.sin(alpha) # noqa
    r_mat[0, 1] = np.cos(gamma) * np.cos(beta) * np.sin(alpha) + np.sin(gamma) * np.cos(alpha) # noqa
    r_mat[0, 2] = -np.cos(gamma) * np.sin(beta)
    r_mat[1, 0] = -np.sin(gamma) * np.cos(beta) * np.cos(alpha) - np.cos(gamma) * np.sin(alpha) # noqa
    r_mat[1, 1] = -np.sin(gamma) * np.cos(beta) * np.sin(alpha) + np.cos(gamma) * np.cos(alpha) # noqa
    r_mat[1, 2] = np.sin(gamma) * np.sin(beta)
    r_mat[2, 0] = np.sin(beta) * np.cos(alpha)
    r_mat[2, 1] = np.sin(beta) * np.sin(alpha)
    r_mat[2, 2] = np.cos(beta)

    return r_mat


def rotate_coords(coords: ArrayLike, alpha: float, beta: float,
                  gamma: float) -> NDArray:
    '''
    Rotates coordinates using euler angles alpha, beta, gamma
    for the zyz convention\n
    https://easyspin.org/easyspin/documentation/eulerangles.html

    Parameters
    ----------
    coords: array_like
        xyz coordinates as (n_atoms, 3) array
    alpha: float
        alpha angle in radians
    beta: float
        beta  angle in radians
    gamma: float
        gamma angle in radians

    Returns
    -------
    ndarray of floats
        xyz coordinates as (n_atoms, 3) array after rotation\n
        in same order as input coordinates
    '''
    coords = np.asarray(coords)

    R = build_rotation_matrix(alpha, beta, gamma)

    # Create (n,3) matrix from coords list
    _coords = coords.T

    # Apply rotation matrix
    rot_coords = R @ _coords

    # Convert back to (3,n) matrix
    rot_coords = rot_coords.T

    return rot_coords


def minimise_rmsd(coords_1: ArrayLike, coords_2: ArrayLike,
                  mask_1: ArrayLike = [], mask_2: ArrayLike = [],
                  order_1: ArrayLike = [], order_2: ArrayLike = []) -> tuple[float, float, float, float]: # noqa
    '''
    Minimises the RMSD between two structures\n
    by rotating coords_1 onto coords_2\n
    If coords_1 and coords_2 are not the same length, then a mask array can be
    \nprovided for either/both and is applied prior to the calculation\n
    coords_1 and coords_2 can also be reordered if new orders are specified\n
    **note reordering occurs before masking**

    Parameters
    ----------
    coords_1: array_like
        xyz coordinates as (n_atoms, 3) array
    coords_2: array_like
        xyz coordinates as (n_atoms, 3) array
    mask_1: array_like
        0 (exclude) or 1 (include) for each element in coords_1
    mask_2: array_like
        0 (exclude) or 1 (include) for each element in coords_2
    order_1: array_like
        new indices for coords_1 - applied BEFORE masking
    order_2: array_like
        new indices for coords_2 - applied BEFORE masking

    Returns
    -------
    float
        Root mean square of norms of deviation between two structures
    float
        alpha angle in radians
    float
        beta angle in radians
    float
        gamma angle in radians
    '''

    coords_1 = np.asarray(coords_1)
    coords_2 = np.asarray(coords_2)

    # Set up new ordering
    if order_1:
        _order_1 = order_1
    else:
        _order_1 = range(len(coords_1))

    if order_2:
        _order_2 = order_2
    else:
        _order_2 = range(len(coords_2))

    # Apply new order
    _coords_1 = coords_1[_order_1]
    _coords_2 = coords_2[_order_2]

    # Set up masks
    if mask_1:
        _coords_1 = np.delete(_coords_1, mask_1, axis=0)

    # Set up masks
    if mask_2:
        _coords_2 = np.delete(_coords_2, mask_2, axis=0)

    # Fit alpha, beta, and gamma to minimise rmsd
    result = least_squares(
        lambda angs: _rotate_and_rmsd(
            angs, _coords_1, _coords_2
        ),
        x0=(1., 1., 1.),
        jac='3-point',
        gtol=np.finfo(float).eps,
        xtol=np.finfo(float).eps,
        ftol=np.finfo(float).eps
    )

    # Get optimum angles
    [alpha, beta, gamma] = result.x
    rmsd = result.fun[0]

    return rmsd, alpha, beta, gamma


def _rotate_and_rmsd(angs: ArrayLike, coords_1: ArrayLike,
                     coords_2: ArrayLike) -> NDArray:
    '''
    Rotates coords_1 by alpha, beta, gamma using the zyz convention\n
    https://easyspin.org/easyspin/documentation/eulerangles.html \n
    then calculates the rmsd between coords_1 and coords_2

    Parameters
    ----------
    angs: array_like
        alpha, beta, gamma in radians
    coords_1: array_like
        xyz coordinates as (n_atoms, 3) array of first system
    coords_2: array_like
        xyz coordinates as (n_atoms, 3) array of second system

    Returns
    -------
    ndarray of floats
        xyz coordinates as (n_atoms, 3) array after rotation\n
        in same order as input coordinates
    '''

    coords_1 = np.asarray(coords_1)
    coords_2 = np.asarray(coords_2)

    # Rotate coordinates of first system
    _coords_1 = rotate_coords(coords_1, angs[0], angs[1], angs[2])

    # Calculate rmsd between rotated first system and original second system
    rmsd = _calculate_rmsd(_coords_1, coords_2)

    return rmsd


def calculate_com(labels: ArrayLike, coords: ArrayLike) -> NDArray:
    '''
    Calculates centre-of-mass using relative atomic masses

    Parameters
    ----------
    labels: array_like
        list of atomic labels
    coords: array_like
        xyz coordinates as (n_atoms, 3) array

    Returns
    -------
    ndarray of floats
        xyz coordinates of centre of mass as (3) array
    '''

    coords = np.asarray(coords)

    labels_nn = remove_label_indices(labels)

    masses = [atomic.masses[lab] for lab in labels_nn]

    com_coords = np.zeros(3)

    for trio, mass in zip(coords, masses):
        com_coords += trio * mass

    com_coords /= np.sum(masses)

    return com_coords
