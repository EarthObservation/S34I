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

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt

class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AetherGeo User Manual")
        self.setWindowFlags(Qt.WindowType.Window)  
        self.setGeometry(100, 100, 1200, 900)  
        
        layout = QVBoxLayout(self)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  
        layout.addWidget(self.text_browser)
        
        self.load_help_content()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def load_help_content(self):
        help_file = os.path.join(os.path.dirname(__file__), "User_Manual.html")
        
        if os.path.exists(help_file):
            with open(help_file, 'r', encoding='utf-8') as f:
                self.text_browser.setHtml(f.read())
        else:
            self.text_browser.setHtml("""
            <h1>AetherGeo User Manual</h1>
            
            <h2>Some error seems to have happened</h2>
            <ul>
                <li><b>Please check the User_Manual file in the icon_function directory</b></li>
                <br>
                <li><b>Or contact the author:</b></li>
                <br>
                <b>Gonçalo Santos</b>
                <br>
                <b>Email: aethergeoofficial@gmail.com or up202004466@up.pt</b>
            </ul>
            """)