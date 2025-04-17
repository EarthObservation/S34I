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

from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QSizePolicy, QMessageBox, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
import umap.umap_ as umap

from endmember_extraction.automatic_selection import AutomaticSelection
from endmember_extraction.manual_selection import ManualSelection
from endmember_extraction.endmember_spectra_window import EndmemberSpectraWidget

class UMAPVisualizerWindow(QDialog):
    def __init__(self, cloud_points, non_masked_indices, main_image, metadata, labels=None, parent=None):
        super().__init__(parent)
        self.cloud_points = cloud_points  
        self.labels = labels  
        self.non_masked_indices = non_masked_indices  
        self.main_image = main_image
        self.metadata = metadata    
        self.setWindowTitle("UMAP 3D Visualization")
        self.setGeometry(100, 100, 1600, 900)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.stacked_widget = QStackedWidget()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stacked_widget)
        
        self.umap_page = QWidget()
        self._setup_umap_page()  
        self.stacked_widget.addWidget(self.umap_page)
        
    def _setup_umap_page(self):
        umap_layout = QHBoxLayout(self)
        self.umap_page.setLayout(QHBoxLayout())

        self.controls_panel = QWidget()
        controls_layout = QVBoxLayout(self.controls_panel)

        manual_selection_label = QLabel("Manual Selection")
        manual_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(manual_selection_label)

        self.freeze_status_label = QLabel("Press 'A' to Freeze/Unfreeze View")
        self.lasso_status_label = QLabel("Press 'S' to Enable/Disable Lasso")
        controls_layout.addWidget(self.freeze_status_label)
        controls_layout.addWidget(self.lasso_status_label)

        button_layout = QHBoxLayout()
        self.clear_all_button = QPushButton("Clear All Selections")
        self.clear_last_button = QPushButton("Clear Last Selection")
        button_layout.addWidget(self.clear_all_button)
        button_layout.addWidget(self.clear_last_button)
        controls_layout.addLayout(button_layout)

        line1 = QWidget()
        line1.setFixedHeight(1)
        line1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        line1.setStyleSheet("background-color: #c0c0c0;")  # Light gray color
        controls_layout.addWidget(line1)

        automatic_selection_label = QLabel("Automatic Selection - OPTICS")
        automatic_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(automatic_selection_label)

        controls_layout.addWidget(QLabel("Clustering Parameters:"))
        
        self.min_samples_input = QSpinBox()
        self.min_samples_input.setRange(2, 100)
        self.min_samples_input.setValue(5)
        controls_layout.addWidget(QLabel("min_samples:"))
        controls_layout.addWidget(self.min_samples_input)

        self.xi_input = QDoubleSpinBox()
        self.xi_input.setRange(0.01, 0.5)
        self.xi_input.setSingleStep(0.01)
        self.xi_input.setValue(0.05)
        controls_layout.addWidget(QLabel("xi:"))
        controls_layout.addWidget(self.xi_input)

        self.min_cluster_size_input = QDoubleSpinBox()
        self.min_cluster_size_input.setRange(0.01, 0.5)
        self.min_cluster_size_input.setSingleStep(0.01)
        self.min_cluster_size_input.setValue(0.05)
        controls_layout.addWidget(QLabel("min_cluster_size:"))
        controls_layout.addWidget(self.min_cluster_size_input)

        self.auto_params_btn = QPushButton("Set Automatic Parameters")
        self.auto_params_btn.clicked.connect(self.calculate_auto_params)
        controls_layout.addWidget(self.auto_params_btn)
        
        self.run_clustering_btn = QPushButton("Run OPTICS Clustering")
        self.run_clustering_btn.clicked.connect(self.run_optics_clustering)
        controls_layout.addWidget(self.run_clustering_btn)

        line2 = QWidget()
        line2.setFixedHeight(1)
        line2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        line2.setStyleSheet("background-color: #c0c0c0;")  
        controls_layout.addWidget(line2)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        controls_layout.addWidget(self.text_edit)
        controls_layout.addStretch()
        umap_layout.addWidget(self.controls_panel, stretch=1)
        
        self.view_spectra_btn = QPushButton("View Endmember Spectra")
        self.view_spectra_btn.clicked.connect(self.show_spectra_view)
        controls_layout.addWidget(self.view_spectra_btn)

        self.figure, self.ax, self.scatter, self.embedding, self.original_colors = self.create_umap_visualization(self.cloud_points, self.labels)
        self.canvas = FigureCanvas(self.figure)
        self.umap_page.layout().addWidget(self.controls_panel, stretch=1)
        self.umap_page.layout().addWidget(self.canvas, stretch=3)

        self.manual_selection = ManualSelection(
            figure=self.figure,
            canvas=self.canvas,
            scatter=self.scatter,
            embedding=self.embedding,
            original_colors=self.original_colors,
            text_display=self.text_edit,
            labels=self.labels
        )

        self.freeze_shortcut = QShortcut(QKeySequence("A"), self)
        self.freeze_shortcut.activated.connect(self.on_freeze_toggle)
        self.lasso_shortcut = QShortcut(QKeySequence("S"), self)
        self.lasso_shortcut.activated.connect(self.on_lasso_toggle)

        self.clear_all_button.clicked.connect(self.manual_selection.reset_endmembers)
        self.clear_last_button.clicked.connect(self.manual_selection.clear_last_endmember)

        self.canvas.mpl_connect('button_press_event', self.manual_selection.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.manual_selection.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.manual_selection.on_mouse_move)

    def create_umap_visualization(self, pure_data, labels):
        reducer = umap.UMAP(n_components=3, random_state=42)
        embedding = reducer.fit_transform(pure_data)
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        if labels is None:
            colors = np.tile([0.7, 0.7, 0.7, 0.6], (len(embedding), 1))
        else:
            cmap = plt.get_cmap('tab20')
            colors = cmap(labels / max(labels))
        original_colors = colors.copy()
        scatter = ax.scatter(*embedding.T, c=colors, alpha=0.6, s=10, picker=True)
        ax.set_title('UMAP 3D Visualization')
        ax.set_xlabel('UMAP 1')
        ax.set_ylabel('UMAP 2')
        ax.set_zlabel('UMAP 3')
        ax.view_init(elev=20, azim=45)
        return fig, ax, scatter, embedding, original_colors

    def on_freeze_toggle(self):
        """Toggle the frozen view state and update the status label."""
        self.manual_selection.toggle_freeze()
        if self.manual_selection.view_frozen:
            self.freeze_status_label.setText("View FROZEN - Press 'A' to Unfreeze")
            self.freeze_status_label.setStyleSheet("color: red;")
        else:
            self.freeze_status_label.setText("Press 'A' to Freeze View")
            self.freeze_status_label.setStyleSheet("")

    def on_lasso_toggle(self):
        """Toggle lasso selection mode and update the status label."""
        self.manual_selection.toggle_lasso()
        if self.manual_selection.lasso_enabled:
            self.lasso_status_label.setText("Lasso ENABLED - Left-click to select")
            self.lasso_status_label.setStyleSheet("color: green;")
        else:
            self.lasso_status_label.setText("Press 'S' to Enable Lasso")
            self.lasso_status_label.setStyleSheet("")
            
    def calculate_auto_params(self):
        """Calculate and update parameters using AutomaticSelection"""
        params = AutomaticSelection.select_parameters(self.cloud_points)
        self.min_samples_input.setValue(params['min_samples'])
        self.xi_input.setValue(params['xi'])
        self.min_cluster_size_input.setValue(params['min_cluster_size'])
        
    def update_cluster_colors(self, cluster_labels):
        """Update visualization colors based on cluster labels."""
        cmap = plt.get_cmap('tab20')
        colors = np.array([cmap(l % cmap.N) if l != -1 else [0.7, 0.7, 0.7, 0.6] for l in cluster_labels])
        self.scatter.set_facecolors(colors)
        self.canvas.draw_idle()
        
        self.manual_selection.original_colors = colors.copy()
        
    def run_optics_clustering(self):
        min_samples = self.min_samples_input.value()
        xi = self.xi_input.value()
        min_cluster_size = self.min_cluster_size_input.value()
        
        labels = AutomaticSelection.run_optics_clustering(
            self.cloud_points, min_samples, xi, min_cluster_size
        )
        
        gray_colors = np.tile([0.7, 0.7, 0.7, 0.6], (len(self.cloud_points), 1))
        
        self.manual_selection.original_colors = gray_colors.copy()
        self.manual_selection.reset_endmembers()
        
        unique_clusters = np.unique(labels)
        for cluster_id in unique_clusters:
            if cluster_id == -1:  
                continue
            indices = np.where(labels == cluster_id)[0].tolist()
            
            self.manual_selection.endmember_counter += 1
            endmember_id = self.manual_selection.endmember_counter
            self.manual_selection.endmembers[endmember_id] = {
                "name": f"{cluster_id}",
                "indices": indices,
                "color": self.manual_selection.endmember_colors[
                    endmember_id % len(self.manual_selection.endmember_colors)
                ]
            }
        
        self.update_cluster_colors(labels)
        self.manual_selection.update_endmember_display()
        
    def show_spectra_view(self):
        """Switch to the Endmember Spectra view."""
        if not self.manual_selection.endmembers:
            QMessageBox.warning(self, "Warning", "No endmembers selected!")
            return

        try:
            endmember_data = {
                em["name"]: em["indices"] 
                for em in self.manual_selection.endmembers.values()
            }
            
            if hasattr(self, 'spectra_widget'):
                self.spectra_widget.update_data(
                    endmember_data,
                    self.non_masked_indices,
                    self.main_image,
                    self.metadata
                )
            else:

                self.spectra_widget = EndmemberSpectraWidget(
                    endmember_data, 
                    self.non_masked_indices,
                    self.main_image,
                    self.metadata,
                    parent=self.stacked_widget
                )
                self.spectra_widget.back_btn.clicked.connect(
                    lambda: self.stacked_widget.setCurrentIndex(0)
                )
                self.stacked_widget.addWidget(self.spectra_widget)
            
            self.stacked_widget.setCurrentIndex(1)
            self.stacked_widget.update()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading spectra: {str(e)}")