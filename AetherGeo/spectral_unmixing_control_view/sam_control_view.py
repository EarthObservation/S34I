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

import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,  QFileDialog, QComboBox, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt

from image_manipulation import saving 

class SAMControlsView(QWidget):
    """Control view for SAM."""
    
    def __init__(self, function_name, parent=None, run_callback=None):
        super().__init__(parent)
        self.function_name = function_name
        self.run_callback = run_callback
        self.parent = parent  # Parent is FunctionListItem
        self.result_data = None  
        self.setup_ui()
        
    def showEvent(self, event):
        """Override showEvent to refresh data when widget becomes visible"""
        super().showEvent(event)
        self.refresh_libraries()
        if self.libraries_combo.count() > 0:
            self.refresh_spectrum_names()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)

        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(80, 30)
        back_btn.clicked.connect(self.parent.show_main_view)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        title = QLabel(self.function_name)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.image_combo = QComboBox()
        self.image_combo.setFixedHeight(35)
        layout.addWidget(QLabel("Select Raster:"))
        layout.addWidget(self.image_combo)
        
        self.mask_combo = QComboBox()
        self.mask_combo.setFixedHeight(35)
        self.mask_combo.addItem("No mask selected", None)
        layout.addWidget(QLabel("Select Mask (optional):"))
        layout.addWidget(self.mask_combo)

        self.libraries_combo = QComboBox()
        self.libraries_combo.setFixedHeight(35)
        self.libraries_combo.currentIndexChanged.connect(self.refresh_spectrum_names) 
        layout.addWidget(QLabel("Spectral library:"))
        layout.addWidget(self.libraries_combo)
        
        self.spectrum_name = QComboBox()
        self.spectrum_name.setFixedHeight(35)
        layout.addWidget(QLabel("Spectrum Name:"))
        layout.addWidget(self.spectrum_name)

        run_btn = QPushButton(f"Run {self.function_name}")
        run_btn.clicked.connect(self.execute_function)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        save_btn = QPushButton("Save Results")
        save_btn.setFixedSize(160, 40)
        save_btn.clicked.connect(self.save_dialog)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def refresh_images(self):
        """Populate image combo box with available images"""
        self.image_combo.clear()
        self.mask_combo.clear()
        self.mask_combo.addItem("Select an image", None)
        main_window = self.parent.parent  # Main application window
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.image_combo.addItem(os.path.basename(path), path)
                self.mask_combo.addItem(os.path.basename(path), path)
                
    def refresh_libraries(self):
        """Populate spectral libraries combo box with available libraries"""
        self.libraries_combo.clear()
        main_window = self.parent.parent
        if hasattr(main_window, 'spectral_libraries'):
            for library in main_window.spectral_libraries:
                self.libraries_combo.addItem(os.path.basename(library), library)
                
    def refresh_spectrum_names(self):
        """Populate spectrum names combo box with available spectra"""
        self.spectrum_name.clear()
        library_path = self.libraries_combo.currentData()
        
        if library_path:
            main_window = self.parent.parent
            if hasattr(main_window, 'spectral_libraries'):
                library_data = main_window.spectral_libraries.get(library_path)
                if library_data and 'metadata' in library_data:
                    spectra_names = library_data['metadata'].get('spectra_names', [])
                    for name in spectra_names:
                        self.spectrum_name.addItem(name, name)
    
    def execute_function(self):
        """Collect parameters and execute SAM"""
        path = self.image_combo.currentData()
        spectral_library = self.libraries_combo.currentData()
        spectrum_name = self.spectrum_name.currentData()

        if not path: 
            QMessageBox.warning(self, "Error", "Please select an image first.")
            return
        
        if not spectral_library:
            QMessageBox.warning(self, "Error", "Please select a spectral library.")
            return
        
        if self.run_callback:
            try:
                self.run_callback(path, spectral_library, spectrum_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"SAM failed: {str(e)}")

    def save_dialog(self):
        """Handle saving results"""
        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Results",
                "",
                "TIF Files (*.tif);;All Files (*.*)"
            )
            
            if output_path:
                if not output_path.lower().endswith(('.tif', '.hdr')):
                    output_path += '.tif'

                path = self.image_combo.currentData()
                if not path or path not in self.parent.parent.image_data:
                    QMessageBox.warning(self, "Error", "No valid image data to save")
                    return

                image_data = self.parent.parent.image_data[path]
                metadata = image_data["metadata"]
                non_masked_indices = image_data["non_masked_indices"]

                if self.result_data is not None:
                    reconstructed = saving.image_recovery(
                        self.result_data.reshape(-1, 1),
                        non_masked_indices,
                        metadata["rows"],
                        metadata["cols"]
                    )
                    
                    saving.save_image(
                        output_path,
                        reconstructed,
                        metadata["map_info"],
                        metadata["coordinates"],
                        metadata["cols"],
                        metadata["rows"],
                        metadata["pixel_size_x"],
                        metadata["pixel_size_y"],
                        metadata["x_origin"],
                        metadata["y_origin"],
                        None
                    )
                    QMessageBox.information(self, "Success", "SAM results saved!")
                else:
                    QMessageBox.warning(self, "Error", "No results to save. Run the analysis first.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")