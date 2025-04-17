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
import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog, QWidget

from image_manipulation.saving import save_image

class PixelPurityIdxControlView(QWidget):
    """Control view for Pixel Purity Index."""
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
        
        self.mask_combo = QComboBox()
        self.mask_combo.setFixedHeight(35)
        self.mask_combo.addItem("No mask selected", None)
        layout.addWidget(QLabel("Select Mask (optional):"))
        layout.addWidget(self.mask_combo)
        
        self.projections_combo = QComboBox()
        self.projections_combo.setFixedHeight(35)
        for i in range(9, 15):  
            value = 2 ** i
            self.projections_combo.addItem(f"{value} projections", value)
        layout.addWidget(QLabel("Number of Projections:"))
        layout.addWidget(self.projections_combo)

        run_btn = QPushButton(f"Run {self.function_name}")
        run_btn.clicked.connect(self.execute_function)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        save_btn = QPushButton("Save PPI mask")
        save_btn.setFixedSize(160, 40)
        save_btn.clicked.connect(self.save_dialog)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def refresh_images(self):
        """Populate image and mask combo boxes."""
        self.image_combo.clear()
        self.mask_combo.clear()
        self.mask_combo.addItem("No mask selected", None)
        main_window = self.parent.parent  
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.image_combo.addItem(os.path.basename(path), path)
                self.mask_combo.addItem(os.path.basename(path), path)

    def execute_function(self):
        """Run PPI on the selected image."""
        path = self.image_combo.currentData()
        if not path or path not in self.parent.parent.image_data:
            QMessageBox.warning(self, "Error", "Please select a valid image.")
            return

        mask_path = self.mask_combo.currentData()
        n_projection = self.projections_combo.currentData()

        if self.run_callback:
            try:
                self.run_callback(path, mask_path, n_projection)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"PPI failed: {str(e)}")

    def save_dialog(self):
        """Save the PPI mask."""
        if self.result_data is None:
            QMessageBox.warning(self, "Error", "No PPI data to save. Run PPI first.")
            return

        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Normalized Image",
                "",
                "TIF Files (*.tif);;All Files (*.*)"
            )
            if not output_path:
                return
            else:
                if not output_path.lower().endswith(('.tif', '.hdr')):
                    output_path += '.tif'

                path = self.image_combo.currentData()
                image_data = self.parent.parent.image_data[path]
                metadata = image_data["metadata"]

                selected_mask = self.mask_combo.currentData()
                if selected_mask is not None and selected_mask in self.parent.parent.image_data:
                    non_masked_indices = self.parent.parent.image_data[selected_mask]["non_masked_indices"]
                else:
                    non_masked_indices = image_data["non_masked_indices"]
                
                if hasattr(self, 'result_data'):
                    reconstructed = np.full((metadata["rows"], metadata["cols"]), np.nan)
                    for idx, (row, col) in enumerate(non_masked_indices):
                        if idx < len(self.result_data):  # Ensure we don't go out of bounds
                            reconstructed[row, col] = self.result_data[idx]

                    save_image(
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
                    QMessageBox.information(self, "Success", "PPI saved successfully.")
                
                else:
                    QMessageBox.warning(self, "Error", "No results available to save. Please run the analysis first.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save results: {str(e)}")
       