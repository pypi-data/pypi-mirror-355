from molmass import Formula, ELEMENTS
import pandas as pd
import numpy as np

try:
    import geant4_pybind as g4
except ImportError:
    g4 = None  # Allow code to load even if Geant4 is not installed

class MaterialComposition:
    def __init__(self, formula=None, predefined_nist=None, enrichment=None, density_g_cm3=None):
        self.formula = formula
        self.predefined_nist = predefined_nist
        self.enrichment = enrichment or {}
        self.density_g_cm3 = density_g_cm3
        self.element_symbols = []
        self.weight_fractions = []
        self.atomic_count = {}
        self.material_mass_amu = None

        # Only initialize if formula or NIST is provided
        if self.formula:
            self._from_formula()
        elif self.predefined_nist:
            self._from_nist()
        # else: allow empty, user will add elements/materials later

    def _from_formula(self):
        material_data = Formula(self.formula)
        composition_df = material_data.composition().dataframe()
        self.material_mass_amu = material_data.mass
        self.element_symbols = composition_df.index.tolist()
        self.weight_fractions = composition_df["Fraction"].tolist()
        self.atomic_count = dict(zip(self.element_symbols, composition_df["Count"].tolist()))

    def _from_nist(self):
        if g4 is None:
            raise ImportError("Geant4 Python bindings (geant4_pybind) are required for predefined NIST materials.")
        g4nist = g4.G4NistManager.Instance()
        material_data = g4nist.FindOrBuildMaterial(self.predefined_nist)
        self.density_g_cm3 = material_data.GetDensity() / (g4.g / g4.cm3)
        self.element_symbols = [element.GetName() for element in material_data.GetElementVector()]
        self.weight_fractions = list(material_data.GetFractionVector())
        self.atomic_count = dict(zip(self.element_symbols, material_data.GetAtomsVector()))
        self.material_mass_amu = sum(ELEMENTS[element].mass * count for element, count in self.atomic_count.items())
        # Handle cases where atomic count has zero values
        if any(count == 0 for count in self.atomic_count.values()):
            self.atomic_count = {element: np.nan for element in self.element_symbols}

    def add_element(self, element, weight_fraction):
        """Add or update an element by weight fraction."""
        mass_fractions = dict(zip(self.element_symbols, self.weight_fractions))
        mass_fractions[element] = mass_fractions.get(element, 0) + weight_fraction
        total = sum(mass_fractions.values())
        self.element_symbols = list(mass_fractions.keys())
        self.weight_fractions = [v / total for v in mass_fractions.values()]
        self.atomic_count = {k: np.nan for k in mass_fractions.keys()}

    def add_material(self, material, loading_fraction_by_mass):
        """Add another material's elements by mass fraction."""
        if not 0 <= loading_fraction_by_mass <= 1:
            raise ValueError("Loading fraction by mass must be between 0 and 1.")
        other_df = material.get_element_dataframe()
        mass_fractions = dict(zip(self.element_symbols, self.weight_fractions))
        for _, row in other_df.iterrows():
            symbol = row["Element Symbol"]
            frac = row["Element Mass Fraction"] * loading_fraction_by_mass
            mass_fractions[symbol] = mass_fractions.get(symbol, 0) + frac
        total = sum(mass_fractions.values())
        self.element_symbols = list(mass_fractions.keys())
        self.weight_fractions = [v / total for v in mass_fractions.values()]
        self.atomic_count = {k: np.nan for k in mass_fractions.keys()}

    def get_element_dataframe(self):
        return pd.DataFrame({
            "Element Symbol": self.element_symbols,
            "Element Mass Fraction": self.weight_fractions,
            "Element Quantity": [self.atomic_count.get(e, np.nan) for e in self.element_symbols]
        })

    def get_isotope_dataframe(self):
        df_material = self.get_element_dataframe()
        isotopes = []
        for _, row in df_material.iterrows():
            element_symbol = row["Element Symbol"]
            element_weight_fraction = row["Element Mass Fraction"]
            element_data = ELEMENTS[element_symbol]
            df_isotopes = pd.DataFrame.from_dict(element_data.isotopes, orient="index")
            df_isotopes.columns = [
                "Isotope Relative Mass",
                "Isotope Natural Abundance",
                "Isotope Mass Number",
                "Charge",
            ]
            df_isotopes.drop(columns=["Charge"], inplace=True)
            df_isotopes["Element Symbol"] = element_symbol
            df_isotopes["Isotope Symbol"] = df_isotopes["Isotope Mass Number"].apply(lambda m: f"{element_symbol}{int(m)}")
            # Handle enrichment if specified
            df_isotopes["User Specified Enrichment"] = df_isotopes["Isotope Symbol"].map(
                lambda iso: self.enrichment.get(iso, df_isotopes.loc[df_isotopes["Isotope Symbol"] == iso, "Isotope Natural Abundance"].values[0])
            )
            if any(isotope.startswith(element_symbol) for isotope in self.enrichment.keys()):
                total_enrichment = df_isotopes["User Specified Enrichment"].sum()
                if total_enrichment > 0:
                    df_isotopes["User Specified Enrichment"] /= total_enrichment
            df_isotopes["Isotope Mass Fraction"] = df_isotopes["User Specified Enrichment"] * element_weight_fraction
            atomic_count = self.atomic_count.get(element_symbol, np.nan)
            df_isotopes["Isotope Quantity"] = df_isotopes["User Specified Enrichment"] * atomic_count
            isotopes.append(df_isotopes)
        return pd.concat(isotopes, ignore_index=True)