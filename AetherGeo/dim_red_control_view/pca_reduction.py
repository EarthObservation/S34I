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
from sklearn.decomposition import PCA

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from image_manipulation import manipulation

class PCAOperations:
    def __init__(self, parent):
        """
        Initialize PCA operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  

    def execute(self, path, n_components):
        """Execute PCA with given parameters"""
        try:
            image_data = self.main_window.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            non_masked_indices = image_data["non_masked_indices"]
            
            if "PCA" in self.parent.control_views:
                control_view = self.parent.control_views["PCA"].widget()
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

            pca_result, eigenvalues = self.PCA_spectral(
                masked_array, 
                n_components=n_components)

            if eigenvalues is not None:
                canvas = self.plot_eigenvalues(eigenvalues)
                dialog = QDialog(self.parent)
                dialog.setWindowTitle("PCA Results")
                QVBoxLayout(dialog).addWidget(canvas)
                dialog.exec()

            if "PCA" in self.parent.control_views:
                control_view = self.parent.control_views["PCA"].widget()
                control_view.result_data = pca_result
            else:
                print("Warning: PCA control view not found to store results.")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"PCA failed: {str(e)}")
            
    def PCA_spectral(self, non_masked_pixels, n_components=11, random_state=42):
        """ 
        Apply PCA to spectral data, and return results and eigenvalues 
        """
        band_values = np.array([pixels for _, pixels in non_masked_pixels])
        
        pca = PCA(n_components=n_components, random_state=random_state, svd_solver='full')
        results_pca = pca.fit_transform(band_values)
        
        eigenvalues = pca.explained_variance_
        
        return results_pca, eigenvalues
    
    def plot_eigenvalues(self, eigenvalues):
        """
        Create a plot of eigenvalues showing variance explained by each component and return a FigureCanvas.
        
        Parameters:
        -----------
        eigenvalues : array-like
            Array of eigenvalues from PCA
        """
        total_variance = np.sum(eigenvalues)
        variance_ratio = eigenvalues / total_variance
        cumulative_variance_ratio = np.cumsum(variance_ratio)
        
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()
        
        ax1.bar(range(1, len(eigenvalues) + 1), variance_ratio * 100, 
                alpha=0.5, color='b', label='Individual')
        ax1.set_xlabel('Principal Component')
        ax1.set_ylabel('Explained Variance Ratio (%)')
        
        ax2.plot(range(1, len(eigenvalues) + 1), cumulative_variance_ratio * 100, 
                'r-', label='Cumulative')
        ax2.set_ylabel('Cumulative Explained Variance Ratio (%)')
        
        plt.title('PCA Explained Variance Ratio by Component')
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return canvas