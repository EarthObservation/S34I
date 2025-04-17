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

def save_library(endmember_spectra, file_name, metadata, names=None):
        
        spectral_data = np.array(list(endmember_spectra.values()))  # (n_endmembers, n_bands)
        
        if metadata.get('wavelengths') is not None:
            wavelengths = [float(w) for w in metadata['wavelengths']]
        else:
            wavelengths = list(range(1, metadata["bands"] + 1))
        
        n_endmembers, n_bands = spectral_data.shape
        sli_file = file_name if file_name.lower().endswith('.sli') else f"{file_name}.sli"
        hdr_file = f"{sli_file.replace('.sli', '.hdr')}"
        
        spectral_data.astype(np.float32).tofile(sli_file)
        
        with open(hdr_file, 'w') as hdr:
            hdr.write("ENVI\n")
            hdr.write("description = {Generated Spectral Library}\n")
            hdr.write(f"samples = {n_bands}\n")
            hdr.write(f"lines = {n_endmembers}\n")
            hdr.write("bands = 1\n")
            hdr.write("header offset = 0\n")
            hdr.write("file type = ENVI Spectral Library\n")
            hdr.write("data type = 4\n")  # 4 = 32-bit float
            hdr.write("interleave = bsq\n")
            hdr.write("byte order = 0\n")
            hdr.write(f"wavelength = {{ {', '.join(map(str, wavelengths))} }}\n")
            hdr.write("wavelength units = Nanometers\n")
            
            if names is not None and isinstance(names, (list, tuple)) and len(names) == n_endmembers:
                hdr.write(f"spectra names = {{ {', '.join(str(name) for name in names)} }}\n")