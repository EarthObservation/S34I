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

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt

from image_manipulation import saving

class WavelengthsControlsView(QWidget):
    """Control view for satellite wavelength assignment."""
    def __init__(self, function_name, parent=None, run_callback=None):
        super().__init__(parent)
        self.function_name = function_name
        self.run_callback = run_callback
        self.parent = parent
        self.result_data = None
        self.setup_ui()

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

        self.satellite_combo = QComboBox()
        self.satellite_combo.setFixedHeight(35)
        self.satellite_combo.addItem("EnMap")
        self.satellite_combo.addItem("WorldView-3")
        self.satellite_combo.addItem("PRISMA")
        layout.addWidget(QLabel("Select Satellite:"))
        layout.addWidget(self.satellite_combo)

        run_btn = QPushButton(f"Run {self.function_name}")
        run_btn.clicked.connect(self.execute_function)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        save_btn = QPushButton("Save Processed Image")
        save_btn.setFixedSize(160, 40)
        save_btn.clicked.connect(self.save_dialog)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def refresh_images(self):
        """Populate image combo box."""
        self.image_combo.clear()
        main_window = self.parent.parent  
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.image_combo.addItem(os.path.basename(path), path)

    def execute_function(self):
        """Run satellite wavelength assignment."""
        path = self.image_combo.currentData()
        satellite = self.satellite_combo.currentText()
        
        if not path or path not in self.parent.parent.image_data:
            QMessageBox.warning(self, "Error", "Please select a valid image.")
            return

        if self.run_callback:
            try:
                self.run_callback(path, satellite)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Operation failed: {str(e)}")

    def save_dialog(self):
        """Save processed image (implementation mirroring normalization)."""
        if self.result_data is None:
            QMessageBox.warning(self, "Error", "No data to save. Run processing first.")
            return

        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Processed Image",
                "",
                "TIF Files (*.tif);;All Files (*.*)"
            )
            if output_path:
                if not output_path.lower().endswith(('.tif', '.hdr')):
                    output_path += '.tif'
                
                path = self.image_combo.currentData()
                image_data = self.parent.parent.image_data[path]
                array = image_data["array"]
                metadata = image_data["metadata"]
                wavelengths = self.result_data
                
                saving.save_image(output_path, array, metadata["map_info"], metadata["coordinates"], 
                                  metadata["cols"], metadata["rows"], metadata["pixel_size_x"], metadata["pixel_size_y"],
                                  metadata["x_origin"], metadata["y_origin"], wavelengths)
                
                QMessageBox.information(self, "Success", "Image saved successfully.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")