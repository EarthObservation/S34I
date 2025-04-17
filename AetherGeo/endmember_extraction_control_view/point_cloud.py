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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from endmember_extraction.umap_visualizer_window import UMAPVisualizerWindow
from image_manipulation import manipulation

class PointCloudOperations:
    def __init__(self, parent):
        self.parent = parent
        self.main_window = parent.parent

    def execute(self, path, mask_path, ppi_path):
        """Execute point cloud generation with given parameters"""
        try:
            metadata = self.main_window.image_data[path]["metadata"]
            main_image = self.main_window.image_data[path]["array"]

            if ppi_path is not None and mask_path is not None:
                input_cloud_array = self.main_window.image_data[mask_path]["array"]
                non_masked_indices = self.main_window.image_data[ppi_path]["non_masked_indices"]
            elif ppi_path is not None and mask_path is None: 
                input_cloud_array = self.main_window.image_data[path]["array"]
                non_masked_indices = self.main_window.image_data[ppi_path]["non_masked_indices"]
            elif ppi_path is None and mask_path is not None:
                input_cloud_array = self.main_window.image_data[mask_path]["array"]
                non_masked_indices = self.main_window.image_data[mask_path]["non_masked_indices"]
            else:
                input_cloud_array = self.main_window.image_data[path]["array"]
                non_masked_indices = self.main_window.image_data[path]["non_masked_indices"]

            cloud_points = manipulation.retrieve_reduction_on_ppi(input_cloud_array, non_masked_indices)

            if cloud_points is not None:
                self.parent.umap_window = UMAPVisualizerWindow(
                    cloud_points, non_masked_indices, main_image, 
                    metadata, labels=None, parent=self.parent
                )
                self.parent.umap_window.setWindowModality(Qt.WindowModality.NonModal)
                self.parent.umap_window.show()
            else:
                QMessageBox.warning(self.parent, "Error", "Point cloud generation failed.")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Point cloud generation failed: {str(e)}")