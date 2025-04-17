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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog

from image_manipulation import saving

from spec_library_managment import saving

class MeanSpectraControlsView(QWidget):
    """Generic control view K-means."""
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
        #self.image_combo.currentIndexChanged.connect(self.update_components_limit)
        layout.addWidget(QLabel("Select Raster:"))
        layout.addWidget(self.image_combo)
        
        self.cluster_image_combo = QComboBox()
        self.cluster_image_combo.setFixedHeight(35)
        layout.addWidget(QLabel("Select Cluster Image:"))
        layout.addWidget(self.cluster_image_combo)
        
        run_btn = QPushButton(f"Run {self.function_name}")
        run_btn.clicked.connect(self.execute_function)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(10)

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
        
        self.cluster_image_combo.clear()
        if hasattr(main_window, 'image_paths'):
            for path in main_window.image_paths:
                self.cluster_image_combo.addItem(os.path.basename(path), path)

    def execute_function(self):
        """Collect parameters and execute the associated function"""
        path = self.image_combo.currentData()
        cluster_image_path = self.cluster_image_combo.currentData()
        
        if not path or path not in self.parent.parent.image_data:
            QMessageBox.warning(self, "Error", "Please select a valid image")
            return
        
        if self.run_callback:
            try:
                self.run_callback(path, cluster_image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{self.function_name} failed: {str(e)}")
         
    def save_dialog(self):
        """Open save file dialog and save results if valid"""
        if self.result_data is None:
            QMessageBox.warning(self, "Error", "No data to save. Run function first.")
            return 
        
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

                metadata = self.parent.parent.image_data[self.image_combo.currentData()]["metadata"]
                
                endmember_spectra = {}
                cluster_labels = []
                
                for cluster_name, spectrum in self.result_data.items():
                    endmember_spectra[cluster_name] = spectrum
                    cluster_labels.append(str(cluster_name))
                    
                saving.save_library(endmember_spectra, output_path, metadata, names=cluster_labels)
                
                QMessageBox.information(self, "Success", "Spectral library saved!")
            else:
                QMessageBox.warning(self, "Error", "Problem with output path")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")