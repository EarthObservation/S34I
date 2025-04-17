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

def apply_mask(image_array, non_masked_indices):
    """
    cria uma variavel composta por [(1, array (b1,b2,b3 etc))]
    depois é preciso reconstruir a imagem associando o idx a lista "non_masked_indices"
    """
    non_masked_pixels = []
    for idx, (row, col) in enumerate(non_masked_indices, 1):
        if image_array.shape[2] > 1:  # Multi-band image
            band_values = image_array[row, col, :]
        else:  
            band_values = image_array[row, col]
        
        non_masked_pixels.append((idx, band_values))
        
    return non_masked_pixels

def extract_bands(image_array, non_masked_indices):
    """
    Returns a list of masked band values (no indices).
    """
    extracted_bands = []
    for row, col in non_masked_indices:  
        if image_array.ndim == 3:  # Multi-band image
            band_values = image_array[row, col, :]
        else:  # Single-band image
            band_values = image_array[row, col]
        extracted_bands.append(band_values)
    return extracted_bands

def retrieve_reduction_on_ppi(result_rd_espectral, pure_pixel_indices):  
    pure_pixel_data = []
    for row, col in pure_pixel_indices:
        spectral_data = result_rd_espectral[row, col, :].squeeze()
        pure_pixel_data.append(spectral_data)  
        
    pure_pixel_array = np.array(pure_pixel_data)

    return pure_pixel_array

def image_recovery(recontruir, non_masked_indices, rows, cols):
    """
    Recontruir = results_ica, 
    Função que recupera a imagem original a partir dos pixeis reduzidos
    """
    n_pixels, n_bands = recontruir.shape
    recovered_image = np.full((rows, cols, n_bands), np.nan, dtype=np.float32)
    try:
        for idx, (row, col) in enumerate(non_masked_indices):
            if row < rows and col < cols:  
                recovered_image[row, col, :] = recontruir[idx, :]
    except Exception as e:
        print(f"Error in image recovery: {e}")
        print(f"Shape of recontruir: {recontruir.shape}")
        print(f"Number of indices: {len(non_masked_indices)}")
        raise
        
    return recovered_image