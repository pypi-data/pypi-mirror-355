import pandas as pd
import numpy as np
from .xcom_data import get_material_xcom

class MaterialsAnalysis:
    def __init__(self):
        self.materials = []
        self.results = {}

    def register_material(self, material):
        self.materials.append(material)

    def calculate_attenuation(self):
        for mat in self.materials:
            self.results[mat.short_name] = get_material_xcom(mat.composition)

    def get_results(self):
        # Flatten results into a multi-index DataFrame
        analysis_results_midx_dict = {
            (material_name, interaction_type): df[interaction_type]
            for material_name, df in self.results.items()
            for interaction_type in df.keys()
        }
        analysis_results_midx_frame = pd.DataFrame(analysis_results_midx_dict)
        analysis_results_midx_frame.replace(0, np.nan, inplace=True)
        analysis_results_midx_frame_interp = analysis_results_midx_frame.interpolate(method='index')
        analysis_results_midx_frame_interp.fillna(0, inplace=True)
        analysis_results_midx_frame_interp.columns.names = ['Material', 'Interaction']
        return analysis_results_midx_frame_interp