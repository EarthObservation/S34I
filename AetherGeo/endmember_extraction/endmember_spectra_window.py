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

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout, QFileDialog, QMessageBox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
import numpy as np

from collections import defaultdict

from spec_library_managment import saving
                            
class EndmemberSpectraWidget(QWidget):
    def __init__(self, endmembers, non_masked_indices, main_image, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Endmember Spectra")
        self.endmembers = endmembers
        self.non_masked_indices = non_masked_indices
        self.main_image = main_image
        self.metadata = metadata
        
        main_layout = QHBoxLayout()
        
        left_panel_layout = QVBoxLayout()
        
        self.back_btn = QPushButton("Back to Cloud")
        left_panel_layout.addWidget(self.back_btn)
        
        self.text_display = QTextEdit()
        self.text_display.setText(f"Loaded {len(endmembers)} endmembers")
        left_panel_layout.addWidget(self.text_display)
        
        self.save_btn = QPushButton("Save Spectra")
        self.save_btn.clicked.connect(self._save_spectra)
        left_panel_layout.addWidget(self.save_btn)
        
        self.figure = plt.figure(figsize=(15, 6))
        self._plot_spectra()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        right_panel_layout = QVBoxLayout()
        right_panel_layout.addWidget(self.canvas)
        right_panel_layout.addWidget(self.toolbar)
        
        main_layout.addLayout(left_panel_layout)
        main_layout.addLayout(right_panel_layout)
        
        self.setLayout(main_layout)
    
    def _plot_spectra(self):
        """Regenerate the plot with current data."""
        
        if self.metadata.get('wavelengths') is not None:
            wavelengths = np.array([float(w) for w in self.metadata['wavelengths']])
        else:
            wavelengths = np.array(list(range(1, self.main_image.shape[2] + 1)))
        
        clusters_dict = defaultdict(list)
        for cluster_label, indices in self.endmembers.items():
            for idx in indices:
                position = self.non_masked_indices[idx]
                clusters_dict[cluster_label].append(position)
        
        endmember_dict = {}
        for cluster_label, pixel_coords in clusters_dict.items():
            spectra_list = []
            for row, col in pixel_coords:
                spectra = self.main_image[row, col, :].squeeze()
                spectra_list.append(spectra)
            endmember_dict[cluster_label] = np.array(spectra_list)
        
        self.figure.clf()
        ax = self.figure.add_subplot(111)
        
        prop_cycle = plt.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']
        
        endmember_spectra = {}
        for idx, (cluster_label, spectra) in enumerate(endmember_dict.items()):
            avg_spectrum = np.mean(spectra, axis=0)
            endmember_spectra[cluster_label] = avg_spectrum
            
            mask = avg_spectrum != 0
            
            x_split = np.split(wavelengths[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
            y_split = np.split(avg_spectrum[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
            
            color = colors[idx % len(colors)]
            for i, (x_segment, y_segment) in enumerate(zip(x_split, y_split)):
                ax.plot(x_segment, y_segment, 
                    color=color,
                    label=cluster_label if i == 0 else "")
        
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Reflectance")
        ax.set_title("Average Spectrum for Each Cluster")
        ax.legend()
        self.figure.tight_layout()
    
    def update_data(self, endmembers, non_masked_indices, main_image, metadata):
        """Update the widget with new data and refresh the plot."""
        self.endmembers = endmembers
        self.non_masked_indices = non_masked_indices
        self.main_image = main_image
        self.metadata = metadata
        self.text_display.setText(f"Loaded {len(endmembers)} endmembers")
        self._plot_spectra()
        self.canvas.draw()
    
    def _save_spectra(self):
        """Handle saving results"""
        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Results",
                "",
                "Spectral Library (*.sli *.hdr);;All Files (*.*)"
            )
            
            if output_path:
                if not output_path.lower().endswith(('.sli', '.hdr')):
                    output_path += '.sli'

                clusters_dict = defaultdict(list)
                for cluster_label, indices in self.endmembers.items():
                    for idx in indices:
                        position = self.non_masked_indices[idx]
                        clusters_dict[cluster_label].append(position)
                
                endmember_dict = {}
                cluster_labels = []  # Store cluster labels in order
                for cluster_label, pixel_coords in clusters_dict.items():
                    spectra_list = []
                    for row, col in pixel_coords:
                        spectra = self.main_image[row, col, :].squeeze()
                        spectra_list.append(spectra)
                    endmember_dict[cluster_label] = np.array(spectra_list)
                    cluster_labels.append(str(cluster_label))  # Convert labels to strings
                
                endmember_spectra = {}
                for cluster_label, spectra in endmember_dict.items():
                    avg_spectrum = np.mean(spectra, axis=0)
                    endmember_spectra[cluster_label] = avg_spectrum
                
                saving.save_library(endmember_spectra, output_path, self.metadata, names=cluster_labels)
                
                QMessageBox.information(self, "Success", "Spectral library saved!")
            else:
                QMessageBox.warning(self, "Error", "Problem with output path")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")