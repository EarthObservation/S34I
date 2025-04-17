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
import os
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

def image_recovery(recontruir, non_masked_indices, rows, cols):
    """
    Recontruir = 2D array (pixels, bands), 
    Function rebuilds the image taking into account the non-masked indices.
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

def save_image(output_path, image_save, map_info, cords, cols, rows, pixel_size_x, pixel_size_y, x_origin, y_origin, wavelengths=None):
    """
    output_path = path to save the image
    image_save = recovered image array, no metadata 
    """
    if output_path is None:
        raise ValueError("Path cannot be None")
        
    if not output_path.lower().endswith(('.tif', '.tiff')):
        output_path += '.tif'
    
    if os.path.exists(output_path):
        raise ValueError("File already exists")
    
    try:
        if image_save.ndim == 3:
            img_rows, img_cols, bands = image_save.shape
        elif image_save.ndim == 2:
            img_rows, img_cols = image_save.shape
            bands = 1
            image_save = image_save.reshape(img_rows, img_cols, bands)
        else:
            raise ValueError("Unsupported image dimensions")
        
        transform = from_origin(x_origin, y_origin, pixel_size_x, pixel_size_y)
        
        if isinstance(cords, (list, tuple)):
            wkt_candidate = ",".join(cords)
            try:
                crs_obj = CRS.from_wkt(wkt_candidate)
                crs = crs_obj.to_wkt()  
            except Exception as e:
                raise RuntimeError(f"Invalid CRS provided: {str(e)}")
        else:
            try:
                crs_obj = CRS.from_wkt(cords)
                crs = crs_obj.to_wkt()
            except Exception:
                crs = cords
        
        with rasterio.open(
            output_path, 'w',
            driver='GTiff',
            height=img_rows,
            width=img_cols,
            count=bands,
            dtype='float32',
            transform=transform,
            crs=crs
        ) as dst:
            for band in range(bands):
                dst.write(image_save[:, :, band], band + 1)
                if wavelengths is not None:
                    dst.set_band_description(band + 1, f"{wavelengths[band]} nm")

            dst.update_tags(
                map_info=str(map_info),
                coordinate_system=str(cords),
                cols=str(cols),
                rows=str(rows),
                pixel_size_x=str(pixel_size_x),
                pixel_size_y=str(pixel_size_y),
                x_origin=str(x_origin),
                y_origin=str(y_origin)
            )
            
            if wavelengths is not None:
                wavelength_str = ','.join(map(str, wavelengths))
                dst.update_tags(
                    wavelength=wavelength_str,
                    WAVELENGTH=wavelength_str,  # Some software looks for uppercase
                    wavelengths=wavelength_str  # Alternative key
                )
        
    except Exception as e:
        raise RuntimeError(f"Error saving image: {str(e)}")