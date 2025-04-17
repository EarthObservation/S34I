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

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QComboBox, 
                            QLabel, QMessageBox, QCheckBox, QHBoxLayout, 
                            QScrollArea, QFrame, QPushButton)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

class SpectraAnalystWindow(QMainWindow):
    def __init__(self, spectral_libraries, parent=None):
        super().__init__(parent)
        self.spectral_libraries = spectral_libraries
        self.spectrum_colors = {} 
        self.plotted_spectra = {} 
        
        self.setWindowTitle("Spectra Analyst")
        self.setGeometry(100, 100, 1800, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)
        
        lib_label = QLabel("Select Spectral Library:")
        lib_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(lib_label)
        
        self.lib_combo = QComboBox()
        self.lib_combo.currentIndexChanged.connect(self.on_library_selected)
        left_layout.addWidget(self.lib_combo)
        
        second_lib_label = QLabel("Select Second Library (Optional):")
        second_lib_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(second_lib_label)
        
        self.second_lib_combo = QComboBox()
        self.second_lib_combo.addItem("No second library")
        self.second_lib_combo.currentIndexChanged.connect(self.on_second_library_selected)
        left_layout.addWidget(self.second_lib_combo)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        checkbox_widget = QWidget()
        self.checkbox_layout = QVBoxLayout(checkbox_widget)
        scroll.setWidget(checkbox_widget)
        left_layout.addWidget(scroll)
        
        self.compare_button = QPushButton("Compare Selected Spectra (SAM)")
        self.compare_button.clicked.connect(self.compare_selected_spectra)
        left_layout.addWidget(self.compare_button)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)
        self.annotation = None
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)
        
        self.refresh_libraries()
        
    def refresh_libraries(self):
        """Update the list of available spectral libraries"""
        self.lib_combo.clear()
        self.second_lib_combo.clear()
        self.second_lib_combo.addItem("No second library")
        
        if not self.spectral_libraries:
            self.lib_combo.addItem("No libraries imported")
            self.lib_combo.setEnabled(False)
            self.second_lib_combo.setEnabled(False)
            return
            
        self.lib_combo.setEnabled(True)
        self.second_lib_combo.setEnabled(True)
        
        for lib_path in self.spectral_libraries.keys():
            self.lib_combo.addItem(os.path.basename(lib_path), lib_path)
            self.second_lib_combo.addItem(os.path.basename(lib_path), lib_path)
            
    def on_library_selected(self, index):
        """Handle library selection"""
        if index < 0 or not self.spectral_libraries:
            return
            
        if hasattr(self, 'annotation') and self.annotation:
            try:
                self.annotation.remove()
            except:
                pass
            self.annotation = None
            
        lib_path = self.lib_combo.currentData()
        if not lib_path:
            return
            
        try:
            lib_data = self.spectral_libraries[lib_path]
            self.current_library = {
                'spectra': lib_data['library_array'],
                'wavelengths': lib_data['metadata'].get('wavelengths'),
                'names': lib_data['metadata'].get('spectra_names', 
                    [f'Spectrum_{i}' for i in range(lib_data['library_array'].shape[1])]),
                'num_bands': lib_data['library_array'].shape[0],
                'num_spectra': lib_data['library_array'].shape[1]
            }
            
            self.create_spectrum_checkboxes(self.current_library)
            self.plot_data(self.current_library)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load library: {str(e)}")
            
    def on_second_library_selected(self, index):
        """Handle second library selection"""
        if index <= 0:  
            self.update_plot_visibility()
            return
            
        lib_path = self.second_lib_combo.currentData()
        if not lib_path:
            return
            
        try:
            lib_data = self.spectral_libraries[lib_path]
            self.second_library = {
                'spectra': lib_data['library_array'],
                'wavelengths': lib_data['metadata'].get('wavelengths'),
                'names': lib_data['metadata'].get('spectra_names', 
                    [f"Lib2_Spectrum_{i}" for i in range(lib_data['library_array'].shape[1])]),
                'num_bands': lib_data['library_array'].shape[0],
                'num_spectra': lib_data['library_array'].shape[1]
            }
            
            self.create_spectrum_checkboxes(self.current_library, self.second_library)
            self.update_plot_visibility()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load second library: {str(e)}")    
            
    def create_spectrum_checkboxes(self, first_library, second_library=None):
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.spectrum_checkboxes = []
        
        first_lib_container = QWidget()
        first_lib_layout = QVBoxLayout(first_lib_container)
        first_lib_layout.setContentsMargins(0, 0, 0, 0)
        
        first_lib_label = QLabel("First Library Spectra:")
        first_lib_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        first_lib_layout.addWidget(first_lib_label)
        
        self._add_library_checkboxes(first_library, first_lib_layout)
        self.checkbox_layout.addWidget(first_lib_container)
        
        if second_library is not None:
            second_lib_container = QWidget()
            second_lib_layout = QVBoxLayout(second_lib_container)
            second_lib_layout.setContentsMargins(0, 0, 0, 0)
            
            second_lib_label = QLabel("Second Library Spectra:")
            second_lib_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            second_lib_layout.addWidget(second_lib_label)
            
            self._add_library_checkboxes(second_library, second_lib_layout, is_second_lib=True)
            self.checkbox_layout.addWidget(second_lib_container)
        
        self.checkbox_layout.addStretch()

    def _add_library_checkboxes(self, library, layout, is_second_lib=False):
        """Helper method to add checkboxes for a library"""
        for i, name in enumerate(library['names']):
            if name not in self.spectrum_colors:
                color_idx = len(self.spectrum_colors) % 20
                self.spectrum_colors[name] = plt.cm.tab20(color_idx)
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            
            # Add color indicator and checkbox
            color_indicator = QWidget()
            color_indicator.setFixedSize(15, 15)
            color = self.spectrum_colors[name]
            color_rgba = [int(c * 255) for c in color]
            style = f"""
                background-color: rgba({color_rgba[0]}, {color_rgba[1]}, 
                                    {color_rgba[2]}, {color_rgba[3]});
                border: 1px solid black;
                border-radius: 2px;
            """
            color_indicator.setStyleSheet(style)
            
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_plot_visibility)
            
            row_layout.addWidget(color_indicator)
            row_layout.addWidget(checkbox)
            row_layout.addStretch()
            
            layout.addWidget(row_widget)
            self.spectrum_checkboxes.append((checkbox, is_second_lib))
        
    def update_plot_visibility(self):
        """Update plot based on checkbox states for both libraries"""
        if not hasattr(self, 'current_library'):
            return
        
        # Clear any existing annotation when updating plot
        if hasattr(self, 'annotation') and self.annotation:
            try:
                self.annotation.remove()
            except:
                pass
            self.annotation = None
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        self._plot_library_data(ax, self.current_library, False)
        
        if hasattr(self, 'second_library'):
            self._plot_library_data(ax, self.second_library, True)
        
        ax.set_xlabel('Wavelength (nm)' if self.current_library['wavelengths'] is not None else 'Band Number')
        ax.set_ylabel('Reflectance')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _plot_library_data(self, ax, library, is_second_lib):
        """Helper method to plot data from a single library"""
        if library['wavelengths'] is not None:
            wavelengths = np.array([float(w) for w in library['wavelengths']])
            x_values = wavelengths
        else:
            x_values = np.arange(library['num_bands'])
        
        if not hasattr(self, 'plotted_spectra'):
            self.plotted_spectra = {}
        
        for checkbox, is_second in self.spectrum_checkboxes:
            if is_second == is_second_lib and checkbox.isChecked():
                name = checkbox.text()
                if name in library['names']:
                    idx = library['names'].index(name)
                    spectrum = library['spectra'][:, idx]
                    
                    mask = spectrum != 0
                    
                    x_split = np.split(x_values[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
                    y_split = np.split(spectrum[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
                    
                    # Store the spectrum data for later use
                    self.plotted_spectra[name] = {
                        'x_values': x_values,
                        'spectrum': spectrum,
                        'color': self.spectrum_colors[name]
                    }
                    
                    # Plot each segment separately
                    for x_segment, y_segment in zip(x_split, y_split):
                        ax.plot(x_segment, y_segment, 
                            label=name if x_segment is x_split[0] else "", 
                            color=self.spectrum_colors[name])
        
    def plot_data(self, data):
        """Initial plot of the spectral library"""
        if hasattr(self, 'annotation') and self.annotation:
            try:
                self.annotation.remove()
            except:
                pass
            self.annotation = None
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if data['wavelengths'] is not None:
            wavelengths = np.array([float(w) for w in data['wavelengths']])
            x_values = wavelengths
            x_label = 'Wavelength (nm)'
            
            if len(wavelengths) > 20:
                step = len(wavelengths) // 10
                ax.set_xticks(wavelengths[::step])
                ax.set_xticklabels([f"{x:.0f}" for x in wavelengths[::step]])
        else:
            x_values = np.arange(data['num_bands'])
            x_label = 'Band Number'
        
        for i in range(data['num_spectra']):
            name = data['names'][i]
            spectrum = data['spectra'][:, i]
            
            mask = spectrum != 0
            
            x_split = np.split(x_values[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
            y_split = np.split(spectrum[mask], np.where(np.diff(np.where(mask)[0]) != 1)[0] + 1)
            
            for x_segment, y_segment in zip(x_split, y_split):
                ax.plot(x_segment, y_segment, 
                    label=name if x_segment is x_split[0] else "", 
                    color=self.spectrum_colors[name])
        
        ax.set_xlabel(x_label)
        ax.set_ylabel('Reflectance')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def on_plot_click(self, event):
        """Handle mouse clicks on the plot"""
        if event.inaxes is None or not hasattr(self, 'current_library'):
            return
        
        if hasattr(self, 'annotation') and self.annotation:
            self.annotation.remove()
            self.annotation = None
        
        x_click, y_click = event.xdata, event.ydata
        
        min_dist = float('inf')
        closest_point = None
        spectrum_name = None
        
        ax = event.inaxes
        
        libraries = [(self.current_library, False)]
        if hasattr(self, 'second_library'):
            libraries.append((self.second_library, True))
        
        for library, is_second_lib in libraries:
            if library['wavelengths'] is not None:
                wavelengths = np.array([float(w) for w in library['wavelengths']])
            else:
                wavelengths = np.arange(library['num_bands'])
            
            x_range = np.ptp(wavelengths)
            y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
            
            for checkbox_tuple in self.spectrum_checkboxes:
                checkbox, is_second = checkbox_tuple
                if is_second == is_second_lib and checkbox.isChecked():
                    name = checkbox.text()
                    if name in library['names']:
                        idx = library['names'].index(name)
                        spectrum = library['spectra'][:, idx]
                        
                        x_idx = np.abs(wavelengths - x_click).argmin()
                        x_val = wavelengths[x_idx]
                        y_val = spectrum[x_idx]
                        
                        dx = (x_val - x_click) / x_range
                        dy = (y_val - y_click) / y_range
                        dist = np.sqrt(dx**2 + dy**2)
                        
                        if dist < min_dist:
                            min_dist = dist
                            closest_point = (x_val, y_val)
                            spectrum_name = name
        
        if closest_point and min_dist < 0.1: 
            text = f'{spectrum_name}\nλ: {closest_point[0]:.1f} nm\nR: {closest_point[1]:.3f}'
            
            ymin, ymax = ax.get_ylim()
            if closest_point[1] > (ymin + ymax) / 2:
                xytext = (10, -15)  
            else:
                xytext = (10, 15)   
            
            self.annotation = ax.annotate(
                text,
                xy=closest_point,
                xytext=xytext,
                textcoords='offset points',
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    fc='yellow',
                    alpha=0.8,
                    edgecolor='black'
                ),
                arrowprops=dict(
                    arrowstyle='->',
                    connectionstyle='arc3,rad=0',
                    color='black'
                )
            )
            
            self.canvas.draw_idle()
            
    def calculate_sam(self, spectrum1, spectrum2):
        """Calculate Spectral Angle Mapper between two spectra"""
        if spectrum1.shape[0] != spectrum2.shape[0]:
            QMessageBox.warning(self, "Error", 
                f"Spectra have different number of bands:\nSpectrum 1: {spectrum1.shape[0]} bands\n" + 
                f"Spectrum 2: {spectrum2.shape[0]} bands\nCannot calculate SAM.")
            return None
        
        mask = (spectrum1 != 0) & (spectrum2 != 0)
        spectrum1 = spectrum1[mask]
        spectrum2 = spectrum2[mask]
        
        dot_product = np.sum(spectrum1 * spectrum2)
        norm1 = np.sqrt(np.sum(spectrum1 * spectrum1))
        norm2 = np.sqrt(np.sum(spectrum2 * spectrum2))
        
        if norm1 == 0 or norm2 == 0:
            return None
            
        cos_angle = dot_product / (norm1 * norm2)
        # Clip to handle floating point errors
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg

    def compare_selected_spectra(self):
        """Compare selected spectra using SAM"""
        selected_spectra = []
        
        for checkbox, is_second in self.spectrum_checkboxes:
            if checkbox.isChecked():
                name = checkbox.text()
                if name in self.plotted_spectra:
                    selected_spectra.append((name, self.plotted_spectra[name]['spectrum']))
        
        if len(selected_spectra) != 2:
            QMessageBox.warning(self, "Warning", 
                "Please select exactly 2 spectra to compare.")
            return
        
        angle = self.calculate_sam(selected_spectra[0][1], selected_spectra[1][1])
        
        if angle is None:
            QMessageBox.warning(self, "Warning", 
                "Could not calculate SAM - invalid spectra.")
            return
        
        QMessageBox.information(self, "SAM Result", 
            f"Spectral Angle between\n{selected_spectra[0][0]} and {selected_spectra[1][0]}:\n"
            f"{angle:.2f} degrees\n\n"
            f"Similarity: {100 - angle:.1f}%")