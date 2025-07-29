from .composition import MaterialComposition

class Material:
    def __init__(self, short_name, formula=None, predefined_nist=None, density_g_cm3=None, enrichment=None):
        self.short_name = short_name
        self.density_g_cm3 = density_g_cm3
        self.composition = MaterialComposition(
            formula=formula,
            predefined_nist=predefined_nist,
            enrichment=enrichment,
            density_g_cm3=density_g_cm3
        )

    def add_element(self, element, weight_fraction):
        """Add or update an element by weight fraction."""
        self.composition.add_element(element, weight_fraction)

    def add_material(self, material, loading_fraction_by_mass):
        """Add another material's elements by mass fraction."""
        # Accepts either a Material or MaterialComposition
        if hasattr(material, "composition"):
            self.composition.add_material(material.composition, loading_fraction_by_mass)
        else:
            self.composition.add_material(material, loading_fraction_by_mass)

    def element_dataframe(self):
        return self.composition.get_element_dataframe()

    def isotope_dataframe(self):
        return self.composition.get_isotope_dataframe()