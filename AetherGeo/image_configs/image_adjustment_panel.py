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

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSlider, QPushButton                         
from PyQt6.QtCore import Qt

class ImageAdjustmentPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background: #2D2D2D;
                color: #FFFFFF;
                border-radius: 5px;
                padding: 8px;
            }
            QSlider {
                min-height: 25px;
            }
            QSlider::groove:horizontal {
                background: #404040;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #707070;
                width: 12px;
                margin: -6px 0;
                border-radius: 6px;
            }
            QLabel {
                font-weight: bold;
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        sat_layout = QHBoxLayout()
        sat_label = QLabel("Saturation:")
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setMinimum(10)
        self.saturation_slider.setMaximum(30)
        self.saturation_slider.setValue(15)  # Default 1.5
        self.saturation_value = QLabel("1.5")
        sat_layout.addWidget(sat_label)
        sat_layout.addWidget(self.saturation_slider)
        sat_layout.addWidget(self.saturation_value)
        layout.addLayout(sat_layout)
        
        gamma_layout = QHBoxLayout()
        gamma_label = QLabel("Gamma:")
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setMinimum(1)
        self.gamma_slider.setMaximum(20)
        self.gamma_slider.setValue(7)  # Default 0.7
        self.gamma_value = QLabel("0.7")
        gamma_layout.addWidget(gamma_label)
        gamma_layout.addWidget(self.gamma_slider)
        gamma_layout.addWidget(self.gamma_value)
        layout.addLayout(gamma_layout)
        
        self.apply_btn = QPushButton("Apply Adjustments")
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border-radius: 4px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        layout.addWidget(self.apply_btn)
        
        self.setFixedSize(340, 160)

        self.saturation_slider.valueChanged.connect(
            lambda v: self.saturation_value.setText(f"{v/10:.1f}")
        )
        self.gamma_slider.valueChanged.connect(
            lambda v: self.gamma_value.setText(f"{v/10:.1f}")
        )