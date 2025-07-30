# PyVCHAM

PyVCHAM is an open-source Python package designed to construct vibronic coupling (VC) Hamiltonians for complex molecular systems where the Born-Oppenheimer approximation fails. Leveraging machine learning techniques, specifically automatic differentiation via TensorFlow, PyVCHAM optimizes Hamiltonian parameters efficiently and accurately. It is built to integrate seamlessly with quantum chemistry tools like [OpenMolcas](https://gitlab.com/Molcas/OpenMolcas) and [ADC-connect](https://github.com/adc-connect/adcc), enabling high-dimensional nonadiabatic dynamics simulations with enhanced flexibility and precision.

## Key Features

- **Automatic Differentiation**: Uses TensorFlow to compute precise gradients of cost functions, improving optimization efficiency.
- **Quantum Chemistry Integration**: Interfaces with tools such as [OpenMolcas](https://gitlab.com/Molcas/OpenMolcas) and [ADC-connect](https://github.com/adc-connect/adcc) for ab initio data input.
- **Standardized JSON Format**: Proposes a structured JSON format for storing VC Hamiltonians, enhancing interoperability with dynamics software like [MCTDH](https://www.pci.uni-heidelberg.de/tc/mctdh.html).
- **Modular Design**: Supports custom diabatic or coupling functions to adapt to specific research needs.
- **Robust Optimization**: Employs the Adam algorithm for parameter fitting, with support for linear and higher-order vibronic coupling terms.
- **Symmetry Handling**: Incorporates symmetry constraints to ensure physically meaningful coupling terms.

## Installation

#### For macOS Users
TensorFlow 2.17.0 or higher must be installed via Conda on macOS due to platform-specific requirements. Follow these steps:

1. Install TensorFlow using Conda:
   ```bash
   conda install tensorflow
   ```
   Note: It takes around 1 or 2 minutes to import tensorflow for the first time.

PyVCHAM requires Python version 3.9 or later (lower than 3.13). Install it via pip:

```bash
pip install vcham
```

For the latest development version, install directly from GitLab:

```bash
pip install git+https://gitlab.com/tc-heidelberg/pyvcham
```

## Usage

PyVCHAM enables the construction of VC Hamiltonians using a multi-point approach, fitting ab initio data to analytical potential energy surfaces. A typical workflow includes:

1. **Prepare Input Data**: Gather normal mode data, ab initio energies, symmetry information, and harmonic frequencies.
2. **Build Database**: Create a Python object containing the input data.
3. **Optimize Parameters**: Use PyVCHAM to fit the VC Hamiltonian parameters, starting with linear vibronic coupling (LVC) and adding higher-order terms as needed.
4. **Export Results**: Save the optimized Hamiltonian in the standardized JSON format.

For detailed examples and instructions, refer to the [documentation](https://gitlab.com/tc-heidelberg/pyvcham).

## Standardized JSON Format

PyVCHAM introduces a standardized JSON format to store VC Hamiltonians, promoting data exchange and compatibility with quantum dynamics tools. The format includes:

- **General Data**: System-wide details, ab initio information, and custom functions.
- **VC Hamiltonian**: Reference geometry, units, state and mode counts, symmetry data, vertical energies, dipole matrices, and LVC parameters.
- **Interactions** (optional): Parameters for intermolecular interactions in multi-molecule systems.

This structure ensures portability and usability across platforms. Explore examples in the repository (e.g., `Examples/li3/results/lvc_li3.json`).


## License

PyVCHAM is released under the MIT License.

## Citations

If you use PyVCHAM in your research, please cite our paper:

[In preparation]

PyVCHAM builds on foundational work in vibronic coupling and quantum dynamics, including:

- Köppel, H.; Domcke, W.; Cederbaum, L. S. "Multimode Molecular Dynamics Beyond the Born-Oppenheimer Approximation," *Advances in Chemical Physics* **1984**, 57, 59–246.
