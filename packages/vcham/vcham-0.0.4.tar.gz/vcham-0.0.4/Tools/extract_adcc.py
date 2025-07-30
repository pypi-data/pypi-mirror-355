import glob
import os

######### Configuration parameters ######################


parse_gs = "CCSD total energy" # Change this to mp3 or mp2 as needed

number_of_excited_states = 8  # Number of excited states to extract (do not take into account the ground state)
number_of_modes = 12  # Number of modes to process

max_displacement = 100  # Maximum displacement value
min_displacement = -100  # Minimum displacement value
step_displacement = 2  # Step size for displacement

###########################################################



# # Remove existing data files
# for file in glob.glob("gs*.dat") + glob.glob("ce*.dat"):
#     os.remove(file)

def extract_data(filename):
    """Extract CCSD total energy and excited state values from an input file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    gs = None
    ex_roots = [None] * number_of_excited_states

    for i, line in enumerate(lines):
        if parse_gs in line:
            parts = line.strip().split()
            if parts:
                gs = parts[-1]
        if "(eV)" in line:
            for j in range(1, number_of_excited_states + 1):
                if i + j < len(lines):
                    root_line = lines[i + j].strip()
                    root_parts = root_line.split()
                    if len(root_parts) >= 4:
                        ex_roots[j - 1] = root_parts[3]

    return gs, ex_roots

if __name__ == "__main__":
    # Process each mode
    for mode in range(1, number_of_modes + 1):
        gs_data = []
        ex_data = [[] for _ in range(number_of_excited_states)]

        # Displacement loop from -100 to 100 in steps of 2
        for disp in range(min_displacement, max_displacement + 1, step_displacement):
            # Construct input file name based on displacement sign
            if disp < 0:
                inpgeo = f"geo_v{mode}_{disp:03d}.out"
            else:
                inpgeo = f"geo_v{mode}_{disp:02d}.out"
            
            # Process file if it exists
            if os.path.exists(inpgeo):
                gs, ex = extract_data(inpgeo)
                
                # Store CCSD total energy if found
                if gs is not None:
                    gs_data.append((disp, gs))

                # Store root values if any are found
                for i, root in enumerate(ex):
                    if root is not None:
                        ex_data[i].append((disp, root))

        # Write collected data to output files
        if gs_data:
            with open(f"gs_v{mode}.dat", 'w') as f:
                for disp, gs in gs_data:
                    f.write(f"{disp} {gs}\n")

        for i in range(number_of_excited_states):
            if ex_data[i]:
                with open(f"ce{i+1}_v{mode}.dat", 'w') as f:
                    for disp, root in ex_data[i]:
                        f.write(f"{disp} {root}\n")
