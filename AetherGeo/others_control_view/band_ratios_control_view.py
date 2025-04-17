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

class BandRatiosControlsView(QWidget):
    """Control view for Band Ratio operations with custom equation builder."""
    
    def __init__(self, function_name, parent=None, run_callback=None):
        super().__init__(parent)
        self.function_name = function_name
        self.run_callback = run_callback
        self.parent = parent  # Parent is FunctionListItem
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
        self.image_combo.currentIndexChanged.connect(self.update_band_combo)
        layout.addWidget(QLabel("Select Raster:"))
        layout.addWidget(self.image_combo)

        self.band_combo = QComboBox()
        self.band_combo.setFixedHeight(35)
        layout.addWidget(QLabel("Select Band:"))
        layout.addWidget(self.band_combo)

        self.equation_display = QLineEdit()
        self.equation_display.setReadOnly(True)
        self.equation_display.setPlaceholderText("Build your equation here...")
        layout.addWidget(QLabel("Equation Builder:"))
        layout.addWidget(self.equation_display)

        add_band_btn = QPushButton("Add Band")
        add_band_btn.clicked.connect(self.add_band_to_equation)
        layout.addWidget(add_band_btn)

        op_layout1 = QHBoxLayout()
        for op in ['+', '-', '*']:
            btn = QPushButton(op)
            btn.clicked.connect(lambda _, o=op: self.append_to_equation(o))
            op_layout1.addWidget(btn)
        layout.addLayout(op_layout1)

        op_layout2 = QHBoxLayout()
        for op in ['/', '(', ')']:
            btn = QPushButton(op)
            btn.clicked.connect(lambda _, o=op: self.append_to_equation(o))
            op_layout2.addWidget(btn)
        layout.addLayout(op_layout2)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_equation)
        layout.addWidget(clear_btn)

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
        main_window = self.parent.parent  # Main application window
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.image_combo.addItem(os.path.basename(path), path)
        self.update_band_combo()

    def update_band_combo(self):
        """Update band selection based on selected image's bands"""
        path = self.image_combo.currentData()
        if not path:
            return

        main_window = self.parent.parent
        if path in main_window.image_data:
            metadata = main_window.image_data[path].get('metadata', {})
            bands = metadata.get('bands', 1)
            
            self.band_combo.clear()
            for band in range(1, bands + 1):
                self.band_combo.addItem(f"Band {band}", band - 1)  # 0-based index

    def add_band_to_equation(self):
        """Add selected band to the equation"""
        band_num = self.band_combo.currentData() + 1  # Convert to 1-based for display
        self.append_to_equation(f"B{band_num}")

    def append_to_equation(self, text):
        """Append text to the equation display"""
        current = self.equation_display.text()
        self.equation_display.setText(current + text)

    def clear_equation(self):
        """Clear the equation display"""
        self.equation_display.clear()

    def execute_function(self):
        """Collect parameters and execute band ratio calculation"""
        path = self.image_combo.currentData()
        equation = self.equation_display.text().strip()

        if not path or not equation:
            QMessageBox.warning(self, "Error", "Please select an image and build an equation.")
            return

        if self.run_callback:
            try:
                self.run_callback(path, equation)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Band operation failed: {str(e)}")

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
                    QMessageBox.information(self, "Success", "Band operation results saved!")
                else:
                    QMessageBox.warning(self, "Error", "No results to save. Run the analysis first.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")