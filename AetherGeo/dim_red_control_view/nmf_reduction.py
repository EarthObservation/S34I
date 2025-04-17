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
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QVBoxLayout, QMessageBox, QDialog
from sklearn.decomposition import NMF

from image_manipulation import manipulation

class NMFOperations:
    def __init__(self, parent):
        """
        Initialize NMF operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  
        
    def execute(self, path, n_components):
        "Execute NMF with given parameters"
        try:
            image_data = self.main_window.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            # Default: use the image's own non_masked_indices
            non_masked_indices = image_data["non_masked_indices"]
            
            if "NMF" in self.parent.control_views:
                control_view = self.parent.control_views["NMF"].widget()
                selected_mask = control_view.mask_combo.currentData()
                if selected_mask is not None and selected_mask in self.main_window.image_data:
                    non_masked_indices = self.main_window.image_data[selected_mask]["non_masked_indices"]
                    
                    cols, rows = metadata["cols"], metadata["rows"]
                    mask_cols = self.main_window.image_data[selected_mask]["metadata"]["cols"]
                    mask_rows = self.main_window.image_data[selected_mask]["metadata"]["rows"]
                    if cols != mask_cols or rows != mask_rows:
                        QMessageBox.warning(self.parent, "Error", "Image and mask dimensions do not match.")
                        return
            
            masked_array = manipulation.apply_mask(array, non_masked_indices)

            nmf_result, significance = self.NMF_spectral(
                masked_array, 
                n_components=n_components)
            
            if significance is not None:
                canvas = self.plot_nmf_significance(significance)
                dialog = QDialog(self.parent)
                dialog.setWindowTitle("NMF Results")
                QVBoxLayout(dialog).addWidget(canvas)
                dialog.exec()
            
            if "NMF" in self.parent.control_views:
                control_view = self.parent.control_views["NMF"].widget()
                control_view.result_data = nmf_result
            else:
                print("Warning: NMF control view not found to store results.")
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"NMF failed: {str(e)}")
            
    def NMF_spectral(self, non_masked_pixels, n_components=11, random_state=42):
        """
        Apply Non-negative Matrix Factorization (NMF) to spectral data,
        and return the transformed representation and a significance measure per component.
        
        Parameters:
            non_masked_pixels: iterable of tuples (mask, pixel_spectrum)
                where each pixel_spectrum is a 1D array (n_features,)
            n_components: int, number of NMF components (default 11)
            random_state: int, for reproducibility
            
        Returns:
            results_nmf: 2D array, shape (n_samples, n_components)
                The activation matrix W.
            significance: 1D array, shape (n_components,)
                Significance measure for each component computed as the L2 norm of that column in W.
        """
        band_values = np.array([pixels for _, pixels in non_masked_pixels])
        
        nmf_model = NMF(n_components=n_components, init='nndsvda', random_state=random_state)
        # W: activations, H: endmember spectra
        W = nmf_model.fit_transform(band_values)
        
        # Compute significance as L2 norm of each column of W
        significance = np.linalg.norm(W, axis=0)
        
        return W, significance
    
    def plot_nmf_significance(self, significance):
        """
        Create a matplotlib FigureCanvas with a bar chart displaying NMF component significance.
        
        Parameters:
            significance (array-like): Significance measure (L2 norms) for each NMF component.
        
        Returns:
            FigureCanvas: A canvas containing the bar chart.
        """
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(range(1, len(significance) + 1), significance, color='purple')
        ax.set_xlabel("Component")
        ax.set_ylabel("Significance (L2 Norm)")
        ax.set_title("NMF Component Significance")
        canvas = FigureCanvas(fig)
        return canvas