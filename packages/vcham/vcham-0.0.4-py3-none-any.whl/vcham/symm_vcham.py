import numpy as np
from .logging_config import get_logger

logger = get_logger(__name__)


class SymmetryMask:
    # Only abelian groups
    _product_tables = {
        "ci": {
            ("Ag", "Ag"): "Ag",
            ("Ag", "Au"): "Au",
            ("Au", "Ag"): "Au",
            ("Au", "Au"): "Ag",
        },
        "cs": {
            ("A'", "A'"): "A'",
            ("A'", "A''"): "A''",
            ("A''", "A'"): "A''",
            ("A''", "A''"): "A'",
        },
        "c2": {
            ("A", "A"): "A",
            ("A", "B"): "B",
            ("B", "A"): "B",
            ("B", "B"): "A",
        },
        "c2h": {
            ("Ag", "Ag"): "Ag",
            ("Ag", "Bg"): "Bg",
            ("Ag", "Au"): "Au",
            ("Ag", "Bu"): "Bu",
            ("Bg", "Ag"): "Bg",
            ("Bg", "Bg"): "Ag",
            ("Bg", "Au"): "Bu",
            ("Bg", "Bu"): "Au",
            ("Au", "Ag"): "Au",
            ("Au", "Bg"): "Bu",
            ("Au", "Au"): "Ag",
            ("Au", "Bu"): "Bg",
            ("Bu", "Ag"): "Bu",
            ("Bu", "Bg"): "Au",
            ("Bu", "Au"): "Bg",
            ("Bu", "Bu"): "Ag",
        },
        "c2v": {
            ("A1", "A1"): "A1",
            ("A1", "A2"): "A2",
            ("A1", "B1"): "B1",
            ("A1", "B2"): "B2",
            ("A2", "A1"): "A2",
            ("A2", "A2"): "A1",
            ("A2", "B1"): "B2",
            ("A2", "B2"): "B1",
            ("B1", "A1"): "B1",
            ("B1", "A2"): "B2",
            ("B1", "B1"): "A1",
            ("B1", "B2"): "A2",
            ("B2", "A1"): "B2",
            ("B2", "A2"): "B1",
            ("B2", "B1"): "A2",
            ("B2", "B2"): "A1",
        },
        "d2": {
            ("A", "A"): "A",
            ("A", "B1"): "B1",
            ("A", "B2"): "B2",
            ("A", "B3"): "B3",
            ("B1", "A"): "B1",
            ("B1", "B1"): "A",
            ("B1", "B2"): "B3",
            ("B1", "B3"): "B2",
            ("B2", "A"): "B2",
            ("B2", "B1"): "B3",
            ("B2", "B2"): "A",
            ("B2", "B3"): "B1",
            ("B3", "A"): "B3",
            ("B3", "B1"): "B2",
            ("B3", "B2"): "B1",
            ("B3", "B3"): "A",
        },
        "d2h": {
            ("Ag", "Ag"): "Ag",
            ("Ag", "B1g"): "B1g",
            ("Ag", "B2g"): "B2g",
            ("Ag", "B3g"): "B3g",
            ("Ag", "Au"): "Au",
            ("Ag", "B1u"): "B1u",
            ("Ag", "B2u"): "B2u",
            ("Ag", "B3u"): "B3u",
            ("B1g", "Ag"): "B1g",
            ("B1g", "B1g"): "Ag",
            ("B1g", "B2g"): "B3g",
            ("B1g", "B3g"): "B2g",
            ("B1g", "Au"): "B1u",
            ("B1g", "B1u"): "Au",
            ("B1g", "B2u"): "B3u",
            ("B1g", "B3u"): "B2u",
            ("B2g", "Ag"): "B2g",
            ("B2g", "B1g"): "B3g",
            ("B2g", "B2g"): "Ag",
            ("B2g", "B3g"): "B1g",
            ("B2g", "Au"): "B2u",
            ("B2g", "B1u"): "B3u",
            ("B2g", "B2u"): "Au",
            ("B2g", "B3u"): "B1u",
            ("B3g", "Ag"): "B3g",
            ("B3g", "B1g"): "B2g",
            ("B3g", "B2g"): "B1g",
            ("B3g", "B3g"): "Ag",
            ("B3g", "Au"): "B3u",
            ("B3g", "B1u"): "B2u",
            ("B3g", "B2u"): "B1u",
            ("B3g", "B3u"): "Au",
            ("Au", "Ag"): "Au",
            ("Au", "B1g"): "B1u",
            ("Au", "B2g"): "B2u",
            ("Au", "B3g"): "B3u",
            ("Au", "Au"): "Ag",
            ("Au", "B1u"): "B1g",
            ("Au", "B2u"): "B2g",
            ("Au", "B3u"): "B3g",
            ("B1u", "Ag"): "B1u",
            ("B1u", "B1g"): "Au",
            ("B1u", "B2g"): "B3u",
            ("B1u", "B3g"): "B2u",
            ("B1u", "Au"): "B1g",
            ("B1u", "B1u"): "Ag",
            ("B1u", "B2u"): "B3g",
            ("B1u", "B3u"): "B2g",
            ("B2u", "Ag"): "B2u",
            ("B2u", "B1g"): "B3u",
            ("B2u", "B2g"): "Au",
            ("B2u", "B3g"): "B1u",
            ("B2u", "Au"): "B2g",
            ("B2u", "B1u"): "B3g",
            ("B2u", "B2u"): "Ag",
            ("B2u", "B3u"): "B1g",
            ("B3u", "Ag"): "B3u",
            ("B3u", "B1g"): "B2u",
            ("B3u", "B2g"): "B1u",
            ("B3u", "B3g"): "Au",
            ("B3u", "Au"): "B3g",
            ("B3u", "B1u"): "B2g",
            ("B3u", "B2u"): "B1g",
            ("B3u", "B3u"): "Ag",
        },
    }

    @classmethod
    def _get_product_table(cls, sym_point_group: str) -> dict:
        """
        Get the product table for a given symmetry point group.

        Parameters
        ----------
        sym_point_group : str
            The symmetry point group.

        Returns
        -------
        dict
            The product table for the given symmetry point group.

        Raises
        ------
        ValueError
            If the symmetry point group is unknown.
        """
        sym_point_group = sym_point_group.lower()
        if sym_point_group not in cls._product_tables:
            raise ValueError(f"Unknown symmetry point group: {sym_point_group}")
        return cls._product_tables[sym_point_group]

    @classmethod
    def _get_total_sym_irrep(cls, vc_system: object) -> str:
        """
        Get the totally symmetric irreducible representation for a given symmetry point group.

        Parameters
        ----------
        vc_system : object
            An object with a ``symmetry_point_group`` attribute.

        Returns
        -------
        str
            The totally symmetric irreducible representation.

        Raises
        ------
        ValueError
            If ``vc_system`` does not have a ``symmetry_point_group`` attribute.
        """
        if not hasattr(vc_system, "symmetry_point_group"):
            logger.error("vc_system must have a 'symmetry_point_group' attribute")
            raise ValueError("vc_system must have a 'symmetry_point_group' attribute")
        sym_point_group = vc_system.symmetry_point_group.lower()
        table = cls._get_product_table(sym_point_group)
        for (state1, state2), result in table.items():
            if state1 == state2 and state1 == result:
                return result
        return next(iter(table.values()))

    @classmethod
    def _validate_jt_effects(cls, jt_effects, n_normal_modes, n_states):
        """
        Validate Jahn-Teller effects parameters.

        Parameters
        ----------
        jt_effects : list of dict
            List of JT effect dictionaries.
        n_normal_modes : int
            Number of normal modes.
        n_states : int
            Number of states.

        Raises
        ------
        TypeError
            If mode or state indices are not of the correct type.
        IndexError
            If mode or state indices are out of bounds.
        ValueError
            If state_pairs or types are malformed.
        """
        for effect in jt_effects:
            mode_index = effect.get("mode")
            state_pairs = effect.get("state_pairs")
            types = effect.get("types")
            # active = effect.get("active", True)  # Not used in validation but present in effect

            # Validate mode index
            if not isinstance(mode_index, int):
                raise TypeError(f"JT effect 'mode' must be an integer, got {type(mode_index)}")
            if not (0 <= mode_index < n_normal_modes):
                raise IndexError(f"JT effect mode index {mode_index} out of bounds for {n_normal_modes} modes")

            # Validate state_pairs and types
            if not isinstance(state_pairs, list):
                raise TypeError("JT effect 'state_pairs' must be a list")
            if not isinstance(types, list):
                raise TypeError("JT effect 'types' must be a list")
            if len(state_pairs) != len(types):
                raise ValueError("Number of 'state_pairs' must equal number of 'types' in JT effect")

            # Validate each state pair
            for pair_idx, pair in enumerate(state_pairs):
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise ValueError(f"State pair at index {pair_idx} must be a 2-element list/tuple")
                state_a, state_b = pair
                if not isinstance(state_a, int) or not isinstance(state_b, int):
                    raise TypeError(f"State indices in pair {pair_idx} must be integers")
                if not (0 <= state_a < n_states) or not (0 <= state_b < n_states):
                    raise IndexError(f"State indices {state_a} or {state_b} out of bounds for {n_states} states")

    @classmethod
    def create_symmetry_matrix(cls, vc_system: object) -> np.ndarray:
        """
        Create a symmetry matrix based on the given parameters.

        Parameters
        ----------
        vc_system : object
            An object containing the necessary attributes:
              - symmetry_point_group : str
                The symmetry point group.
              - number_normal_modes : int
                Number of normal modes.
              - number_states : int
                Number of states.
              - symmetry_modes : list
                List of symmetry modes.
              - symmetry_states : list
                List of symmetry states.
              - coupling_with_gs : bool
                Whether the ground state is coupled.
              - totally_sym_irrep : str
                The totally symmetric irreducible representation.
              - jt_effects : list of dict, optional
                Each dictionary specifies a JT effect with keys:
                  * 'mode': int, index of the normal mode where the JT effect occurs
                  * 'state_pairs': list of tuples/lists, each containing two state indices
                  * 'types': list of str, JT effect types for each state pair
                  * 'active': bool, optional (default True), whether the effect is optimized
                  * 'source': int, optional, mode index for parameter copying if inactive

        Returns
        -------
        np.ndarray
            Symmetry matrix of shape (n_normal_modes, n_states, n_states).

        Raises
        ------
        AttributeError
            If vc_system lacks required attributes.
        ValueError
            If symmetry operations or JT effects are invalid.
        TypeError
            If mode or state indices are not integers.
        IndexError
            If mode or state indices are out of bounds.
        """
        try:
            # Extract and normalize attributes from vc_system
            sym_point_group = vc_system.symmetry_point_group.lower()
            n_normal_modes = vc_system.number_normal_modes
            n_states = vc_system.number_states
            sym_modes = [mode.upper() for mode in vc_system.symmetry_modes]
            sym_states = [state.upper() for state in vc_system.symmetry_states]
            coupling_with_gs = vc_system.coupling_with_gs
            total_sym_irrep = vc_system.totally_sym_irrep.upper()
            jt_effects = vc_system.jt_effects or []

            # Validate JT effects early
            cls._validate_jt_effects(jt_effects, n_normal_modes, n_states)

            # Initialize symmetry matrix
            symmetry_matrix = np.zeros((n_normal_modes, n_states, n_states), dtype=np.float64)

            # Get product table for efficiency
            product_table = cls._get_product_table(sym_point_group)

            # Precompute intermediate symmetries for each mode and state_i
            inter_sym_cache = {}
            for nmode, sym_mode in enumerate(sym_modes):
                for i, state_i in enumerate(sym_states):
                    inter_sym = product_table.get((state_i, sym_mode))
                    if inter_sym is None:
                        raise ValueError(f"Product not found for {state_i} and {sym_mode}")
                    inter_sym_cache[(nmode, i)] = inter_sym

            # Populate symmetry matrix
            for nmode, sym_mode in enumerate(sym_modes):
                for i in range(n_states):
                    inter_sym = inter_sym_cache[(nmode, i)]
                    for j in range(n_states):
                        state_j = sym_states[j]
                        product = product_table.get((inter_sym, state_j))
                        if product is None:
                            raise ValueError(f"Product not found for {inter_sym} and {state_j}")

                        if sym_mode == total_sym_irrep:
                            # Symmetric mode: diagonal elements = 1 (kappa), off-diagonal = 0
                            symmetry_matrix[nmode, i, j] = 1.0 if i == j else 0.0
                        elif product == total_sym_irrep:
                            # Non-symmetric mode: 1 if product is totally symmetric, unless ground state decoupled
                            symmetry_matrix[nmode, i, j] = 0.0 if not coupling_with_gs and (i == 0 or j == 0) else 1.0
                        else:
                            symmetry_matrix[nmode, i, j] = 0.0

            # Apply Jahn-Teller effects
            if jt_effects:
                logger.info("Jahn-Teller effect detected, applying %d effects", len(jt_effects))
                for effect in jt_effects:
                    mode_index = effect["mode"]
                    state_pairs = effect["state_pairs"]
                    active = effect.get("active", True)

                    for state_a, state_b in state_pairs:
                        if active:
                            # Active JT effect: off-diagonal coupling
                            symmetry_matrix[mode_index, state_a, state_b] = 2.0
                            symmetry_matrix[mode_index, state_b, state_a] = 2.0
                        else:
                            # Inactive JT effect: diagonal elements for parameter copying
                            symmetry_matrix[mode_index, state_a, state_a] = 2.0
                            symmetry_matrix[mode_index, state_b, state_b] = 2.0

            return symmetry_matrix

        except AttributeError as error:
            logger.error("vc_system is missing an expected attribute: %s", error)
            raise
        except Exception as error:
            logger.exception("An error occurred while creating the symmetry matrix: %s", error)
            raise