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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox

class PointCloudControlsView(QWidget):
    """Control view for Point Cloud Extraction."""
    
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

        self.layer_combo = QComboBox()
        self.layer_combo.setFixedHeight(35)
        layout.addWidget(QLabel("Select Main Image:"))
        layout.addWidget(self.layer_combo)

        self.secondImage_combo = QComboBox()
        self.secondImage_combo.setFixedHeight(35)
        self.secondImage_combo.addItem("No Reduction Result Selected", None)
        layout.addWidget(QLabel("Select reduction result (optional):"))
        layout.addWidget(self.secondImage_combo)
        
        self.ppi_combo = QComboBox()
        self.ppi_combo.setFixedHeight(35)
        self.ppi_combo.addItem("No PPI selected", None)
        layout.addWidget(QLabel("Select PPI Mask (optional):"))
        layout.addWidget(self.ppi_combo)

        generate_btn = QPushButton("Generate Point Cloud")
        generate_btn.clicked.connect(self.execute_function)
        generate_btn.setFixedSize(160, 40)
        layout.addWidget(generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def refresh_images(self):
        """Populate image combo boxes."""
        self.layer_combo.clear()
        self.secondImage_combo.clear()
        self.ppi_combo.clear()
        
        self.secondImage_combo.addItem("No mask selected", None)
        self.ppi_combo.addItem("No PPI selected", None)
        
        main_window = self.parent.parent
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.layer_combo.addItem(os.path.basename(path), path)
                self.secondImage_combo.addItem(os.path.basename(path), path)
                self.ppi_combo.addItem(os.path.basename(path), path)

    def execute_function(self):
        """Execute point cloud generation"""
        path = self.layer_combo.currentData()
        secondImage_path = self.secondImage_combo.currentData()
        ppi_path = self.ppi_combo.currentData()

        if not path:
            QMessageBox.warning(self, "Error", "Please select a layer.")
            return

        if self.run_callback:
            try:
                self.run_callback(path, secondImage_path, ppi_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Point cloud generation failed: {str(e)}")