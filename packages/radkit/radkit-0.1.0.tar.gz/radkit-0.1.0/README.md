# RADKIT

A modular Python library for calculating photon cross-section data, building compound materials, and computing energy-dependent attenuation coefficients using NIST XCOM data.

## Features

- Retrieve photon cross-section data for elements and compounds
- Build materials from chemical formulas, NIST/Geant4 names, or by mixing components
- NIST/Geant4 names available from https://geant4-userdoc.web.cern.ch/UsersGuides/ForApplicationDeveloper/html/Appendix/materialNames.html 
- Support for user-specified isotope enrichment
- Output results as tidy pandas DataFrames
- Easy plotting and analysis

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/radkit.git
    cd radkit
    ```
2. Create and activate a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3. Install the package and dependencies:
    ```bash
    pip install -e .
    ```

## Usage

```python
from radkit import Material, MaterialsAnalysis

# Define materials
water = Material(short_name="H2O", formula="H2O")
lead = Material(short_name="Pb", formula="Pb")

# Build a composite material
aerogel = Material(short_name="Aerogel", density_g_cm3=0.2)
aerogel.add_material(water, loading_fraction_by_mass=0.5)
aerogel.add_material(lead, loading_fraction_by_mass=0.5)

# Analyze attenuation
analysis = MaterialsAnalysis()
analysis.register_material(aerogel)
analysis.calculate_attenuation()
df = analysis.get_results()
print(df)
```

## Project Structure 

radkit/
├── radkit/
│   ├── __init__.py
│   ├── composition.py
│   ├── xcom_data.py
│   ├── material.py
│   ├── analysis.py
│   └── utils.py
├── notebooks/
├── tests/
├── pyproject.toml
└── README.md

## Requirements

* Python 3.8+
* All dependencies are specified in pyproject.toml
* (Optional) geant4_pybind for NIST material support

## License

* MIT License

## Author

* Dr. Charles Stephen Sosa