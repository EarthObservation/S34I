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

from PyQt6.QtWidgets import QMessageBox

import matplotlib.pyplot as plt

from collections import defaultdict

class MeanSpectraOperations:
    def __init__(self, parent):
        """
        Initialize OPTICS operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  
    
    def execute(self, path, cluster_image_path):
        """Execute OPTICS with given parameters"""
        try:
            image_data = self.main_window.image_data[path]
            cluster_image_data = self.main_window.image_data[cluster_image_path]
            array = image_data["array"]
            cluster_array = cluster_image_data["array"]
            metadata = image_data["metadata"]
            cluster_metadata = cluster_image_data["metadata"]

            cols, rows = metadata["cols"], metadata["rows"]
            mask_cols, mask_rows = cluster_metadata["cols"], cluster_metadata["rows"]
            
            if cols != mask_cols or rows != mask_rows:
                        QMessageBox.warning(self.parent, "Error", "Image dimensions do not match.")    
                        return
            
            data = cluster_array.squeeze()
            unique_classes = np.unique(data)
            unique_classes = unique_classes[:]   
                
            class_coordinates = {}
                
            for value in unique_classes:
                rows, cols = np.where(data == value)
                class_coordinates[value] = (list(zip(rows, cols))) 
                
            clusters_dict = defaultdict(list)

            for idx, cord in class_coordinates.items():
                for position in cord:
                    clusters_dict[idx].append(position)

            class_dict = {}

            for cluster_label, pixel_coords in clusters_dict.items():
                spectra_list = []  
                for row, col in pixel_coords:  
                    spectra = array[row, col, :].squeeze()  
                    spectra_list.append(spectra)  
                class_dict[cluster_label] = spectra_list  

            for cluster_label in class_dict:
                class_dict[cluster_label] = np.array(class_dict[cluster_label])
            
            if metadata["wavelengths"] is not None:
                wavelengths = np.array([float(w) for w in metadata["wavelengths"]])
            else:
                wavelengths = np.array(list(range(1, array.shape[2] + 1)))
            
            plt.figure(figsize=(12, 8))
            colors = plt.cm.tab10(np.linspace(0, 1, len(class_dict)))
            
            avg_spectra_dict = {}
            
            for idx, (cluster_label, spectra) in enumerate(class_dict.items()):
                avg_spectrum = np.mean(spectra, axis=0)
                avg_spectra_dict[f'Cluster {cluster_label}'] = avg_spectrum
                
                mask = avg_spectrum != 0
                
                x_split = np.split(wavelengths[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
                y_split = np.split(avg_spectrum[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
                
                color = colors[idx]
                for i, (x_segment, y_segment) in enumerate(zip(x_split, y_split)):
                    plt.plot(x_segment, y_segment, 
                            color=color,
                            label=f'Cluster {cluster_label}' if i == 0 else "")

            if metadata["wavelengths"] is not None:
                plt.xlabel("Wavelength")
            else:
                plt.xlabel("Bands")
            plt.ylabel("Reflectance")
            plt.legend()
            plt.title("Average Spectra for Each Cluster")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.show()

            if "Mean Spectra from Cluster" in self.parent.control_views:
                control_view = self.parent.control_views["Mean Spectra from Cluster"].widget()
                control_view.result_data = avg_spectra_dict
            else:
                print("Warning: Mean Spectra control view not found to store results.")
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Mean Spectra failed: {str(e)}")
            return