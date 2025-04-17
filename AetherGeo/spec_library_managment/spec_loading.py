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
from spectral import envi

def spectral_library_load(filepath):
    """
    Opens an ENVI spectral library (.hdr + .sli)
    
    Args:
        filepath (str): Path to spectral library file (.hdr or .sli)
        
    Returns:
        tuple: (library_array, metadata)
            - library_array: numpy array of shape (bands, samples)
            - metadata: dictionary with library information
    """
    try:
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext in ['.hdr', '.sli']:
            base_filepath = os.path.splitext(filepath)[0]
            
            try:
                header = envi.read_envi_header(base_filepath + '.hdr')
            except:
                raise FileNotFoundError(f"Could not find or read header file at {base_filepath}.hdr")
                
            num_spectra = int(header['lines'])
            num_bands = int(header['samples'])
            interleave = header.get('interleave', 'bsq').lower()
            
            try:
                spectra = np.fromfile(base_filepath + '.sli', dtype=np.float32)
            except:
                raise FileNotFoundError(f"Could not find or read data file at {base_filepath}.sli")
            
            if interleave == 'bsq':
                # BSQ: Band Sequential
                spectra = spectra.reshape((num_spectra, num_bands)).T
            elif interleave == 'bip':
                # BIP: Band Interleaved by Pixel
                spectra = spectra.reshape(num_bands, num_spectra)
            else:
                raise ValueError(f"Unsupported interleave format: {interleave}")
                
            metadata = {
                'format': 'ENVI',
                'interleave': interleave,
                'samples': num_spectra,
                'bands': num_bands,
                'wavelengths': header.get('wavelength', None),
                'spectra_names': header.get('spectra names', [f'Spectrum_{i}' for i in range(num_spectra)]),
                'path': filepath,
                'header': header # Full header
            }
            
        elif file_ext == '.txt':
            # Handle text file format
            try:
                data = np.loadtxt(filepath, skiprows=1, delimiter='\t')
                wavelengths = data[:, 0]
                spectra = data[:, 1:]  # Shape will be (bands, samples)
                
                # Get spectrum name from header
                with open(filepath, 'r') as f:
                    header_line = f.readline().strip()
                    spectrum_name = header_line.split('\t')[1:]  # Skip 'Wavelength' column
                
                metadata = {
                    'format': 'TXT',
                    'interleave': 'bip',
                    'samples': spectra.shape[1],
                    'bands': len(wavelengths),
                    'wavelengths': wavelengths,
                    'spectra_names': spectrum_name,
                    'path': filepath,
                    'header': None
                }
                
            except Exception as e:
                raise ValueError(f"Error reading text file: {str(e)}")
        
        return spectra, metadata
        
    except Exception as e:
        raise Exception(f"Failed to load spectral library: {str(e)}")