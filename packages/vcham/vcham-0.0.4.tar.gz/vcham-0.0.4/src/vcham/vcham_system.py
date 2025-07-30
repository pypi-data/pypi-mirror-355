import numpy as np
import os
from typing import Any, Dict, List, Optional, Union, Tuple
from .logging_config import get_logger
from .symm_vcham import SymmetryMask

logger = get_logger(__name__)


class VCSystem:
    """
    Initialize the VCSystem object.

    Attributes
    ----------
    elements : list of str, optional
        List of element symbols in the system.
    reference_geometry : np.ndarray, optional
        Reference geometry of the system, given as a NumPy array of shape (n_atoms, 3).
    vc_type : str, default "linear"
        Type of the vibrational coupling system, e.g., "linear", "quadratic", etc.
    units : str, default "eV"
        Units for the energy and frequency values, e.g., "eV", "Hartree", etc.
    number_normal_modes : int, optional
        Number of normal modes in the system.
    number_states : int, optional
        Number of electronic states considered in the system.
    displacement_vector : list of np.ndarray, optional
        List of displacement vectors for each normal mode, where each vector is a NumPy array.
    database_abinitio : list of np.ndarray, optional
        List of ab initio data arrays, where each array corresponds to a state and contains energy values for different displacements.
        It is a list of NumPy arrays, each of shape (n_states, n_displacements). Overall shape is (number_normal_modes, number_states, n_displacements).
    coupling_with_gs : bool, optional
        Whether the system is coupled with the ground state (GS).
        If not provided, it will be initialized as True. It is useful for highly excited states.
    symmetry_point_group : str, optional
        The point group symmetry of the system, e.g., "C2v", "Cs", etc.
    totally_sym_irrep : str, optional
        The totally symmetric irreducible representation of the system. It is automatically computed from the symmetry point group.
    symmetry_modes : list of str, optional
        List of irreps corresponding to the normal modes.
    symmetry_states : list of str, optional
        List of irreps corresponding to the electronic states.
    vib_freq : np.ndarray, optional
        Vibrational frequencies for the normal modes, given as a NumPy array.
    energy_shift : np.ndarray, optional
        Energy shifts for the states, given as a NumPy array. It is computed from the ab initio database.
    vcham : list of np.ndarray, optional
        List of vibrational coupling Hamiltonian matrices, where each matrix is a NumPy array.
        It is used to store the Hamiltonian for each normal mode.
    diab_funct : list of str, optional
        List of diabatic function names for each normal mode.
    symmetry_matrix : list of np.ndarray, optional
        List of symmetry matrices, where each matrix is a NumPy array.
        It is used to store the symmetry operations for the system. It is computed from the symmetry variables.
    jt_effects : list of dict, optional
        List of Jahn-Teller (JT) effects, where each effect is a dictionary containing:
        - 'mode': int, the index of the normal mode.
        - 'state_pairs': list, pairs of states coupled by the JT effect.
        - 'types': list, JT effect types for each state pair.
        Optionally, if a JT effect is inactive ('active': False), it must include:
        - 'source': int, the mode index to copy parameters from.
    dipole_matrix : list of np.ndarray, optional
        List of dipole matrices, where each matrix is a NumPy array.
        It is used to store the dipole moments for the system. The dimensions of the dipole matrix should be (n_states, n_states, 3).

     """
    def __init__(
        self,
        elements: List[str] = None,
        reference_geometry: Optional[np.ndarray] = None,
        vc_type: str = "linear",
        units: str = "eV",
        number_normal_modes: Optional[int] = None,
        number_states: Optional[int] = None,
        displacement_vector: Optional[List[Union[np.ndarray, Any]]] = None,
        database_abinitio: Optional[List[Union[np.ndarray, Any]]] = None,
        coupling_with_gs: Optional[bool] = True,
        symmetry_point_group: Optional[str] = None,
        totally_sym_irrep: Optional[str] = None,
        symmetry_modes: Optional[List[str]] = None,
        symmetry_states: Optional[List[str]] = None,
        vib_freq: Optional[np.ndarray] = None,
        energy_shift: Optional[np.ndarray] = None,
        vcham: Optional[List[np.ndarray]] = None,
        diab_funct: Optional[List[str]] = None,
        symmetry_matrix: Optional[List[np.ndarray]] = None,
        jt_effects: Optional[List[Dict[str, Any]]] = None,
        dipole_matrix: Optional[List[np.ndarray]] = None,
    ):

        self.atomic_weights: Dict[str, float] = {
            "H": 1.00782503223, 
            "He": 4.00260325413,
            "Li": 6.938,        
            "Be": 9.0121831,    
            "B": 10.806,        
            "C": 12.0096,       
            "N": 14.00643,      
            "O": 15.99903,      
            "F": 18.998403163,  
            "Ne": 20.1797,      
            "Na": 22.98976928,  
            "Mg": 24.304,       
            "Al": 26.9815385,   
            "Si": 28.084,       
            "P": 30.973761998,  
            "S": 32.059,        
            "Cl": 35.446,       
            "Ar": 39.792,
            "X" : 1.0,  # Placeholder for unknown elements
            "Ghost": 1.0,  # Placeholder for ghost atoms       
        }
        # Basic parameters
        self.vc_type = vc_type
        self.units = units
        self.number_normal_modes = number_normal_modes
        self.number_states = number_states
        self.vib_freq = vib_freq
        # The energy shift passed in is replaced by the computed shift below.
        self.energy_shift = energy_shift

        # Input data lists are defaulted to empty lists if not provided.
        self.displacement_vector = displacement_vector or []
        self.database_abinitio = database_abinitio or []

        # Symmetry-related variables
        self.coupling_with_gs = coupling_with_gs
        self.symmetry_point_group = symmetry_point_group
        self.totally_sym_irrep = totally_sym_irrep.upper() if totally_sym_irrep else None
        self.symmetry_modes = symmetry_modes or []
        self.symmetry_states = symmetry_states or []
        self.symmetry_matrix = symmetry_matrix

        # Jahn-Teller effect parameters
        self.jt_effects = jt_effects
        self.jt_params: Dict[int, Any] = {}  # Stores JT parameters keyed by mode.
        self.dipole_matrix = dipole_matrix

        # Additional data storage for output and optimization
        self.summary_output: List[Any] = []
        self.optimized_params: List[Any] = []

        # Parameters for fitting
        self.vcham = vcham
        self.diab_funct = diab_funct

        self.reference_geometry = reference_geometry
        self.elements = elements

        # Validate essential inputs and convert arrays where needed.
        self._validate_essential_inputs()

        # Compute energy shifts from the ab initio database.
        self.energy_shift = self._find_energy_shifts()

        # Create lvc_data dictionary containing all relevant information.
        self.lvc_data = self._get_lvc_data()

        # Initialize dictionaries/lists that depend on the number of normal modes.
        if self.number_normal_modes is None:
            logger.error("number_normal_modes must be provided.")
            raise ValueError("number_normal_modes must be provided.")

        self.idx_dict = {
            "jt_on": [[] for _ in range(self.number_normal_modes)],
            "jt_off": [[] for _ in range(self.number_normal_modes)],
            "kappa": [[] for _ in range(self.number_normal_modes)],
            "lambda": [[] for _ in range(self.number_normal_modes)],
        }
        # Initialize the number of diabatic parameters for each mode and state.
        self.n_diab_params = [
            [0 for _ in range(self.number_states)] for _ in range(self.number_normal_modes)
        ]
        # Pre-allocate output storage lists per mode.
        self.summary_output = [[] for _ in range(self.number_normal_modes)]
        self.optimized_params = [[] for _ in range(self.number_normal_modes)]

    def add_geometry(self, geometry: np.ndarray) -> None:
        """
        Add or update the reference geometry.

        This method processes the provided geometry, ensures it is centered at the center of mass (COM), and updates the system's reference geometry.

        Parameters
        ----------
        geometry : list of tuple or str
            The geometry data to be added or updated. It can be provided in two formats:
            1. A list of tuples, where each tuple contains an element symbol and its coordinates:
                - e.g., [("H", [0.0, 0.0, 0.0]), ("O", [0.0, 0.0, 1.0]), ...].
            2. A string path to an XYZ file containing the geometry.
        """
        # Geometry is given by a dictionary of element and xyz coordinates

        elements, coords = self._process_geometry(geometry)
        centered = self._is_centered(elements, coords)

        if not centered:
            logger.info("Geometry is not centered. Centering...")
            # Center the geometry at the center of mass (COM)
            coords = self._center_geometry(elements, coords)

        self.reference_geometry = coords
        self.elements = elements
        self.lvc_data["elements"] = [elements]
        self.lvc_data["reference_geometry"] = [coords]
        logger.info("Reference geometry updated.")

    def add_dipole_matrix(self, dipole_matrix: np.ndarray) -> None:
        """Add or update the dipole matrix.

        Parameters
        ----------
        dipole_matrix : np.ndarray
            The dipole matrix to be added or updated. It should be a 3D numpy array where each slice corresponds to a state and each vector corresponds to a mode.
            The dipole matrix should have dimensions (n_states, n_states, 3). The last dimension represents the x, y, z components of the dipole moment.

        """
        self.dipole_matrix = dipole_matrix
        self.lvc_data["dipole_matrix"] = [dipole_matrix]
        logger.info("Dipole matrix updated.")

    def _append_jt_param(self, jt_values: Dict[str, Any]) -> None:
        """
        Append or update the JT parameters for a given mode.

        Parameters
        ----------
        jt_values : dict
            Dictionary with keys:
                - 'mode': int, the mode index.
                - 'params': dict, typically containing keys such as 'on' and 'off'.

        Raises
        ------
        ValueError
            If the 'mode' key is missing.
        """
        mode = jt_values.get("mode")
        if mode is None:
            logger.error("JT parameter dictionary must include a 'mode' key.")
            raise ValueError("JT parameter dictionary must include a 'mode' key.")

        self.jt_params[mode] = jt_values["params"]
        logger.info("Stored JT parameters for mode %d: %s", mode, self.jt_params[mode])

    def _validate_jt_inputs(self) -> None:
        """
        Validate Jahn-Teller effect inputs.

        Each entry in jt_effects must be a dictionary with the keys:
            - 'mode': int, the index of the normal mode.
            - 'state_pairs': list, pairs of states coupled by the JT effect.
            - 'types': list, JT effect types for each state pair.
        Optionally, if a JT effect is inactive ('active': False), it must include:
            - 'source': int, the mode index to copy parameters from.

        Raises
        ------
        ValueError
            If any of the validations fail.
        """
        if self.jt_effects is None:
            return  # No JT effects to validate

        if not isinstance(self.jt_effects, list):
            logger.error("jt_effects must be provided as a list of dictionaries.")
            raise ValueError("jt_effects must be provided as a list of dictionaries.")

        for effect in self.jt_effects:
            if not isinstance(effect, dict):
                logger.error("Each entry in jt_effects must be a dictionary.")
                raise ValueError("Each entry in jt_effects must be a dictionary.")

            required_keys = ["mode", "state_pairs", "types"]
            for key in required_keys:
                if key not in effect:
                    logger.error("JT effect is missing required key: '%s'", key)
                    raise ValueError(f"JT effect is missing required key: '{key}'.")

            if not isinstance(effect["state_pairs"], list):
                logger.error("'state_pairs' must be a list.")
                raise ValueError("'state_pairs' must be a list.")
            if not isinstance(effect["types"], list):
                logger.error("'types' must be a list.")
                raise ValueError("'types' must be a list.")
            if len(effect["state_pairs"]) != len(effect["types"]):
                logger.error(
                    "The number of 'state_pairs' must equal the number of 'types'."
                )
                raise ValueError("The number of 'state_pairs' must equal the number of 'types'.")

            if "active" in effect and not isinstance(effect["active"], bool):
                logger.error("The 'active' key, if provided, must be a boolean.")
                raise ValueError("The 'active' key, if provided, must be a boolean.")

            if effect.get("active") is False and "source" not in effect:
                logger.error("Inactive JT effects must include a 'source' key.")
                raise ValueError("Inactive JT effects must include a 'source' key.")

    def _validate_essential_inputs(self) -> None:
        """
        Validate essential inputs for the system and ensure that
        all elements in data lists are numpy arrays.

        Raises
        ------
        ValueError
            If required inputs are missing.
        TypeError
            If symmetry_point_group is provided and is not a string.
        """
        if not self.database_abinitio or not self.displacement_vector:
            msg = (
                "Both database_abinitio and displacement_vector must be provided "
                "for the computation of the vertical shifts."
            )
            logger.error(msg)
            raise ValueError(msg)

        # Ensure that all entries in database_abinitio are np.ndarray.
        self.database_abinitio = [
            arr if isinstance(arr, np.ndarray) else np.array(arr)
            for arr in self.database_abinitio
        ]

        # Ensure that all entries in displacement_vector are np.ndarray.
        self.displacement_vector = [
            arr if isinstance(arr, np.ndarray) else np.array(arr)
            for arr in self.displacement_vector
        ]

        # Validate and process symmetry-related inputs.
        if self.symmetry_point_group is not None:
            if not isinstance(self.symmetry_point_group, str):
                logger.error("symmetry_point_group must be a string.")
                raise TypeError("symmetry_point_group must be a string.")
            else:
                self.totally_sym_irrep = SymmetryMask._get_total_sym_irrep(self)
                logger.info("Total symmetry irrep: %s", self.totally_sym_irrep)
                self.symmetry_matrix = SymmetryMask.create_symmetry_matrix(self)
                logger.info("Symmetry matrix successfully created.")

    def _find_energy_shifts(self) -> np.ndarray:
        """
        Compute the vertical energy shifts from the ab initio database.

        Returns
        -------
        np.ndarray
            Array of vertical energy shifts for each state.

        Raises
        ------
        ValueError
            If no zero displacement is found for mode 0.
        IndexError
            If the zero displacement index is out of bounds.
        """
        try:
            displacement_mode = self.displacement_vector[0]
        except IndexError:
            logger.error("displacement_vector is empty. Cannot compute energy shifts.")
            raise ValueError("displacement_vector is empty. Cannot compute energy shifts.")

        # Find indices where the displacement is effectively zero.
        close_to_zero_indices = np.where(np.isclose(displacement_mode, 0.0))[0]
        if close_to_zero_indices.size == 0:
            logger.error("No zero displacement found in displacement_vector for mode 0.")
            raise ValueError("No zero displacement found in displacement_vector for mode 0.")

        zero_index = close_to_zero_indices[0]
        mode_0_data = self.database_abinitio[0]

        if zero_index >= mode_0_data.shape[1]:
            logger.error(
                "Zero displacement index %d is out of bounds (max index: %d).",
                zero_index,
                mode_0_data.shape[1] - 1,
            )
            raise IndexError("Zero displacement index is out of bounds for displacement dimension.")

        e0_constants = mode_0_data[:, zero_index]
        logger.info("Computed vertical energy shifts: %s", e0_constants)
        return e0_constants

    def _get_lvc_data(self) -> Dict[str, Any]:
        """
        Return a dictionary containing system data for the LVC calculation.

        Returns
        -------
        dict
            Dictionary with keys such as 'reference_geometry', 'units',
            'number_normal_modes', 'number_states', and others.
        """
        lvc_data = {
            "elements": [self.elements],
            "reference_geometry": [self.reference_geometry],
            "units": [self.units],
            "number_normal_modes": [self.number_normal_modes],
            "number_states": [self.number_states],
            "coupling_with_gs": ["Yes"] if self.coupling_with_gs else ["No"],
            "symmetry_point_group": [self.symmetry_point_group],
            "totally_sym_irrep": [self.totally_sym_irrep],
            "symmetry_modes": [self.symmetry_modes],
            "symmetry_states": [self.symmetry_states],
            "vib_freq": [self.vib_freq],
            "energy_shift": [self.energy_shift],
            "dipole_matrix": [self.dipole_matrix],
            "lvcham": [self.vcham],
        }
        return lvc_data

    def __repr__(self) -> str:
        """Return a string representation of the VCSystem object."""
        return (
            f"VCSystem(vc_type='{self.vc_type}', units='{self.units}', "
            f"number_normal_modes={self.number_normal_modes}, number_states={self.number_states}, "
            f"symmetry_point_group='{self.symmetry_point_group}', "
            f"jt_effects='{self.jt_effects}')"
        )
    
    
    def _read_xyz(self, file_path: str) -> List[Tuple[str, List[float]]]:
        """Reads an XYZ file and returns a list of (element, [x, y, z]) tuples.
        
        Args:
            file_path (str): Path to the XYZ file.
        
        Returns:
            List[Tuple[str, List[float]]]: List of atoms with their coordinates.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is malformed.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
            try:
                num_atoms = int(lines[0].strip())
            except ValueError:
                raise ValueError("First line must be an integer number of atoms.")
            
            if len(lines) < num_atoms + 2:
                raise ValueError("File does not contain enough lines for the specified number of atoms.")
            
            atoms = []
            for line in lines[2:2 + num_atoms]:
                parts = line.split()
                if len(parts) < 4:
                    raise ValueError(f"Line '{line.strip()}' does not have enough columns.")
                element = parts[0]
                try:
                    coords = [float(x) for x in parts[1:4]]
                except ValueError:
                    raise ValueError(f"Coordinates in line '{line.strip()}' are not numbers.")
                atoms.append((element, coords))
            
            return atoms

    def _process_geometry(self, input_data: List[Tuple[str, List[float]]]) -> Tuple[List[str], np.ndarray]:
        """Processes geometry input and returns elements and coordinates.
        
        Args:
            input_data: List of (element, [x, y, z]).
        
        Returns:
            Tuple[List[str], np.ndarray]: (elements, coords), where coords is a NumPy array of shape (n_atoms, 3).
        """
        # Input data could be a list of tuples (element, [x, y, z]) or a string path to an XYZ file
        if isinstance(input_data, str):
            input_data = self._read_xyz(input_data)
        elif not isinstance(input_data, list):
            raise ValueError("Input data must be a list of tuples or a string path to an XYZ file.")
        if not all(isinstance(atom, tuple) and len(atom) == 2 for atom in input_data):
            raise ValueError("Each atom must be a tuple of (element, [x, y, z]).")
        if not all(isinstance(atom[1], list) and len(atom[1]) == 3 for atom in input_data):
            raise ValueError("Coordinates must be a list of three floats.")
        # Extract elements and coordinates
        elements = [atom[0] for atom in input_data]
        coords_list = [atom[1] for atom in input_data]
        coords = np.array(coords_list, dtype=float)
        return elements, coords

    def _calculate_com(self, elements: List[str], coords: np.ndarray) -> np.ndarray:
        """Calculates the center of mass (COM) of the geometry.
        
        Args:
            elements: List of element symbols.
            coords: NumPy array of coordinates, shape (n_atoms, 3).
            atomic_weights: Dictionary of atomic weights for each element.
        
        Returns:
            np.ndarray: The center of mass vector.
        """
        # Do it case insensitive
        elements = [el.capitalize() for el in elements]
        # Check if all elements are in the atomic weights dictionary
        if not all(el in self.atomic_weights for el in elements):
            raise ValueError("Some elements are not in the atomic weights dictionary.")
        # Convert elements to atomic weights
        masses = np.array([self.atomic_weights[el] for el in elements])
        total_mass = np.sum(masses)
        com = np.sum(masses[:, None] * coords, axis=0) / total_mass
        return com

    def _is_centered(self, elements: List[str], coords: np.ndarray, tol: float = 1e-6) -> bool:
        """Checks if the geometry is centered at the center of mass.
        
        Args:
            elements: List of element symbols.
            coords: NumPy array of coordinates, shape (n_atoms, 3).
            atomic_weights: Dictionary of atomic weights for each element.
            tol: Tolerance for considering COM as zero (default: 1e-6).
        
        Returns:
            bool: True if the center of mass is at origin within tolerance, False otherwise.
        """
        com = self._calculate_com(elements, coords)
        return np.allclose(com, [0, 0, 0], atol=tol)

    def _center_geometry(self, elements: List[str], coords: np.ndarray) -> np.ndarray:
        """Centers the geometry at the center of mass (COM) if it isn't already.
        
        Args:
            elements: List of element symbols.
            coords: NumPy array of coordinates, shape (n_atoms, 3).
            atomic_weights: Dictionary of atomic weights for each element.
        
        Returns:
            np.ndarray: The centered coordinates.
        """
        if not self._is_centered(elements, coords):
            com = self._calculate_com(elements, coords)
            coords = coords - com
        return coords