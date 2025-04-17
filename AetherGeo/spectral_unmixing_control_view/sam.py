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

from image_manipulation import manipulation

from spec_library_managment.spec_manipulation import get_spectrum_by_name

class SAMOperations:
    def __init__(self, parent):
        """
        Initialize SAM operations with parent reference to access necessary data
        parent: FunctionListItem instance
        """
        self.parent = parent
        self.main_window = parent.parent  
    
    def execute(self, path, spectral_library, spectrum_name):
        """Execute SAM with given parameters"""
        try:
            image_data = self.main_window.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            # Default: use the image's own non_masked_indices
            non_masked_indices = image_data["non_masked_indices"]
            
            if "SAM" in self.parent.control_views:
                control_view = self.parent.control_views["SAM"].widget()
                selected_mask = control_view.mask_combo.currentData()
                if selected_mask is not None and selected_mask in self.main_window.image_data:
                    non_masked_indices = self.main_window.image_data[selected_mask]["non_masked_indices"]
                    
                    cols, rows = metadata["cols"], metadata["rows"]
                    mask_cols, mask_rows = self.main_window.image_data[selected_mask]["metadata"]["cols"], self.main_window.image_data[selected_mask]["metadata"]["rows"]
                    if cols != mask_cols or rows != mask_rows:
                        QMessageBox.warning(self.parent, "Error", "Image and mask dimensions do not match.")    
                        return
            
            masked_array = manipulation.retrieve_reduction_on_ppi(array, non_masked_indices)
    
            spectral_library = control_view.libraries_combo.currentData()
            spectrum = get_spectrum_by_name(self.main_window.spectral_libraries[spectral_library]['library_array'],
                                            self.main_window.spectral_libraries[spectral_library]['metadata']['spectra_names'], 
                                            spectrum_name)
            
            if masked_array.shape[1] != len(spectrum):
                QMessageBox.warning(self.parent, "Error", "Spectrum length does not match image bands.")    
                return
            
            results = self.sam(masked_array, spectrum)
            
            if "SAM" in self.parent.control_views:
                control_view = self.parent.control_views["SAM"].widget()
                control_view.result_data = results
                QMessageBox.information(self.parent, "Success", "Calculation completed!")
            else:
                print("Warning: SAM control view not found to store results.")
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"SAM failed: {str(e)}")
    
    def sam(self, masked_array, spectrum):
        """
        Runs the Spectral Angle Mapper (SAM) algorithm
        
        Parameters:
            masked_array: numpy array of shape (n_pixels, n_bands)
            spectrum: numpy array of shape (n_bands,)
            
        Returns:
            sam_scores: numpy array of shape (n_pixels,) containing spectral angles in radians
        """
        spectrum = spectrum.reshape(-1)
        
        dot_product = np.sum(masked_array * spectrum, axis=1)
        
        pixel_magnitudes = np.sqrt(np.sum(masked_array**2, axis=1))
        spectrum_magnitude = np.sqrt(np.sum(spectrum**2))
        
        cos_angle = dot_product / (pixel_magnitudes * spectrum_magnitude)
        
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # Convert to angle in radians
        sam_scores = np.arccos(cos_angle)
        
        return sam_scores