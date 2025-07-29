import tables
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from molmass import ELEMENTS
import xcom


# You must set this to the correct path for your system!
NIST_XCOM_HDF5_PATH = xcom.NIST_XCOM_HDF5_PATH


photon_cross_section_column_names = [
    'Coherent (barns/at.)',
    'Incoherent (barns/at.)',
    'Photoelectric (barns/at.)',
    'Pair-atom (barns/at.)',
    'Pair-elec (barns/at.)'
]


def get_element_xcom(element_symbol):
    atomic_number = ELEMENTS[element_symbol].number
    integer_string = f"{atomic_number:03d}"
    with tables.open_file(NIST_XCOM_HDF5_PATH) as h5file:
        table = h5file.get_node(f'/Z{integer_string}', "data")
        data = pd.DataFrame(table.read())
    data.columns = ['Energy (MeV)'] + photon_cross_section_column_names
    data['Energy (MeV)'] /= 1e6
    data.set_index('Energy (MeV)', inplace=True)
    return data


def get_material_xcom(material_composition):
    # Dictionary to store mass attenuation data for each element
    predefined_mass_energy_dict = {
        symbol: get_element_xcom(symbol)
        for symbol in material_composition.element_symbols
    }
    # Collect all unique energy values across all elements
    all_energies = np.unique(np.concatenate([df.index.values for df in predefined_mass_energy_dict.values()]))
    # Retrieve weight fractions of each element in the material
    weight_fractions = dict(zip(material_composition.element_symbols, material_composition.weight_fractions))
    # Initialize dictionary to store computed attenuation coefficients
    attenbook = {'Energy (MeV)': all_energies}
    for photon_data_selection in photon_cross_section_column_names:
        compound_mass_attenuation = np.zeros_like(all_energies, dtype=float)
        for element, df in predefined_mass_energy_dict.items():
            weight_fraction = weight_fractions.get(element, 0)
            interp_mass_atten = interp1d(df.index, df[photon_data_selection], kind='linear', bounds_error=False, fill_value="extrapolate")
            interpolated_mass_atten = interp_mass_atten(all_energies)
            compound_mass_attenuation += weight_fraction * interpolated_mass_atten
        attenbook[photon_data_selection] = compound_mass_attenuation
    attenframe = pd.DataFrame(attenbook).set_index('Energy (MeV)')
    return attenframe