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

from PyQt6.QtWidgets import QVBoxLayout, QDialog, QTableWidget, QTableWidgetItem, QTextEdit

class MetadataDialog(QDialog):
    def __init__(self, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Metadata")
        self.setFixedSize(600, 400)
        
        self.setStyleSheet("""
            QDialog {
                background: #2D2D2D;
                color: #FFFFFF;
            }
            QTableView {
                background: #404040;
                gridline-color: #505050;
                border: none;
            }
            QHeaderView::section {
                background: #353535;
                color: #FFFFFF;
                padding: 4px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self._populate_table(metadata)
        
        layout.addWidget(self.table)
        
    def _populate_table(self, metadata):
        self.table.setRowCount(len(metadata))
        for row, (key, value) in enumerate(metadata.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            
            if isinstance(value, (list, np.ndarray)):
                disp_value = ", ".join(map(str, value))
                text_edit = QTextEdit()
                text_edit.setText(disp_value)
                text_edit.setReadOnly(True)
                text_edit.setMinimumHeight(50)
                self.table.setCellWidget(row, 1, text_edit)
                self.table.setRowHeight(row, 50)  
            elif isinstance(value, float):
                disp_value = f"{value:.4f}"
                self.table.setItem(row, 1, QTableWidgetItem(disp_value))
                self.table.setRowHeight(row, 50)
            else:
                disp_value = str(value)
                self.table.setItem(row, 1, QTableWidgetItem(disp_value))
                self.table.setRowHeight(row, 50)
        
        self.table.resizeColumnsToContents()