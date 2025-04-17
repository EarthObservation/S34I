"""
AetherGeo is a software for data analysis, centered around geological applications.>
Copyright (C) <2025>  <Gonçalo Santos>
Version 1.0.0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

A full copy of the GNU General Public License can be found under the License file.
Otherwise, see <https://www.gnu.org/licenses/>

The author would like to give the sincerest thanks to all the individuals (single and plural) that built and still
manage and maintain all the libraries that made this application possible. 
The main interface is built in PyQt6, developed and maintained by Riverbank Computing (https://www.riverbankcomputing.com/software/pyqt/).
Also, a special thanks to the individuals behind: NumPy, OpenGL, Matplotlib, Spectral, Rasterio, UMAP, Sklearn and SciPy and scikit-image, h5py and pyproj.
It is also important to cite that this software is free and open source, in this way providing to the community a new accessible tool. 

If you want to contact the author, please send an email to aethergeoofficial@gmail.com or up202004466@up.pt
"""

import numpy as np

from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout
from sklearn.decomposition import FastICA
from scipy.stats import kurtosis

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from image_manipulation import manipulation

class ICAOperations:
    def __init__(self, parent):
        """
        Initialize ICA operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  
    
    def execute(self, path, n_components):
        """Execute ICA with given parameters"""
        try:
            image_data = self.main_window.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            # Default: use the image's own non_masked_indices
            non_masked_indices = image_data["non_masked_indices"]
            
            if "ICA" in self.parent.control_views:
                control_view = self.parent.control_views["ICA"].widget()
                selected_mask = control_view.mask_combo.currentData()
                if selected_mask is not None and selected_mask in self.main_window.image_data:
                    non_masked_indices = self.main_window.image_data[selected_mask]["non_masked_indices"]
                    
                    cols, rows = metadata["cols"], metadata["rows"]
                    mask_cols, mask_rows = self.main_window.image_data[selected_mask]["metadata"]["cols"], self.main_window.image_data[selected_mask]["metadata"]["rows"]
                    if cols != mask_cols or rows != mask_rows:
                        QMessageBox.warning(self.parent, "Error", "Image and mask dimensions do not match.")    
                        return
                    
            masked_array = manipulation.apply_mask(array, non_masked_indices)
            
            ica_result, ica_kurtosis = self.ICA_spectral(
                masked_array, 
                n_components=n_components)

            if ica_kurtosis is not None:
                canvas = self.plot_ica_kurtosis(ica_kurtosis)
                dialog = QDialog(self.parent)
                dialog.setWindowTitle("ICA Results")
                QVBoxLayout(dialog).addWidget(canvas)
                dialog.exec()

            if "ICA" in self.parent.control_views:
                control_view = self.parent.control_views["ICA"].widget()
                control_view.result_data = ica_result
            else:
                print("Warning: ICA control view not found to store results.")
        
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"ICA failed: {str(e)}")
            
    def ICA_spectral(self, non_masked_pixels, n_components=11, random_state=42):
        """
        Apply ICA to spectral data and compute kurtosis for each independent component.
        """
        band_values = np.array([pixels for _, pixels in non_masked_pixels])
        
        ica = FastICA(n_components=n_components, random_state=random_state)
        results_ica = ica.fit_transform(band_values)
        
        ica_kurtosis = kurtosis(results_ica, axis=0)
        
        return results_ica, ica_kurtosis
    
    def plot_ica_kurtosis(self, ica_kurtosis):
        """
        Create a matplotlib FigureCanvas with a bar chart displaying ICA component kurtosis.

        Parameters:
            ica_kurtosis (array-like): Kurtosis values for each ICA component.

        Returns:
            FigureCanvas: A canvas containing the bar chart.
        """
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(range(1, len(ica_kurtosis) + 1), ica_kurtosis)
        ax.set_xlabel("Component")
        ax.set_ylabel("Kurtosis")
        ax.set_title("ICA Component Kurtosis")
        canvas = FigureCanvas(fig)
        return canvas
