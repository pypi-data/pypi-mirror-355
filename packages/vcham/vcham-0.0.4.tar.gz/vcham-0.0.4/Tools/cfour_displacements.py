import numpy as np
import os

############## Variables to change ###############

inputfile = "../Examples/cfour_c2h2f2/output" # Output file from CFOUR frequency calculation
natoms    = 6        # Number of atoms of the molecule
is_linear = False    # Indicate whether the molecule is linear or not (for the number of modes)

min_displacement  = -10.0
max_displacement  =  10.0
step_displacement =   0.2

outputfile = "c2f2h2_geometries" # Output directory for the displaced geometries
##################################################


def parse_coordinates_and_masses(file_path):
    start_reading_symm = False
    start_reading_coords = False
    start_reading_masses = False
    coordinates = []
    atoms = []
    masses = []

    with open(file_path, 'r') as file:
        for line in file:
            if "The largest Abelian subgroup of the full molecular point" in line:
                start_reading_symm = True
                continue

            if "Coordinates (in bohr)" in line:
                start_reading_coords = True
                start_reading_masses = False
                # Skip the next two header lines
                next(file)
                next(file)
                continue
            
            if "masses used" in line:
                start_reading_masses = True
                start_reading_coords = False
                continue
            if start_reading_symm:
                parts = line.split()
                symm_point_grp = parts[-2]
                start_reading_symm = False

            if start_reading_coords:
                if line.strip() == "" or "-----" in line:  # End of the coordinate section
                    start_reading_coords = False
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    atom = parts[0]
                    x = float(parts[2])
                    y = float(parts[3])
                    z = float(parts[4])
                    atoms.append(atom)
                    coordinates.append([x, y, z])

            if start_reading_masses:
                if "Normal Coordinate Analysis" in line:  # End of the masses section
                    start_reading_masses = False
                    continue
                parts = line.split()
                for mass in parts:
                    masses.append(float(mass))

    coordinates_array = np.array(coordinates)
    atoms_array = np.array(atoms)
    masses_array = np.array(masses)
    return symm_point_grp, atoms_array, coordinates_array, masses_array


def parse_normal_coordinates(file_path, natoms, is_linear):
    start_reading = False
    frequencies = []
    full_normal_modes = []
    last_line_nmodes = []
    irreps = []
    num_modes = 3 * natoms - 5 if is_linear else 3 * natoms - 6

    with open(file_path, 'r') as file:
        for line in file:
            if "Normal Coordinates" in line:
                start_reading = True
                # next(file)  # Skip the empty line following "Normal Coordinates"
                continue
            
            if start_reading:
                full_blocks = num_modes // 3  # The modes are distributed in 3 columns
                last_block = None if (num_modes % 3) == 0 else (num_modes % 3)
                for _ in range(full_blocks):
                    irreps.extend(next(file).split())
                    freqs = [float(f) for f in next(file).split()]
                    frequencies.extend(freqs)
                    next(file)  # Skip the "VIBRATION" line

                    for _ in range(natoms):
                        line_nmode = next(file).split()[1:]  # Skip the atom label
                        line_nmode = [float(f) for f in line_nmode]
                        full_normal_modes.append(line_nmode)
                    
                    next(file)  # Skip the blank line at the end of the block
                full_normal_modes = np.array(full_normal_modes).reshape(full_blocks,9 * natoms) # 9 because there are 3nmodes in cartesian(xyz) per blockfull_blocks
                full_normal_modes = np.reshape(full_normal_modes, (full_blocks, natoms * 3, 3)) # making the blocks simpler
                
                if last_block:
                    irreps.extend(next(file).split())
                    freqs = [float(f) for f in next(file).split()]
                    frequencies.extend(freqs)
                    next(file)  # Skip the "VIBRATION" line

                    for _ in range(natoms):
                        line_nmode = next(file).split()[1:]  # Skip the atom label
                        line_nmode = [float(f) for f in line_nmode]
                        last_line_nmodes.append(line_nmode)
                    last_line_nmodes = np.array(last_line_nmodes).reshape(-1) # all data in a line
                    last_line_nmodes = np.reshape(last_line_nmodes,(natoms * last_block,3)) # Same structure as before 

                start_reading = False
    arr_nmodes_reshap = []
    for block in range(full_blocks):
        arr_full_lines = [[] for _ in range(3)]
        for idx in range(natoms):
            arr_full_lines[0].append(full_normal_modes[block][0+idx*3])
            arr_full_lines[1].append(full_normal_modes[block][1+idx*3])
            arr_full_lines[2].append(full_normal_modes[block][2+idx*3])
        arr_full_lines = np.array(arr_full_lines)
        arr_nmodes_reshap.extend(arr_full_lines)
    if last_block:
        arr_last_lines = [[] for _ in range(last_block)]
        if last_block == 2:
            for idx in range(natoms):
                print(last_line_nmodes[0+idx*2])
                arr_last_lines[0].append(last_line_nmodes[0+idx*2])
                arr_last_lines[1].append(last_line_nmodes[1+idx*2])
        else:
            for idx in range(natoms):
                arr_last_lines[0].append(last_line_nmodes[0+idx])
        arr_nmodes_reshap.extend(arr_last_lines)
    arr_nmodes_reshap = np.array(arr_nmodes_reshap)

    frequencies_array = np.array(frequencies)
    normal_modes_array = np.array(arr_nmodes_reshap)
    irreps_array = np.array(irreps)
    
    return irreps_array, frequencies_array, normal_modes_array



# Calculate reduced mass for each mode
def reduced_mass_calculation(normal_modes_array):
    """
    Calculate the reduced mass for each normal mode.

    Parameters:
    normal_modes_array (numpy.ndarray): Array of normal modes. Each row represents a mode.
    masses_array (numpy.ndarray): Array of atomic masses corresponding to each atom.

    Returns:
    numpy.ndarray: Array of reduced masses for each mode.
    """

    red_mass = np.zeros(len(normal_modes_array))
    for i, mode in enumerate(normal_modes_array):
        # Calculate the reduced mass for the mode
        suma = np.sum(mode**2 / masses_array[:,np.newaxis])
        red_mass[i] = 1 / suma
    return red_mass


def cfour_to_gaussian_normal_modes(normal_modes_array, masses_array, red_mass):
    """
    Convert normal modes from CFOUR format to Gaussian format.

    Parameters:
    normal_modes_array (numpy.ndarray): Tensor of normal modes.
    red_mass (numpy.ndarray): Array of reduced masses for each mode.
    masses_array (numpy.ndarray): Array of atomic masses corresponding to each atom.

    Returns:
    numpy.ndarray: Transformed normal modes in Gaussian format.
    """
    new_modes = np.empty_like(normal_modes_array)
    red_mass_sqrt = np.sqrt(red_mass)

    for idx, mode in enumerate(normal_modes_array):
        # Transform the mode by applying the reduced mass scaling and mass normalization
        new_modes[idx] = mode * red_mass_sqrt[idx] / np.sqrt(masses_array[:,np.newaxis])
    return new_modes


def calculate_znorm_and_zred(new_modes, masses_array):
    """
    Calculate znorm and zred for the given normal modes and masses.

    Parameters:
    new_modes (numpy.ndarray): Array of normal modes. Each row represents a mode.
    masses_array (numpy.ndarray): Array of atomic masses corresponding to each atom.

    Returns:
    tuple: znorm and zred arrays.
    """
    # Initialize arrays to store the results
    znorm = np.empty(new_modes.shape[0])
    zred  = np.empty(new_modes.shape[0])    
    # Calculate znorm and zred for each mode
    for idx, mode in enumerate(new_modes):
        mode2 = mode * mode  # Element-wise square of the mode
        znorm[idx] = np.sum(mode2)  # Sum of squared components
        zred[idx]  = np.sum(mode2 * masses_array[:,np.newaxis])  # Sum of squared components weighted by the masses
    
    return znorm, zred


    
def save_displacements_dat(output_path, dimless_disp, opt_geo, start=-8, end=8, step=0.5):
    """
    Generate and save displaced geometries based on dimensionless displacements.

    Args:
        output_path (str): Base path for saving output files.
        dimless_disp (np.array): Array of dimensionless displacements.
        opt_geo (np.array): Array of optimized geometry coordinates.
        start (float): Starting value for displacement.
        end (float): Ending value for displacement.
        step (float): Step size for displacement.

    Returns:
        str: Confirmation message upon completion.
    """

    if not isinstance(dimless_disp, np.ndarray) or not isinstance(opt_geo, np.ndarray):
        raise TypeError("Dimensionless displacements and optimized geometry must be NumPy arrays.")
    
    if not os.path.exists(output_path):
        # Create the directory
        os.makedirs(output_path)
        print(f"Directory '{output_path}' created successfully!")
    else:
        print(f"Directory '{output_path}' already exists.")

    displacement = np.arange(start, end + step, step)

    for i, nmode in enumerate(dimless_disp):
        for j, a in enumerate(range(int(start*10), int(end*10) + int(step*10), int(step*10))):
        # for disp in displacement:
            geo = opt_geo + displacement[j] * nmode
            name_pos = f"{a:02d}"
            name_neg = f"{a:03d}"
            file_name = f"geo_v{i+1}_{name_neg}.dat" if displacement[j] < -1e-8 else f"geo_v{i+1}_{name_pos}.dat"
            file_path = os.path.join(output_path, file_name)
            np.savetxt(file_path, geo, fmt='%.6f')
    return "\nDIMENSIONLESS DISPLACEMENTS ALONG NORMAL MODES SUCCESSFULLY DONE.\n"

def save_displacements_xyz(output_path, dimless_disp, opt_geo, chemical_elements, start=-8, end=8, step=0.5, ghost=False):
    """
    Generate and save displaced geometries based on dimensionless displacements.

    Args:
        output_path (str): Base path for saving output files.
        dimless_disp (np.array): Array of dimensionless displacements.
        opt_geo (np.array): Array of optimized geometry coordinates.
        start (float): Starting value for displacement.
        end (float): Ending value for displacement.
        step (float): Step size for displacement.

    Returns:
        str: Confirmation message upon completion.
    """

    if not isinstance(dimless_disp, np.ndarray) or not isinstance(opt_geo, np.ndarray):
        raise TypeError("Dimensionless displacements and optimized geometry must be NumPy arrays.")

    if not os.path.exists(output_path):
        # Create the directory
        os.makedirs(output_path)
        print(f"Directory '{output_path}' created successfully!")
    else:
        print(f"Directory '{output_path}' already exists.")

    displacement = np.arange(start, end + step, step)
    num_atoms = len(chemical_elements) + 1 if ghost else len(chemical_elements)
    other_basis = False

    for i, nmode in enumerate(dimless_disp):
        for j, a in enumerate(range(int(start * 10), int(end * 10) + int(step * 10), int(step * 10))):
            geo = opt_geo + displacement[j] * nmode
            name_pos = f"{a:02d}"
            name_neg = f"{a:03d}"
            file_name = f"geo_v{i+1}_{name_neg}.xyz" if displacement[j] < -1e-8 else f"geo_v{i+1}_{name_pos}.xyz"
            file_path = os.path.join(output_path, file_name)

            # Prepare the content for the .xyz file
            with open(file_path, 'w') as file:
                file.write(f"{num_atoms}\n\n")  # Write number of atoms and a blank line
                if ghost:
                    file.write("ghost 0.000000 0.000000 0.000000\n")
                for element, coord in zip(chemical_elements, geo):
                    basis = None
                    if other_basis:
                        if element == "C":
                            basis =".ANO-RCC...4s3p2d."
                        elif element == "H":
                            basis =".ANO-RCC...2s1p."
                        elif element == "F":
                            basis =".ANO-RCC...4s3p2d1f."
                    file.write(f"{element}{basis} {coord[0]:.6f} {coord[1]:.6f} {coord[2]:.6f}\n")

    return "\nDIMENSIONLESS DISPLACEMENTS ALONG NORMAL MODES SUCCESSFULLY DONE.\n"

if __name__ == "__main__":
    # Constants
    BOHR_TO_ANG    = 0.529177210903      # Bohr radious to Anstrom
    HARTREE_TO_CM1 = 219474.63136320     # Hartree to cm-1
    AMU_TO_AU      = 5.485799090441e-4   # AMU to au

    C1C3C4 = BOHR_TO_ANG * np.sqrt(HARTREE_TO_CM1* AMU_TO_AU)

    if not os.path.exists(inputfile):
        raise FileNotFoundError(f"The input file '{inputfile}' does not exist. It should be the output file from a CFOUR frequency calculation.")
    # Check if the input file is empty
    if os.path.getsize(inputfile) == 0:
        raise ValueError(f"The input file '{inputfile}' is empty. Please provide a valid CFOUR output file.")

    # Get symmetry point group, atoms, reference geometry and masses from CFOUR output
    symm_point_grp, atoms_array, ref_geom, masses_array = parse_coordinates_and_masses(inputfile)
    print("Symmetry point group in CFOUR:\n", symm_point_grp)
    print("\nAtoms:\n", atoms_array)
    print("\nReference coordinate (bohr):\n", ref_geom)
    print("\nMasses (AMU):\n", masses_array)

    # Get irreducible representations, frequencies and normal modes from CFOUR output
    irreps_array, frequencies_array, cfour_modes = parse_normal_coordinates(inputfile, natoms, is_linear)
    print("\nIrreducible Representations of the normal modes:\n", irreps_array)
    print("\nFrequencies (cm^{-1}):\n", frequencies_array)
    print("\nNormal modes:\n", cfour_modes)

    # Calculate reduced mass of the modes
    red_mass = reduced_mass_calculation(cfour_modes)

    # Transform CFOUR normal modes into Gaussian normal modes
    gaussian_modes = cfour_to_gaussian_normal_modes(cfour_modes, masses_array, red_mass)

    # Check that is correct
    znorm, zred = calculate_znorm_and_zred(gaussian_modes, masses_array)
    print(f"\nIf it is correct it should give a ones array:\n {znorm}")
    print(f"\nIf it is correct it should give the reduced mass array:\n {zred}")

    # Dimensionless displacements along normal modes
    runit = C1C3C4 / np.sqrt(red_mass * frequencies_array)
    dimless_disp = gaussian_modes * runit[:,np.newaxis, np.newaxis]
    ref_geom = ref_geom * BOHR_TO_ANG 

    # Save displacements in .dat format
    # save_displacements_dat(outputfile, dimless_disp, ref_geom, min_displacement, max_displacement, step_displacement)

    # Save displacements in .xyz format
    save_displacements_xyz(outputfile, dimless_disp, ref_geom, atoms_array, min_displacement, max_displacement, step_displacement, ghost=False)



