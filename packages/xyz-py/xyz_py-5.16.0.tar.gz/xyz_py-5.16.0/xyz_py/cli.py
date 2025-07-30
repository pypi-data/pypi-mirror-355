'''
This is the main the command line interface to xyz_py
'''

import argparse
import numpy as np
import numpy.linalg as la
import os
import sys

from . import xyz_py
from . import atomic


def origin_func(uargs):
    '''
    Wrapper for cli call to get set atom at origin

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''

    # Load data
    labels, coords = xyz_py.load_xyz(uargs.xyz_file)
    comment = xyz_py.load_xyz_comment(uargs.xyz_file)

    labels_nn = xyz_py.remove_label_indices(labels)

    # If specified atom has no index, check for duplicates in xyz file
    if xyz_py.remove_label_indices(uargs.central_atom) == uargs.central_atom:
        matches = [
            it
            for it, labnn in enumerate(labels_nn)
            if labnn == uargs.central_atom
        ]
    else:
        matches = [
            it
            for it, lab in enumerate(labels)
            if lab == uargs.central_atom
        ]

    if len(matches) == 0:
        cprint('Error: cannot find specified atom in file', 'red')
        sys.exit(1)
    elif len(matches) > 1:
        cprint(
            (
                'Error: Multiple of specified atom found, perhaps try using '
                'indexing? e.g. Cr1'
            ),
            'red'
        )

    # Shift coords
    coords -= coords[matches[0]]

    # Save new file
    xyz_py.save_xyz(uargs.xyz_file, labels, coords, comment=comment)

    return


def inertia_tensor_func(uargs):
    '''
    Wrapper for cli call to get inertia tensor and eigenvectors/values

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''

    labels, coords = xyz_py.load_xyz(uargs.xyz_file)

    com_coords = coords - xyz_py.calculate_com(labels, coords)
    atomic_masses = np.array(
        [
            atomic.masses[lab]
            for lab in xyz_py.remove_label_indices(labels)
        ]
    )

    itensor = np.zeros([3, 3])

    itensor[0, 0] = np.sum(
        atomic_masses * (com_coords[:, 1]**2 + com_coords[:, 2]**2)
    )
    itensor[0, 1] = -np.sum(
        atomic_masses * com_coords[:, 0] * com_coords[:, 1]
    )
    itensor[0, 2] = -np.sum(
        atomic_masses * com_coords[:, 0] * com_coords[:, 2]
    )
    itensor[1, 1] = np.sum(
        atomic_masses * (com_coords[:, 0]**2 + com_coords[:, 2]**2)
    )
    itensor[1, 2] = -np.sum(
        atomic_masses * com_coords[:, 1] * com_coords[:, 2]
    )
    itensor[2, 2] = np.sum(
        atomic_masses * (com_coords[:, 0]**2 + com_coords[:, 1]**2)
    )
    itensor += np.triu(itensor, 1).transpose()

    values, vecs = la.eigh(itensor)

    print('Inertia Tensor (AMU angs^2):')
    print(itensor)

    print('Eigenvalues (AMU angs^2):')
    print(values)

    print('Eigenvectors:')
    print(vecs)

    return


def struct_info_func(uargs):
    '''
    Wrapper for cli call to get_ bonds, dihedrals and angles

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''
    formatting = xyz_py.detect_xyz_formatting(uargs.xyz_file)

    try:
        labels, coords = xyz_py.load_xyz(
            uargs.xyz_file,
            missing_headers=formatting['missing_headers'],
            atomic_numbers=formatting['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    f_head = os.path.splitext(uargs.xyz_file)[0]

    if uargs.cutoffs:
        cutoffs = parse_cutoffs(uargs.cutoffs)
    else:
        cutoffs = {}

    # Generate neighbourlist
    neigh_list = xyz_py.get_neighborlist(
        labels,
        coords,
        adjust_cutoff=cutoffs
    )

    # Get bonds
    bond_labels, bond_lengths = xyz_py.find_bonds(
        labels,
        coords,
        style='labels',
        neigh_list=neigh_list,
        verbose=not uargs.quiet
    )

    bonds = np.array([
        '{}-{}, {:.7f}'.format(*label, value)
        for label, value in zip(bond_labels, bond_lengths)
    ])

    if uargs.save:
        # Save to file
        np.savetxt(
            f'{f_head}_bonds.csv',
            bonds,
            fmt='%s',
            header='label, length (Angstrom)'
        )
    else:
        print('Bonds:')
        for bond in bonds:
            print(bond)
        print()

    # Get angles
    angle_labels, angle_values = xyz_py.find_angles(
        labels,
        coords,
        style='labels',
        neigh_list=neigh_list,
        verbose=not uargs.quiet
    )

    if uargs.radians:
        ang_conv = np.pi / 180.
    else:
        ang_conv = 1.

    angles = [
        '{}-{}-{}, {:.7f}'.format(*label, value * ang_conv)
        for label, value in zip(angle_labels, angle_values)
    ]

    if uargs.save and len(angles):
        # Save to file
        np.savetxt(
            f'{f_head}_angles.csv',
            angles,
            fmt='%s',
            header='label, angle (degrees)'
        )
    elif len(angles):
        print('Angles:')
        for angle in angles:
            print(angle)
        print()

    # Get dihedrals
    dihedral_labels, dihedral_values = xyz_py.find_dihedrals(
        labels,
        coords,
        style='labels',
        neigh_list=neigh_list,
        verbose=not uargs.quiet
    )

    dihedrals = np.array([
        '{}-{}-{}-{}, {:.7f}'.format(*label, value * ang_conv)
        for label, value in zip(dihedral_labels, dihedral_values)
    ])

    if uargs.save and len(dihedrals):
        # Save to file
        np.savetxt(
            f'{f_head}_dihedrals.csv',
            dihedrals,
            fmt='%s',
            header='label, dihedral angle (degrees)'
        )
    elif len(dihedrals):
        print('Dihedrals:')
        for dihedral in dihedrals:
            print(dihedral)
        print()

    if not uargs.quiet and uargs.save:
        msg = 'Bonds'
        if len(angles):
            msg += ', angles'
        if len(dihedrals):
            msg += ', and dihedrals'
        msg += f' written to {f_head}_<property>.csv'
        print(msg)

    return


def rotate_func(uargs):
    '''
    Wrapper for cli call to rotate

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''
    formatting = xyz_py.detect_xyz_formatting(uargs.xyz_file)

    try:
        labels, coords = xyz_py.load_xyz(
            uargs.xyz_file,
            missing_headers=formatting['missing_headers'],
            atomic_numbers=formatting['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    # Load comment line
    if not formatting['missing_headers']:
        comment = xyz_py.load_xyz_comment(uargs.xyz_file)
    else:
        comment = ''

    if uargs.angles:
        if not uargs.radians:
            uargs.angles = np.array(uargs.angles) * 180. / np.pi

        rotated_coords = xyz_py.rotate_coords(
            coords,
            uargs.angles[0],
            uargs.angles[1],
            uargs.angles[2]
        )
    elif uargs.matrix:
        matrix = np.loadtxt(uargs.matrix)
        if matrix.shape != (3, 3):
            red_exit('Error: rotation matrix must be 3x3')
        if uargs.radians:
            red_exit('Error: rotation matrix cannot be in radians')
        rotated_coords = (matrix @ coords.T).T

    if uargs.out_f_name:
        out_f_name = uargs.out_f_name
    else:
        out_f_name = '{}_rotated.xyz'.format(
            os.path.splitext(uargs.xyz_file)[0]
        )

    xyz_py.save_xyz(out_f_name, labels, rotated_coords, comment=comment)

    return


def overlay_func(uargs):
    '''
    Wrapper for cli call to overlay

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''

    formatting_1 = xyz_py.detect_xyz_formatting(uargs.xyz_file_1)

    try:
        labels_1, coords_1 = xyz_py.load_xyz(
            uargs.xyz_file_1,
            missing_headers=formatting_1['missing_headers'],
            atomic_numbers=formatting_1['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    formatting_2 = xyz_py.detect_xyz_formatting(uargs.xyz_file_2)

    try:
        labels_2, coords_2 = xyz_py.load_xyz(
            uargs.xyz_file_2,
            missing_headers=formatting_2['missing_headers'],
            atomic_numbers=formatting_2['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    if len(labels_1) != len(labels_2):
        red_exit("Error: Files must have same number of atoms")

    coords_1 -= coords_1[0]
    coords_2 -= coords_2[0]

    rmsd, alpha, beta, gamma = xyz_py.minimise_rmsd(
        coords_1, coords_2
    )

    print(f'RMSD between structures is {rmsd:.4f}')

    _coords_1 = xyz_py.rotate_coords(coords_1, alpha, beta, gamma)

    out_coords = np.vstack([_coords_1, coords_2])

    out_labels = labels_1 + labels_2

    out_f_name = 'overlayed.xyz'

    xyz_py.save_xyz(out_f_name, out_labels, out_coords)

    return


def list_form_func(uargs):
    '''
    Wrapper for cli call to find_entities

    Parameters
    ----------
        uargs : argparser object
            command line arguments

    Returns
    -------
        None

    '''

    formatting = xyz_py.detect_xyz_formatting(uargs.xyz_file)

    try:
        labels, coords = xyz_py.load_xyz(
            uargs.xyz_file,
            missing_headers=formatting['missing_headers'],
            atomic_numbers=formatting['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    labels = xyz_py.add_label_indices(labels)

    if uargs.cutoffs:
        cutoffs = parse_cutoffs(uargs.cutoffs)
    else:
        cutoffs = {}

    entities_dict = xyz_py.find_entities(
        labels, coords, adjust_cutoff=cutoffs, non_bond_labels=uargs.no_bond
    )

    for key, val in entities_dict.items():
        print('{} : {:d}'.format(key, len(val)))

    return


def renumber_func(uargs):
    '''
    Wrapper for cli call to renumber
    '''

    formatting = xyz_py.detect_xyz_formatting(uargs.xyz_file)

    try:
        labels, c = xyz_py.load_xyz(
            uargs.xyz_file,
            missing_headers=formatting['missing_headers'],
            atomic_numbers=formatting['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    # Load comment line
    if not formatting['missing_headers']:
        comment = xyz_py.load_xyz_comment(uargs.xyz_file)
    else:
        comment = ''

    # Remove existing labels
    labels = xyz_py.remove_label_indices(labels)

    # Add new labels
    labels = xyz_py.add_label_indices(labels, style=uargs.style)

    # Save new xyz file
    xyz_py.save_xyz(uargs.xyz_file, labels, c, comment=comment)

    return


def denumber_func(uargs):
    '''
    Wrapper for cli call to denumber
    '''

    formatting = xyz_py.detect_xyz_formatting(uargs.xyz_file)

    try:
        labels, c = xyz_py.load_xyz(
            uargs.xyz_file,
            missing_headers=formatting['missing_headers'],
            atomic_numbers=formatting['atomic_numbers']
        )
    except (ValueError, xyz_py.XYZError) as err:
        red_exit(str(err))

    # Load comment line
    if not formatting['missing_headers']:
        comment = xyz_py.load_xyz_comment(uargs.xyz_file)
    else:
        comment = ''

    # Remove existing labels
    labels = xyz_py.remove_label_indices(labels)

    # Save new xyz file
    xyz_py.save_xyz(uargs.xyz_file, labels, c, comment=comment)

    return


def parse_cutoffs(cutoffs):

    if len(cutoffs) % 2:
        raise argparse.ArgumentTypeError('Error, cutoffs should come in pairs')

    for it in range(1, len(cutoffs), 2):
        try:
            float(cutoffs[it])
        except ValueError:
            raise argparse.ArgumentTypeError(
                'Error, second part of cutoff pair should be float'
            )

    parsed = {}

    for it in range(0, len(cutoffs), 2):

        parsed[cutoffs[it].capitalize()] = float(cutoffs[it + 1])

    return parsed


def read_args(arg_list=None):
    '''
    Parser for command line arguments. Uses subparsers for individual programs

    Parameters
    ----------
        args : argparser object
            command line arguments

    Returns
    -------
        None

    '''

    description = '''
    A package for manipulating xyz files and chemical structures
    '''

    epilog = '''
    To display options for a specific program, use xyz_py PROGRAMNAME -h
    '''

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='prog')

    shift_origin = subparsers.add_parser(
        'origin',
        description=(
            'Translate all coordinates such that specified atom is at origin'
        )
    )
    shift_origin.set_defaults(func=origin_func)

    shift_origin.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    shift_origin.add_argument(
        'central_atom',
        type=str,
        help='Atom whose coordinates define new origin'
    )

    inertia_tensor = subparsers.add_parser(
        'inertia',
        description=(
            'Calculates and diagonalises inertia tensor for given xyz file.'
            '(Uses relative atomic masses)'
        )
    )
    inertia_tensor.set_defaults(func=inertia_tensor_func)

    inertia_tensor.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    struct_info = subparsers.add_parser(
        'struct_info',
        description=(
            'Extracts structural information (bonds, angles and '
            'dihedrals) from xyz file'
        )
    )
    struct_info.set_defaults(func=struct_info_func)

    struct_info.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    struct_info.add_argument(
        '-s',
        '--save',
        action='store_true',
        help='Save data to file rather than printing to screen'
    )

    struct_info.add_argument(
        '--cutoffs',
        type=str,
        nargs='+',
        default=[],
        metavar=['symbol', 'cutoff'],
        help='Change cutoff for symbol to cutoff e.g. Gd 2.5'
    )

    struct_info.add_argument(
        '-r', '--radians',
        action='store_true',
        help='Use radians instead of degrees'
    )

    struct_info.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress file location print to screen'
    )

    rotate = subparsers.add_parser(
        'rotate',
        description=(
            'Rotate xyz file either rotation matrix in file, or by '
            'specifying Euler angles in Easyspin convention'
        )
    )
    rotate.set_defaults(func=rotate_func)

    rotate.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    rotation_specifier = rotate.add_mutually_exclusive_group(required=True)

    rotation_specifier.add_argument(
        '--angles',
        type=float,
        nargs=3,
        help='Angles, alpha, beta, gamma in degrees, separated by spaces'
    )

    rotation_specifier.add_argument(
        '--matrix',
        type=str,
        help='Rotation matrix in file, applied as xnew = R.x'
    )

    rotate.add_argument(
        '-r', '--radians',
        action='store_true',
        help='Use radians instead of degrees'
    )

    rotate.add_argument(
        '--out_f_name',
        type=str,
        metavar='file_name',
        help='Output file name - default is append xyz file with _rotated'
    )

    overlay = subparsers.add_parser(
        'overlay',
        description=(
            'Overlay two xyz files by rotating file_1 onto file_2'
            'Files MUST have the same number of atoms, and the same order'
        )
    )
    overlay.set_defaults(func=overlay_func)

    overlay.add_argument(
        'xyz_file_1',
        type=str,
        help=(
            'File containing xyz coordinates in .xyz format - this structure'
            'will be rotated onto the second file'
        )
    )

    overlay.add_argument(
        'xyz_file_2',
        type=str,
        help=(
            'File containing xyz coordinates in .xyz format'
        )
    )

    list_form = subparsers.add_parser(
        'list_formulae',
        description=(
            'Finds bonded entities in xyz file using adjacency, and '
            'prints their formula and number of ocurrences'
        )
    )
    list_form.set_defaults(func=list_form_func)

    list_form.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    list_form.add_argument(
        '--cutoffs',
        type=str,
        nargs='+',
        metavar='symbol number',
        help='Modify cutoff used to define bonds'
    )

    list_form.add_argument(
        '--no_bond',
        type=str,
        default=[],
        nargs='+',
        metavar='symbol',
        help='Atom labels specifying atoms to which no bonds can be formed'
    )

    renumber = subparsers.add_parser(
        'renumber',
        description=(
            '(Re)numbers atom labels in file'
        )
    )
    renumber.set_defaults(func=renumber_func)

    renumber.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    renumber.add_argument(
        '--style',
        type=str,
        default='per_element',
        choices=['per_element', 'sequential'],
        help=(
            'per_element : Index by element e.g. Dy1, Dy2, N1, N2, etc.'
            'sequential : Index the atoms 1->N'
        )
    )

    denumber = subparsers.add_parser(
        'denumber',
        description=(
            '(Re)numbers atom labels in file'
        )
    )
    denumber.set_defaults(func=denumber_func)

    denumber.add_argument(
        'xyz_file',
        type=str,
        help='File containing xyz coordinates in .xyz format'
    )

    # If arg_list==None, i.e. normal cli usage, parse_args() reads from
    # 'sys.argv'. The arg_list can be used to call the argparser from the
    # back end.

    # read sub-parser
    parser.set_defaults(func=lambda args: parser.print_help())
    args = parser.parse_args(arg_list)
    args.func(args)


def cstr(string: str, color: str):
    '''
    Produces colorised string

    Parameters
    ----------
    string: str
        String to print
    color: str {'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                'black_yellowbg', 'black_bluebg'}
        String name of color

    Returns
    -------
    str
        Input string with colours
    '''

    ccodes = {
        'red': '\u001b[31m',
        'green': '\u001b[32m',
        'yellow': '\u001b[33m',
        'blue': '\u001b[34m',
        'magenta': '\u001b[35m',
        'cyan': '\u001b[36m',
        'white': '\u001b[37m',
        'black_yellowbg': '\u001b[30;43m\u001b[K',
        'black_bluebg': '\u001b[30;44m\u001b[K',
    }
    end = '\033[0m\u001b[K'

    # Count newlines at neither beginning nor end
    num_c_nl = string.rstrip('\n').lstrip('\n').count('\n')

    # Remove right new lines to count left new lines
    num_l_nl = string.rstrip('\n').count('\n') - num_c_nl
    l_nl = ''.join(['\n'] * num_l_nl)

    # Remove left new lines to count right new lines
    num_r_nl = string.lstrip('\n').count('\n') - num_c_nl
    r_nl = ''.join(['\n'] * num_r_nl)

    # Remove left and right newlines, will add in again later
    _string = string.rstrip('\n').lstrip('\n')

    out = '{}{}{}{}{}'.format(l_nl, ccodes[color], _string, end, r_nl)

    return out


def can_float(s: str) -> bool:
    '''
    For a given string, checks if conversion to float is possible

    Parameters
    ----------
    s: str
        string to check

    Returns
    -------
    bool
        True if value can be converted to float
    '''
    out = True
    try:
        s = float(s.strip())
    except ValueError:
        out = False

    return out


def cprint(string: str, color: str):
    '''
    Prints colored output to screen

    Parameters
    ----------
    string: str
        String to print
    color: str {'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                'black_yellowbg', 'black_bluebg'}
        String name of color

    Returns
    -------
    None
    '''

    return print(cstr(string, color))


def red_exit(string: str):
    cprint(string, 'red')
    sys.exit(-1)


def main():
    read_args()
