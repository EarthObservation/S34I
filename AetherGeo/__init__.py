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

import sys
import os
import numpy as np

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QCheckBox,
                            QFileDialog, QToolBar, QListWidget, QListWidgetItem,
                            QMessageBox, QStackedWidget, QScrollArea, QSizePolicy, 
                            QMenu
                            )
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer, QSize

from preprocessing_control_view.wavelength_assignment import WavelengthsControlsView
from preprocessing_control_view.normalization import NormalizationControlsView

from dim_red_control_view.dim_red_control_view import DimRedFunctionControlsView
from dim_red_control_view.pca_reduction import PCAOperations
from dim_red_control_view.ica_reduction import ICAOperations
from dim_red_control_view.nmf_reduction import NMFOperations

from endmember_extraction_control_view.point_cloud_control_view import PointCloudControlsView
from endmember_extraction_control_view.point_cloud import PointCloudOperations
from endmember_extraction_control_view.pixel_purity_idx_control_view import PixelPurityIdxControlView
from endmember_extraction_control_view.pixel_purity_idx import PixelPurityIdxOperations

from spectral_unmixing_control_view.sam_control_view import SAMControlsView
from spectral_unmixing_control_view.sam import SAMOperations

from clustering_control_view.k_means_clustering_control_view import KmeansControlsView 
from clustering_control_view.k_means import KMeansOperations
from clustering_control_view.optics_clustering_control_view import OPTICSControlsView
from clustering_control_view.optics import OPTICSOperations
from clustering_control_view.mean_spectra_control_view import MeanSpectraControlsView
from clustering_control_view.mean_spectra import MeanSpectraOperations

from spec_library_managment import spec_loading

from spectra_analyst_window.spectra_analyst_window import SpectraAnalystWindow

from others_control_view.band_ratios_control_view import BandRatiosControlsView

from image_manipulation import manipulation, loading

from image_configs.band_selection_panel import BandSelectionPanel
from image_configs.image_adjustment_panel import ImageAdjustmentPanel
from image_configs.metadata_dialog_panel import MetadataDialog

from gl_widget import ImageGLWidget

from icon_functions.plot_window import PlotWindow
from icon_functions.help_window import HelpWindow
from icon_functions.license_window import LicenseWindow

class ImageListItem(QWidget):
    def __init__(self, image_name, path, parent=None):
        super().__init__(parent)
        self.path = path
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        self.name_label = QLabel(image_name)
        self.selection_toggle = QCheckBox()
        self.selection_toggle.setChecked(False)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.name_label)
        layout.addWidget(self.selection_toggle)
        self.setLayout(layout)

    def show_context_menu(self, position):
        menu = QMenu(self)  
        view_meta_action = menu.addAction("View Metadata")
        action = menu.exec(self.mapToGlobal(position)) # Map position relative to THIS widget

        if action == view_meta_action:
            main_window = self.get_main_window()
            if main_window:
                main_window.show_metadata_dialog(self.path)

    def get_main_window(self):
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parentWidget()
        return None
       
class FunctionListItem(QWidget):
    """Main widget listing available analysis functions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Main application window
        self.control_views = {}
        self.function_view = QWidget()  
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.stack)

        self.setup_function_view()
        main_scroll_area = QScrollArea()
        main_scroll_area.setWidgetResizable(True)
        main_scroll_area.setWidget(self.function_view)
        self.stack.addWidget(main_scroll_area)
        self.main_scroll_area = main_scroll_area

    def setup_function_view(self):
        """Create the main menu with function buttons"""
        if self.function_view.layout():
            QWidget().setLayout(self.function_view.layout())
            
        layout = QVBoxLayout(self.function_view)
        
        pre_process_functions_label = QLabel("Pre-Processing")
        pre_process_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pre_process_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(pre_process_functions_label)
        
        self.add_function_button("Data Normalization", self.show_normalization_controls)
        self.add_function_button("Attribute Wavelengths", self.show_wavelengths_controls)
        
        Dim_Red_functions_label = QLabel("Dimensionality Reduction")
        Dim_Red_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        Dim_Red_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(Dim_Red_functions_label)

        self.add_function_button("Principal Component Analysis", self.show_pca_controls)
        self.add_function_button("Independent Component Analysis", self.show_ica_controls)
        self.add_function_button("Non-negative Matrix Factorization", self.show_nmf_controls)
        
        End_Extract_functions_label = QLabel("Endmember Extraction")
        End_Extract_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        End_Extract_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(End_Extract_functions_label)
        
        self.add_function_button("Pixel Purity Index", self.show_ppi_controls)
        self.add_function_button("Point Cloud Extraction", self.show_point_cloud_controls)
        
        unmixing_functions_label = QLabel("Spectral Unmixing")
        unmixing_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unmixing_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(unmixing_functions_label)
        
        self.add_function_button("Spectral Angle Mapper", self.show_sam_controls)
        
        Clustering_functions_label = QLabel("Clustering")
        Clustering_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        Clustering_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(Clustering_functions_label)
        
        self.add_function_button("OPTICS", self.show_optics_controls)
        self.add_function_button("K-means", self.show_k_means_controls)
        self.add_function_button("Mean Spectra from Cluster", self.mean_spectra_controls)
        
        Spec_analysis_functions_label = QLabel("Spectral Libraries")
        Spec_analysis_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        Spec_analysis_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(Spec_analysis_functions_label)
        
        self.add_function_button("Import Library", self.show_import_library_controls)
        self.add_function_button("Spectra Analyst", self.show_spectra_analyst) 
        
        Others_functions_label = QLabel("Others")
        Others_functions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        Others_functions_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(Others_functions_label)
        
        self.add_function_button("Band Ratios", self.show_band_ratios_controls)
        
        layout.addStretch()

    def add_function_button(self, name, callback):
        """Create a unified button for a specific function"""
        btn = QPushButton(name)
        btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                background: #404040;
                border: none;
                border-radius: 4px;
                margin: 2px 5px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        btn.clicked.connect(callback)
        self.function_view.layout().addWidget(btn)

    def show_normalization_controls(self):
        """Show normalization control view."""
        self.show_function_controls("Data Normalization")

    def show_wavelengths_controls(self):
        """Show wavelength assignment control view"""
        self.show_function_controls("Wavelengths from Satellite")
    
    def show_pca_controls(self):
        """Show PCA control view"""
        self.show_function_controls("PCA")

    def show_ica_controls(self):
        """Show ICA control view"""
        self.show_function_controls("ICA")
        
    def show_nmf_controls(self):
        """Show NMF control view"""
        self.show_function_controls("NMF")

    def show_ppi_controls(self):
        """Show Pixel Purity Index control view"""
        self.show_function_controls("Pixel Purity Index")
    
    def show_point_cloud_controls(self):
        """Show Point Cloud Extraction control view"""
        self.show_function_controls("Point Cloud Extraction")
  
    def show_sam_controls(self):
        """Show SAM control view"""
        self.show_function_controls("SAM")
    
    def show_optics_controls(self):
        """Show OPTICS control view"""
        self.show_function_controls("OPTICS")

    def show_k_means_controls(self):
        """Show K-means control view"""
        self.show_function_controls("K-means")
  
    def mean_spectra_controls(self):
        """Show mean spectra control view"""
        self.show_function_controls("Mean Spectra from Cluster")
  
    def show_import_library_controls(self):
        """Show file dialog for spectral library import"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Spectral Library",
            "",
            "Spectral Libraries (*.hdr *.hdr *.txt *.csv *.asd);;All Files (*)"
        )
        if file_name:
            self.run_import_library(file_name)
    
    def show_spectra_analyst(self):
        """Open Spectra Analyst window"""
        main_window = self.parent
        
        if not hasattr(main_window, 'spectral_libraries') or not main_window.spectral_libraries:
            QMessageBox.warning(self, "Warning", "No spectral libraries imported. Please import a library first.")
            return
            
        if not hasattr(self, 'spectra_analyst_window'):
            self.spectra_analyst_window = SpectraAnalystWindow(main_window.spectral_libraries, self)
        else:
            self.spectra_analyst_window.refresh_libraries()
            
        self.spectra_analyst_window.show()
    
    def show_band_ratios_controls(self):
        """Show Band Ratio control view"""
        self.show_function_controls("Band Ratios")
    
    def create_control_view(self, function_name):
        """Create and return a control view for the specified function."""
        if function_name == "Data Normalization":
            run_callback = self.run_normalization
            control_view = NormalizationControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "Wavelengths from Satellite":
            run_callback = self.run_wavelengths  
            control_view = WavelengthsControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "PCA":
            run_callback = self.run_pca
            control_view = DimRedFunctionControlsView(
            function_name=function_name,
            parent=self,  
            run_callback=run_callback
        )
        elif function_name == "ICA":
            run_callback = self.run_ica
            control_view = DimRedFunctionControlsView(
            function_name=function_name,
            parent=self,  
            run_callback=run_callback
        )
        elif function_name == "NMF":
            run_callback = self.run_nmf
            control_view = DimRedFunctionControlsView(
            function_name=function_name,
            parent=self,  
            run_callback=run_callback
        )
        elif function_name == "Pixel Purity Index":   
            run_callback = self.run_ppi
            control_view = PixelPurityIdxControlView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "Point Cloud Extraction":
            run_callback = self.run_point_cloud
            control_view = PointCloudControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "SAM":
            run_callback = self.run_sam
            control_view = SAMControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )    
        elif function_name == "OPTICS":
            run_callback = self.run_optics
            control_view = OPTICSControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "K-means":
            run_callback = self.run_k_means
            control_view = KmeansControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "Mean Spectra from Cluster":
            run_callback = self.run_mean_spectra
            control_view = MeanSpectraControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        elif function_name == "Band Ratios":
            run_callback = self.run_band_ratios
            control_view = BandRatiosControlsView(
                function_name=function_name,
                parent=self,
                run_callback=run_callback
        )
        else:
            return None
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(control_view)
        scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.stack.addWidget(scroll_area)
        self.control_views[function_name] = scroll_area
        return scroll_area
        
    def show_function_controls(self, function_name):
        """Show specified function's control view (now in scroll area)"""
        if function_name not in self.control_views:
            self.create_control_view(function_name)
        
        scroll_area = self.control_views[function_name]
        control_view = scroll_area.widget()
        control_view.refresh_images()
        self.stack.setCurrentWidget(scroll_area)

    def show_main_view(self):
        """Return to main function menu"""
        self.stack.setCurrentWidget(self.main_scroll_area)

    def run_normalization(self, path, mask_path):
        """Execute pixel-wise Min-Max normalization to [0, 1]."""
        try:
            main_window = self.parent
            image_data = main_window.image_data[path]
            array = image_data["array"]  
            metadata = image_data["metadata"]
            rows, cols, bands = array.shape

            if mask_path and mask_path in main_window.image_data:
                mask_data = main_window.image_data[mask_path]
                if (rows, cols) != (mask_data["metadata"]["rows"], mask_data["metadata"]["cols"]):
                    QMessageBox.warning(self, "Error", "Image and mask dimensions mismatch.")
                    return
                non_masked_indices = mask_data["non_masked_indices"]
            else:
                non_masked_indices = image_data["non_masked_indices"]

            masked = manipulation.apply_mask(array, non_masked_indices)
            masked.sort(key=lambda x: x[0])  
            img_2d = np.column_stack([band_values for _, band_values in masked])  

            #--- Pixel-wise Min-Max scaling to [0, 1] ---
            min_vals = img_2d.min(axis=1, keepdims=True)
            max_vals = img_2d.max(axis=1, keepdims=True)
            range_vals = max_vals - min_vals
            range_vals[range_vals == 0] = 1  # Avoid division by zero for flat pixels
            img_normalized = (img_2d - min_vals) / range_vals

            img_normalized = img_normalized.T  

            control_view = self.control_views["Data Normalization"].widget()
            control_view.result_data = img_normalized

            QMessageBox.information(self, "Success", "Pixel normalization to [0, 1] completed!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Normalization failed: {str(e)}")
    
    def run_wavelengths(self, path, satellite):
        """Placeholder for satellite wavelength assignment"""
        try:
            main_window = self.parent
            image_data = main_window.image_data[path]
            wavelengths = image_data["metadata"]["wavelengths"]
            
            if wavelengths is not None:
                QMessageBox.warning(self, "Error", "Image already has wavelengths atributed.")    
                return
            
            if satellite == "WorldView-3":
                wavelengths = [
                    427, 478, 546, 608, 659, 724, 833, 949, 1195, 1570, 1660, 1725, 2165, 2205, 2260, 2335
                ]
            elif satellite == "EnMap":
                wavelengths = [
                    420, 426, 432, 438, 444, 450, 456, 462, 468, 474, 480, 486, 492, 498, 504, 510,
                    516, 522, 528, 534, 540, 546, 552, 558, 564, 570, 576, 582, 588, 594, 600, 606,
                    612, 618, 624, 630, 636, 642, 648, 654, 660, 666, 672, 678, 684, 690, 696, 702,
                    708, 714, 720, 726, 732, 738, 744, 750, 756, 762, 768, 774, 780, 786, 792, 798,
                    804, 810, 816, 822, 828, 834, 840, 846, 852, 858, 864, 870, 876, 882, 888, 894,
                    900, 906, 912, 918, 924, 930, 936, 942, 948, 954, 960, 966, 972, 978, 984, 990, 993,
                    1006, 1018, 1029, 1041, 1052, 1064, 1075, 1087, 1098, 1110, 1121, 1133, 1144, 1156, 1167, 1179,
                    1190, 1202, 1213, 1225, 1236, 1248, 1259, 1271, 1282, 1294, 1305, 1317, 1328, 1340, 1351, 1363,
                    1374, 1386, 1397, 1409, 1420, 1432, 1443, 1455, 1466, 1478, 1489, 1501, 1512, 1524, 1535, 1547,
                    1558, 1570, 1581, 1593, 1604, 1616, 1627, 1639, 1650, 1662, 1673, 1685, 1696, 1708, 1719, 1731,
                    1742, 1754, 1765, 1777, 1788, 1800, 1811, 1823, 1834, 1846, 1857, 1869, 1880, 1892, 1903, 1915,
                    1926, 1938, 1949, 1961, 1972, 1984, 1995, 2007, 2018, 2030, 2041, 2053, 2064, 2076, 2087, 2099,
                    2110, 2122, 2133, 2145, 2156, 2168, 2179, 2191, 2202, 2214, 2225, 2237, 2248, 2260, 2271, 2283,
                    2294, 2306, 2317, 2329, 2340, 2352, 2363, 2375, 2386, 2398, 2409, 2421, 2432, 2444, 2445
                ]
            elif satellite == "PRISMA":
                vnir_bands = [round(400 + (1010 - 400) / 65 * i, 1) for i in range(66)]
                swir_bands = [round(1010 + (2500 - 1010) / 172 * i, 1) for i in range(173)]
                wavelengths = vnir_bands + swir_bands
            
            if image_data["metadata"]["bands"] != len(wavelengths):
                QMessageBox.warning(self, "Error", "Image and wavelength list dimensions do not match.")
                return
            
            if "Wavelengths from Satellite" in self.control_views:
                control_view = self.control_views["Wavelengths from Satellite"].widget()
                control_view.result_data = wavelengths
            else:
                print("Warning: Wavelengths control view not found to store results.")
            
            QMessageBox.information(self, "Success", f"Applied {satellite} wavelengths!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wavelength assignment failed: {str(e)}")
    
    def run_pca(self, path, n_components):
        """Delegate PCA execution to PCAOperations class"""
        self.pca_operations = PCAOperations(self)
        self.pca_operations.execute(path, n_components)

    def run_ica(self, path, n_components):
        """Delegate ICA execution to ICAOperations class"""
        self.ica_operations = ICAOperations(self)
        self.ica_operations.execute(path, n_components)

    def run_nmf(self, path, n_components):
        """Delegate NMF execution to ICAOperations class"""
        self.nmf_operations = NMFOperations(self)
        self.nmf_operations.execute(path, n_components)
    
    def run_point_cloud(self, path, mask_path, ppi_path):
        """Delegate point cloud generation to PointCloudOperations class"""
        self.point_cloud_operations = PointCloudOperations(self)
        self.point_cloud_operations.execute(path, mask_path, ppi_path)
        
    def run_ppi(self, path, mask_path, n_projection):
        """Delegate PPI execution to PPIOperations class"""
        self.ppi_operations = PixelPurityIdxOperations(self)
        self.ppi_operations.execute(path, mask_path, n_projection)
        
    def run_sam(self, path, spectral_library, spectrum_name):
        """Delegate SAM execution to PPIOperations class"""
        self.sam_operations = SAMOperations(self)
        self.sam_operations.execute(path, spectral_library, spectrum_name)
        
    def run_optics(self, path, mask_path, min_samples, xi, min_cluster_size):
        """Delegate K-Means execution to PPIOperations class"""
        self.optics_operations = OPTICSOperations(self)
        self.optics_operations.execute(path, mask_path, min_samples, xi, min_cluster_size)
    
    def run_k_means(self, path, mask_path, n_components):
        """Delegate K-Means execution to PPIOperations class"""
        self.kmeans_operations = KMeansOperations(self)
        self.kmeans_operations.execute(path, mask_path, n_components)
    
    def run_mean_spectra(self, original_image, cluster_image):
        """Delegate Mean Spectra execution to MeanSpectraOperations class"""
        self.kmeans_operations = MeanSpectraOperations(self)
        self.kmeans_operations.execute(original_image, cluster_image)
    
    def run_import_library(self, file_path):
        """Import and store spectral library data"""
        try:
            main_window = self.parent
            
            if not hasattr(main_window, 'spectral_libraries'):
                main_window.spectral_libraries = {}
                
            library_array, metadata = spec_loading.spectral_library_load(file_path)
            
            main_window.spectral_libraries[file_path] = {
                'library_array': library_array,
                'metadata': metadata
            }
            
            QMessageBox.information(self, "Success", f"Spectral library imported: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Library import failed: {str(e)}")
    
    def run_band_ratios(self, path, equation):
        """Execute custom band equation calculation"""
        try:
            import re
            image_data = self.parent.image_data[path]
            array = image_data["array"]
            metadata = image_data["metadata"]
            non_masked_indices = image_data["non_masked_indices"]
            
            masked_data = manipulation.extract_bands(array, non_masked_indices)
            
            if isinstance(masked_data[0], np.ndarray): 
                masked_array = np.array(masked_data)
            else:  # Single-band (reshape to 2D)
                masked_array = np.array(masked_data).reshape(-1, 1)

            if masked_array.ndim != 2:
                raise ValueError("Masked array must be 2D (n_pixels, n_bands)")
            
            bands_used = list(map(int, re.findall(r'B(\d+)', equation)))
            if not bands_used:
                raise ValueError("No valid bands in equation")

            max_band = max(bands_used)
            if max_band > masked_array.shape[1]:
                raise ValueError(f"Band {max_band} exceeds available bands ({masked_array.shape[1]})")

            band_arrays = {}
            for b in bands_used:
                band_idx = b - 1  # 0-based index
                band_data = masked_array[:, band_idx].astype(float)
                band_arrays[f'B{b}'] = band_data

            with np.errstate(divide='ignore', invalid='ignore'):
                result = eval(equation, {'__builtins__': None}, band_arrays)
                result = np.squeeze(result)  
            
            result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

            control_view = self.control_views["Band Ratios"].widget()
            control_view.result_data = result
            
            QMessageBox.information(self, "Success", "Calculation completed!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Operation failed: {str(e)}")
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AetherGeo")
        self.setGeometry(5, 50, 1900, 900)
        self.image_paths = []
        self.image_data = {}
        self.band_indices = {}

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: #2D2D2D;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                min-width: 40px;
                min-height: 40px;
                padding: 5px;
            }
            QToolButton:hover {
                background: #505050;
            }
            QToolButton:pressed {
                background: #606060;
            }
        """)
        self.addToolBar(self.toolbar)
        
        plot_btn = QPushButton()
        plot_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "Plot.png")))  
        plot_btn.setIconSize(QSize(35, 35))
        plot_btn.setFixedSize(40, 40)
        plot_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        plot_btn.clicked.connect(self.plot_function)
        self.toolbar.addWidget(plot_btn)
        
        help_menu_btn = QPushButton()
        help_menu_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "Manual.png")))  
        help_menu_btn.setIconSize(QSize(35, 35))
        help_menu_btn.setFixedSize(40, 40) 
        help_menu_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        help_menu_btn.clicked.connect(self.help_menu_function)
        self.toolbar.addWidget(help_menu_btn)
        
        license_btn = QPushButton()  
        license_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "License.png")))  
        license_btn.setIconSize(QSize(35, 35))
        license_btn.setFixedSize(40, 40)
        license_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        license_btn.clicked.connect(self.show_license)
        self.toolbar.addWidget(license_btn)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_layout = QVBoxLayout(left_panel)

        browse_btn = QPushButton("Import Raster")
        browse_btn.setFixedHeight(40)
        browse_btn.clicked.connect(self.browse_files)
        left_layout.addWidget(browse_btn)

        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_select)
        left_layout.addWidget(self.image_list)

        right_panel = QWidget()
        right_panel.setFixedWidth(300) 
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)  
        right_layout.setSpacing(0)

        self.function_item = FunctionListItem(self)
        right_layout.addWidget(self.function_item, 1) 
        
        self.gl_widget = ImageGLWidget()
        layout.addWidget(left_panel)        
        layout.addWidget(self.gl_widget)    
        layout.addWidget(right_panel)      
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_panel_position)
        self.timer.start(100)
        
        self.band_panel = BandSelectionPanel(self)
        self.band_panel.hide()
        self.band_panel.update_btn.clicked.connect(self.update_bands)
  
        QApplication.instance().processEvents()
        self.update_panel_position()
        
        for color in ['R', 'G', 'B']:
            self.band_panel.sliders[color].valueChanged.connect(
                lambda value, c=color: self.band_panel.value_labels[c].setText(str(value))
            )
            
        self.adjust_panel = ImageAdjustmentPanel(self)
        self.adjust_panel.hide()
        self.adjust_panel.apply_btn.clicked.connect(self.update_image_adjustments)
      
    def plot_function(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Error", "Please import an image first.")
            return
        
        self.plot_window = PlotWindow(self.image_paths, self)
        self.plot_window.show()
    
    def help_menu_function(self):
        """Show help window"""
        self.help_window = HelpWindow(self)
        self.help_window.show()
        
    def show_license(self):
        """Show license information"""
        self.license_window = LicenseWindow(self)
        self.license_window.show()
    
    def update_display_image(self):
        current_path = None
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            widget = self.image_list.itemWidget(item)
            if widget.selection_toggle.isChecked():
                current_path = widget.path
                break

        if not current_path:
            self.gl_widget.setImageData(None)
            return

        image_array = self.image_data[current_path]['array']

        if current_path in self.band_indices:
            indices = self.band_indices[current_path]
            r_idx = indices['R'] - 1
            g_idx = indices['G'] - 1
            b_idx = indices['B'] - 1
            image = image_array[:, :, [r_idx, g_idx, b_idx]]
        else:
            image = image_array

        sat = float(self.adjust_panel.saturation_value.text()) if self.adjust_panel.isVisible() else 1.5
        gamma = float(self.adjust_panel.gamma_value.text()) if self.adjust_panel.isVisible() else 0.7

        self.gl_widget.saturation = sat
        self.gl_widget.gamma = gamma

        non_masked_indices = self.image_data[current_path]['non_masked_indices']
        data = (non_masked_indices, image)
        self.gl_widget.setImageData(data)
    
    def update_image_adjustments(self):
        self.update_display_image()
    
    def update_panel_position(self):
        """Update panel positions after initial layout"""
        if hasattr(self, 'band_panel') and hasattr(self, 'adjust_panel'):
            gl_rect = self.gl_widget.geometry()
            toolbar_height = self.toolbar.height()
            
            self.band_panel.move(
                gl_rect.x() + gl_rect.width() - self.band_panel.width() - 12,
                gl_rect.y() + toolbar_height + 12
            )
            
            self.adjust_panel.move(
                gl_rect.x() + gl_rect.width() - self.adjust_panel.width() - 12,
                gl_rect.y() + gl_rect.height() - self.adjust_panel.height() + 32
            )
            
    def showEvent(self, event):
        """Handle initial positioning when window first appears"""
        super().showEvent(event)
        self.update_panel_position()

    def browse_files(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.hdr *.tif *.tiff *.he5);;All Files (*)"
        )
        if file_name:
            self.process_and_display_image(file_name)

    def process_image(self, file_path):
        image_tuple = loading.normal_image_load(file_path)
        raw_metadata = loading.metadata_extract(file_path)
        
        non_masked_indices = image_tuple[0]
        image_array = image_tuple[1]
        # Convert tuple to structured dictionary
        metadata = {
            'map_info': raw_metadata[0],
            'coordinates': raw_metadata[1],
            'cols': raw_metadata[2],
            'rows': raw_metadata[3],
            'bands': raw_metadata[4],
            'interleave': raw_metadata[5],
            'wavelengths': raw_metadata[6],
            'pixel_size_x': raw_metadata[7],
            'pixel_size_y': raw_metadata[8],
            'x_origin': raw_metadata[9],
            'y_origin': raw_metadata[10],
        }
        
        return image_array, metadata, non_masked_indices
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_panel_position()
    
    def show_metadata_dialog(self, path):
        metadata = self.image_data[path]['metadata']
        dialog = MetadataDialog(metadata, self)
        dialog.exec()
    
    def handle_image_selection(self, state, path):
        """Handle both checked and unchecked states"""
        if state == Qt.CheckState.Checked.value:
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                widget = self.image_list.itemWidget(item)
                if widget.path != path and widget.selection_toggle.isChecked():
                    widget.selection_toggle.setChecked(False)

            image_info = self.image_data[path]
            metadata = image_info['metadata']
            bands = metadata.get('bands', 1)

            if bands > 3:
                if path not in self.band_indices:
                    self.band_indices[path] = {'R': 1, 'G': 2, 'B': 3}
                for color in ['R', 'G', 'B']:
                    slider = self.band_panel.sliders[color]
                    slider.setMaximum(bands)
                    slider.setValue(self.band_indices[path][color])
                    self.band_panel.value_labels[color].setText(str(self.band_indices[path][color]))
                self.band_panel.show()
            else:
                self.band_panel.hide()

            self.adjust_panel.show()
            self.update_display_image()

        else:  
            current_selection = None
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                widget = self.image_list.itemWidget(item)
                if widget.selection_toggle.isChecked():
                    current_selection = widget.path
                    break

            if current_selection:
                image_array = self.image_data[path]['array']
                non_masked_indices = self.image_data[path]['non_masked_indices']
                data = (non_masked_indices, image_array)
                self.gl_widget.setImageData(data)
                if current_selection in self.band_indices:
                    self.band_panel.show()
                else:
                    self.band_panel.hide()
            else:
                self.gl_widget.setImageData(None)
                self.band_panel.hide()
                self.adjust_panel.hide()

    def process_and_display_image(self, file_path):
        if file_path not in self.image_paths:
            try:
                image_array, metadata, non_masked_indices = self.process_image(file_path)
                self.image_data[file_path] = {
                    'array': image_array,
                    'metadata': metadata,
                    'non_masked_indices': non_masked_indices
                }
                self.image_paths.append(file_path)
                
                item = QListWidgetItem(self.image_list)
                item_widget = ImageListItem(os.path.basename(file_path), file_path)
                item.setSizeHint(item_widget.sizeHint())
                self.image_list.addItem(item)
                self.image_list.setItemWidget(item, item_widget)
                
                item_widget.selection_toggle.stateChanged.connect(
                    lambda state, path=file_path: self.handle_image_selection(state, path)
                )
                    
            except Exception as e:
                print(f"Error loading image: {str(e)}")

    def on_image_select(self, item):
        item_widget = self.image_list.itemWidget(item)
        item_widget.selection_toggle.setChecked(True)
        
    def setup_band_combos(self, path):
        image_info = self.image_data[path]
        metadata = image_info['metadata']
        bands = metadata['bands']
        wavelengths = metadata.get('wavelengths', [])
        
        for combo in [self.band_panel.r_combo, self.band_panel.g_combo, self.band_panel.b_combo]:
            combo.clear()
            for i in range(bands):
                if wavelengths and i < len(wavelengths):
                    text = f"Band {i+1} ({wavelengths[i]} nm)"
                else:
                    text = f"Band {i+1}"
                combo.addItem(text, i)
            combo.setCurrentIndex(0)
            
    def update_bands(self):
        current_path = None
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            widget = self.image_list.itemWidget(item)
            if widget.selection_toggle.isChecked():
                current_path = widget.path
                break
        
        if not current_path:
            self.band_panel.hide()
            return
        
        if current_path and current_path in self.image_data:
            self.band_indices[current_path] = {
                'R': self.band_panel.sliders['R'].value(),
                'G': self.band_panel.sliders['G'].value(),
                'B': self.band_panel.sliders['B'].value()
            }
            
            r_idx = self.band_indices[current_path]['R'] - 1
            g_idx = self.band_indices[current_path]['G'] - 1
            b_idx = self.band_indices[current_path]['B'] - 1
            
            image_array = self.image_data[current_path]['array']
            composite = image_array[:, :, [r_idx, g_idx, b_idx]]
            non_masked_indices = self.image_data[current_path]['non_masked_indices']
            data = (non_masked_indices,composite)
            self.gl_widget.setImageData(data)
        else:
            print("Error: Invalid band selection for image array shape.")
            
    def add_function_item(self):
        item = QListWidgetItem()
        widget = FunctionListItem(self)
        item.setSizeHint(widget.sizeHint())
        self.function_list.addItem(item)
        self.function_list.setItemWidget(item, widget)
    
if __name__ == '__main__':
    app = QApplication(sys.argv) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 