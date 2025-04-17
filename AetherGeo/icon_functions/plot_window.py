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

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QDialog, QComboBox, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path

from image_manipulation import saving

class PlotWindow(QDialog):
    def __init__(self, image_paths, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Plot Parameters")
        self.setFixedSize(800, 800)
        self.parent = parent
        
        self.setStyleSheet("""
            QDialog {
                background: #2D2D2D;
                color: #FFFFFF;
            }
            QComboBox, QSlider {
                background: #404040;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px;
                min-height: 30px;
            }
            QSlider::groove:horizontal {
                background: #505050;
                height: 4px;
            }
            QSlider::handle:horizontal {
                background: #707070;
                width: 12px;
                margin: -6px 0;
                border-radius: 6px;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(20)
        
        image_layout = QHBoxLayout()
        image_label = QLabel("Select Image:")
        image_label.setFixedWidth(80)
        self.image_combo = QComboBox()
        self.image_combo.setFixedHeight(35)
        for path in image_paths:
            self.image_combo.addItem(os.path.basename(path), path)
        self.image_combo.currentIndexChanged.connect(self.image_selected)
        image_layout.addWidget(image_label)
        image_layout.addWidget(self.image_combo)
        layout.addLayout(image_layout)
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure = Figure(figsize=(8, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('X Band')
        self.ax.set_ylabel('Y Band')
        self.ax.grid(True)
        plot_layout.addWidget(self.canvas)
        layout.addWidget(plot_widget)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        self.sliders = {}
        self.value_labels = {}
        for axis in ['X', 'Y']:
            slider_container = QWidget()
            slider_layout = QHBoxLayout(slider_container)
            slider_layout.setContentsMargins(0, 0, 0, 0)
            
            label = QLabel(f"{axis} Band:")
            label.setFixedWidth(60)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(1)
            value_label = QLabel("1")
            value_label.setFixedWidth(30)
            
            self.sliders[axis] = slider
            self.value_labels[axis] = value_label
            slider.valueChanged.connect(
                lambda v, ax=axis: self.value_labels[ax].setText(str(v))
            )
            
            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)
            slider_layout.addWidget(value_label)
            controls_layout.addWidget(slider_container)
        
        self.selected_points = None
        self.scatter = None
        self.lasso = None
        self._initialize_lasso()
        
        plot_btn = QPushButton("Generate Plot")
        plot_btn.setFixedSize(120, 35)
        plot_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        plot_btn.clicked.connect(self.generate_plot)
        controls_layout.addWidget(plot_btn)
        
        layout.addLayout(controls_layout)
        
        save_selection_btn = QPushButton("Save Selection")
        save_selection_btn.setFixedSize(120, 35)
        save_selection_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        save_selection_btn.clicked.connect(self.save_dialog)
        layout.addWidget(save_selection_btn)
        
        if image_paths:
            self.image_selected()
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _initialize_lasso(self):
        """Initialize lasso selector"""
        def onselect(verts):
            if self.scatter is None:
                return
                
            path = Path(verts)
            ind = path.contains_points(self.scatter.get_offsets())
            
            colors = np.array(['blue'] * len(self.scatter.get_offsets()))
            alphas = np.full(len(colors), 0.1)
            
            if ind.any():  
                colors[ind] = 'red'
                alphas[ind] = 0.6
                self.selected_points = ind
            
            self.scatter.set_color(colors)
            self.scatter.set_alpha(alphas)
            
            self.canvas.draw_idle()
            
        self.lasso = LassoSelector(
            ax=self.ax,
            onselect=onselect,
            button=1  
        )
        
    def image_selected(self):
        """Update sliders when image is selected"""
        path = self.image_combo.currentData()
        if not path:  
            for axis in ['X', 'Y']:
                self.sliders[axis].setMaximum(1)
                self.sliders[axis].setValue(1)
            return
            
        if path in self.parent.image_data:
            image_info = self.parent.image_data[path]
            bands = image_info['metadata'].get('bands', 1)
            
            for axis in ['X', 'Y']:
                self.sliders[axis].setMaximum(bands)
                self.sliders[axis].setValue(1)
    
    def generate_plot(self):
        """Generate plot from selected bands"""
        path = self.image_combo.currentData()
        if not path:
            return
            
        x_band = self.sliders['X'].value() - 1
        y_band = self.sliders['Y'].value() - 1
        
        image_array = self.parent.image_data[path]['array']
        rows, cols, bands = image_array.shape
        pixels_2d = image_array.reshape(-1, bands)
        
        self.ax.clear()
        
        self.scatter = self.ax.scatter(
            pixels_2d[:, x_band],
            pixels_2d[:, y_band],
            c='blue', alpha=0.1, s=1
        )
        
        self.ax.set_xlabel(f'Band {x_band + 1}')
        self.ax.set_ylabel(f'Band {y_band + 1}')
        self.ax.grid(True)
        
        self._initialize_lasso()
        self.canvas.draw()
        
    def get_selected_indices(self):
        """Return indices of selected points"""
        return np.where(self.selected_points)[0] if self.selected_points is not None else []
    
    def save_dialog(self):
        """Save the selected points as a binary mask (1 for selected, NaN for others)."""
        if self.selected_points is None or not np.any(self.selected_points):
            QMessageBox.warning(self, "Error", "No selection to save.")
            return

        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Selection Mask",
                "",
                "TIF Files (*.tif);;All Files (*.*)"
            )
            if not output_path:
                return

            if not output_path.lower().endswith(('.tif', '.hdr')):
                output_path += '.tif'

            path = self.image_combo.currentData()
            image_data = self.parent.image_data[path]
            metadata = image_data["metadata"]
            
            mask = np.full((metadata["rows"], metadata["cols"]), np.nan)
            
            if self.scatter is not None and self.selected_points is not None:
                selected_indices = np.where(self.selected_points)[0]

                rows = selected_indices // metadata["cols"]
                cols = selected_indices % metadata["cols"]

                mask[rows, cols] = 1

            saving.save_image(
                output_path,
                mask,
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
            QMessageBox.information(self, "Success", "Selection mask saved successfully.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save results: {str(e)}")