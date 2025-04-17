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
from sklearn.cluster import KMeans

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from image_manipulation import manipulation

class KMeansOperations:
    def __init__(self, parent):
        """
        Initialize K-Means operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  
    
    def execute(self, path, mask_path, n_components):
        """Execute K-Means with given parameters"""
        try:
            image_data = self.main_window.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            # Default: use the image's own non_masked_indices
            non_masked_indices = image_data["non_masked_indices"]
            
            if "K-means" in self.parent.control_views:
                control_view = self.parent.control_views["K-means"].widget()
                selected_mask = control_view.mask_combo.currentData()
                if selected_mask is not None and selected_mask in self.main_window.image_data:
                    non_masked_indices = self.main_window.image_data[selected_mask]["non_masked_indices"]
                    
                    cols, rows = metadata["cols"], metadata["rows"]
                    mask_cols, mask_rows = self.main_window.image_data[selected_mask]["metadata"]["cols"], self.main_window.image_data[selected_mask]["metadata"]["rows"]
                    if cols != mask_cols or rows != mask_rows:
                        QMessageBox.warning(self.parent, "Error", "Image and mask dimensions do not match.")    
                        return
            
            masked_array = manipulation.retrieve_reduction_on_ppi(array, non_masked_indices)
            
            labels = self.k_means(masked_array, n_components)
            
            canvas = self.k_means_finalwindow(labels)
            dialog = QDialog(self.parent)
            dialog.setWindowTitle("K-means Results")
            QVBoxLayout(dialog).addWidget(canvas)
            dialog.exec()
            
            if "K-means" in self.parent.control_views:
                control_view = self.parent.control_views["K-means"].widget()
                control_view.result_data = labels
            else:
                print("Warning: K-means control view not found to store results.")
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"K-Means failed: {str(e)}")
            
    def k_means(self, masked_array, n_components):
        """
        Apply K-means to spectral data.
        """
        kmeans = KMeans(n_clusters=n_components, init='k-means++', random_state=42)
        labels = kmeans.fit_predict(masked_array)
        
        return labels
    
    def k_means_finalwindow(self, labels):
        """
        Create a matplotlib FigureCanvas and show information about the results.
        """
        n_pixels = len(labels)
        unique_labels = np.unique(labels)
        
        fig = plt.figure(figsize=(9, 7))
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.3)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        
        results_text = f"Results:\nTotal pixels processed: {n_pixels}\n\n"
        for label in unique_labels:
            cluster_size = np.sum(labels == label)
            percentage = (cluster_size / n_pixels) * 100
            results_text += f"Cluster {label + 1}:\n"
            results_text += f"Pixels: {cluster_size}\n"
            results_text += f"Percentage: {percentage:.2f}%\n\n"
        
        ax1.text(0.05, 0.95, results_text,
                        transform=ax1.transAxes,
                        verticalalignment='top',
                        fontsize=10,
                        family='monospace',
                        bbox=dict(facecolor='white',
                                edgecolor='gray',
                                alpha=0.9,
                                pad=10))
        ax1.set_title("Cluster Statistics", pad=20)
        ax1.axis('off')
        
        sizes = [np.sum(labels == label) for label in unique_labels]
        labels_pie = [f'Cluster {label + 1}' for label in unique_labels]
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))
        
        ax2.pie(sizes, 
                labels=labels_pie, 
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                shadow=True,
                textprops={'fontsize': 9})
        ax2.set_title('Cluster Distribution', pad=20)
        
        plt.tight_layout(pad=2.0)
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(600, 400)
        
        toolbar = NavigationToolbar2QT(canvas, None)
        
        container = QVBoxLayout()
        container.addWidget(toolbar)
        container.addWidget(canvas)
        
        dialog = QDialog(self.parent)
        dialog.setLayout(container)
        
        return dialog
        