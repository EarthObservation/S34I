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
import rasterio
import h5py
import spectral.io.envi as envi
import spectral as spy
from scipy.ndimage import zoom
from pyproj import Transformer

def get_non_masked_indices(image_array):
    """
    Returns a list of indices (row, col) for pixels that are considered valid.
    A pixel is considered masked (invalid) if:
      - It contains NaN
      - It is equal to -999999 (for all bands, if multi-band)
      - It is equal to -32768 (for EnMap images)
      - It is equal to 0 (for all bands, if multi-band)
      - It is composed of a constant value across all bands
    """
    if image_array.ndim == 2:
        valid = ~(np.isnan(image_array) | 
                 (image_array == -999999) | 
                 (image_array == -32768))
        indices = np.argwhere(valid)
        return [tuple(idx) for idx in indices]
    elif image_array.ndim == 3:
        mask_nan = np.any(np.isnan(image_array), axis=2)
        mask_bad = (image_array == -999999).all(axis=2)
        mask_enmap = (image_array == -32768).all(axis=2)
        mask_zeros = (image_array == 0).all(axis=2)
        
        if image_array.shape[2] > 1:
            mask_constant = (np.ptp(image_array, axis=2) == 0)
        else:
            mask_constant = np.zeros(image_array.shape[:2], dtype=bool)
            mask_constant = ((image_array[:,:,0] == -999999) | 
                           (image_array[:,:,0] == -32768) | 
                           np.isnan(image_array[:,:,0]) | 
                           (image_array[:,:,0] == 0))
            
        valid = ~(mask_nan | mask_bad | mask_enmap | mask_zeros | mask_constant)
        indices = np.argwhere(valid)
        return [tuple(idx) for idx in indices]
    else:
        raise ValueError("Unsupported image array dimensions")

def normal_image_load(path):
    """ 
    Takes input images and returns the non-masked indices and the image array.
    The function supports ENVI and TIFF formats.
    """
    if path is None:
        raise ValueError("Path cannot be None")
        
    if not os.path.exists(path):
        raise FileNotFoundError("File not found")
        
    file_ext = os.path.splitext(path)[1].lower()
    try:
        if file_ext == ".hdr":
            image = envi.open(path).load()
            image_array = np.array(image)
            non_masked_indices = get_non_masked_indices(image_array)
            return non_masked_indices, image_array
        elif file_ext in ('.tif', '.tiff'):
            with rasterio.open(path) as src:
                image = src.read()
                image_array = np.transpose(image, (1, 2, 0))
                non_masked_indices = get_non_masked_indices(image_array)
                return non_masked_indices, image_array
        elif file_ext == '.he5':
            with h5py.File(path, 'r') as f:
                prisma_roots = [
                    '/HDFEOS/SWATHS/PRS_L2D_HCO/',
                    '/HDFEOS/SWATHS/PRS_L2D_PCO/',
                    '/HDFEOS/SWATHS/PRS_L1_STD/',
                    '/HDFEOS/SWATHS/PRS_L2C_PCO/'
                ]
                
                root_path = None
                for path in prisma_roots:
                    if path in f:
                        root_path = path
                        break
                
                if not root_path:
                    raise ValueError("Could not find a valid PRISMA data path")
                
                vnir_path = f"{root_path}Data Fields/VNIR_Cube"
                swir_path = f"{root_path}Data Fields/SWIR_Cube"
                
                if vnir_path not in f or swir_path not in f:
                    raise ValueError(f"VNIR or SWIR cube not found at expected paths: {vnir_path}, {swir_path}")
                
                vnir = f[vnir_path][:]
                swir = f[swir_path][:]
                                             
                vnir_reshaped = np.transpose(vnir, (0, 2, 1))
                swir_reshaped = np.transpose(swir, (0, 2, 1))
                
                if vnir_reshaped.shape[0] != swir_reshaped.shape[0] or vnir_reshaped.shape[1] != swir_reshaped.shape[1]:

                    zoom_factors = (
                        vnir_reshaped.shape[0] / swir_reshaped.shape[0],  # rows
                        vnir_reshaped.shape[1] / swir_reshaped.shape[1],  # cols
                        1  # bands (keep as is)
                    )
                    
                    swir_resampled = zoom(swir_reshaped, zoom_factors, order=0)  
                else:
                    swir_resampled = swir_reshaped
                
                vnir_fill = f[vnir_path].attrs.get('FillValue', -9999)
                swir_fill = f[swir_path].attrs.get('FillValue', -9999)
                
                image_array = np.concatenate((
                    np.where(vnir_reshaped <= vnir_fill, np.nan, vnir_reshaped),
                    np.where(swir_resampled <= swir_fill, np.nan, swir_resampled)
                ), axis=2)
                
                non_masked_indices = get_non_masked_indices(image_array)
                return non_masked_indices, image_array
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        raise RuntimeError(f"Error loading image: {str(e)}")

def get_utm_zone(longitude, latitude):
    """
    Calculate UTM zone from WGS84 coordinates with special cases handling.
    Returns tuple of (zone_number, epsg_code)
    """
    zone_number = int((longitude + 180) / 6) + 1
    
    # Special zones handling
    if 56 <= latitude < 64 and 3 <= longitude < 12:
        zone_number = 32  # Special case for southern Norway
    elif 72 <= latitude < 84:
        if 0 <= longitude < 9:
            zone_number = 31
        elif 9 <= longitude < 21:
            zone_number = 33
        elif 21 <= longitude < 33:
            zone_number = 35
        elif 33 <= longitude < 42:
            zone_number = 37
            
    # Determine if Northern or Southern hemisphere
    epsg = f"326{zone_number:02d}" if latitude >= 0 else f"327{zone_number:02d}"
    return zone_number, f"EPSG:{epsg}"

def transform_prisma_coords(x_origin, y_origin, pixel_size_x, pixel_size_y, rows, cols):
    """Transform PRISMA WGS84 coordinates to appropriate UTM zone"""
    try:
        # Calculate center coordinates
        center_lon = x_origin + (cols/2 * pixel_size_x)
        center_lat = y_origin + (rows/2 * pixel_size_y)
        
        # Get UTM zone and EPSG code
        zone_number, utm_epsg = get_utm_zone(center_lon, center_lat)
        print(f"Calculated UTM zone: {zone_number} ({utm_epsg})")
        
        # Create coordinate transformer
        transformer = Transformer.from_crs("EPSG:4326", utm_epsg, always_xy=True)
        
        # Transform corners
        x_utm, y_utm = transformer.transform(x_origin, y_origin)
        x_end_utm, y_end_utm = transformer.transform(
            x_origin + (cols * pixel_size_x),
            y_origin + (rows * pixel_size_y)
        )
        
        # Calculate pixel sizes in meters
        pixel_size_x_utm = abs((x_end_utm - x_utm) / cols)
        pixel_size_y_utm = abs((y_end_utm - y_utm) / rows)
        
        return {
            'x_origin': x_utm,
            'y_origin': y_utm,
            'pixel_size_x': pixel_size_x_utm,
            'pixel_size_y': pixel_size_y_utm,
            'crs': utm_epsg
        }
    except Exception as e:
        raise ValueError(f"Coordinate transformation failed: {str(e)}")

def metadata_extract(path):
    if path is None:
        raise ValueError("Path cannot be None")
        
    if not os.path.exists(path):
        raise FileNotFoundError("File not found")
        
    file_ext = os.path.splitext(path)[1].lower()
    try:
        if file_ext == ".hdr":
            img = spy.envi.open(path)
            map_info = img.metadata.get('map info', None)  # Spatial info
            cords = img.metadata.get('coordinate system string', None)
            cols = int(img.metadata['samples'])  # Number of columns
            rows = int(img.metadata['lines'])      # Number of rows
            bands = int(img.metadata['bands'])      # Number of bands
            interleave = img.metadata['interleave'] # Interleave format (e.g., 'bip', 'bil', 'bsq')
            wavelengths = img.metadata.get('wavelength', None)  # List of wavelengths (if available)
            
            if map_info and len(map_info) >= 7:
                x_origin = float(map_info[3])
                y_origin = float(map_info[4])
                pixel_size_x = float(map_info[5])  # Pixel width
                pixel_size_y = float(map_info[6])  # Pixel height
            else:
                x_origin = 0
                y_origin = 0
                pixel_size_x = 1
                pixel_size_y = 1
                
            return map_info, cords, cols, rows, bands, interleave, wavelengths, pixel_size_x, pixel_size_y, x_origin, y_origin
        elif file_ext == '.tif' or file_ext == '.tiff':
            with rasterio.open(path) as src:
                cols = src.width
                rows = src.height
                bands = src.count
                transform = src.transform
                
                x_origin = transform[2]  
                y_origin = transform[5]
                pixel_size_x = transform[0]
                pixel_size_y = abs(transform[4])
                cords = src.crs.to_string() if src.crs else None
                    
                tags = src.tags()
                wavelengths = None
                    
                wavelength_tags = ['wavelength', 'WAVELENGTH', 'wavelengths', 'WAVELENGTHS']
                for tag in wavelength_tags:
                    if tag in tags:
                        try:
                            wavelengths = [float(w) for w in tags[tag].split(',')]
                            break
                        except (ValueError, AttributeError):
                            continue
                    
                if not wavelengths:
                    try:
                        band_descs = [src.descriptions[i] for i in range(bands)]
                        if all('nm' in desc.lower() for desc in band_descs):
                            wavelengths = [float(desc.split()[0]) for desc in band_descs]
                    except (AttributeError, ValueError, IndexError):
                        wavelengths = None
                    
                map_info = src.crs.to_dict() if src.crs else None
                interleave = 'bip'
                    
                return map_info, cords, cols, rows, bands, interleave, wavelengths, pixel_size_x, pixel_size_y, x_origin, y_origin
        elif file_ext == '.he5':
            # Improved PRISMA HDF5 format handling
            with h5py.File(path, 'r') as f:
                # Initialize with defaults
                x_origin = y_origin = 0
                pixel_size_x = pixel_size_y = 30  # Default to 30m if no info found
                rows = cols = bands = 0
                wavelengths = None
                map_info = None
                cords = "EPSG:4326"  # Default to WGS84
                interleave = 'bip'
                utm_zone = None
                
                # Try different known paths for PRISMA metadata
                try:
                    # First, find the correct root path for PRISMA data
                    prisma_roots = [
                        '/HDFEOS/SWATHS/PRS_L2D_HCO/',
                        '/HDFEOS/SWATHS/PRS_L2D_PCO/',
                        '/HDFEOS/SWATHS/PRS_L1_STD/',
                        '/HDFEOS/SWATHS/PRS_L2C_PCO/'
                    ]
                    
                    root_path = None
                    for path in prisma_roots:
                        if path in f:
                            root_path = path
                            break
                    
                    if not root_path:
                        # Find any path that might contain PRISMA data
                        for key in f.keys():
                            if 'PRS' in key:
                                root_path = f'/{key}/'
                                break
                    
                    if root_path:
                        print(f"Found PRISMA root path: {root_path}")
                        
                        # Get cube dimensions
                        vnir_paths = [
                            f'{root_path}Data Fields/VNIR_Cube',
                            f'{root_path}Data_Fields/VNIR_Cube',
                            f'{root_path}VNIR_Cube'
                        ]
                        
                        swir_paths = [
                            f'{root_path}Data Fields/SWIR_Cube',
                            f'{root_path}Data_Fields/SWIR_Cube',
                            f'{root_path}SWIR_Cube'
                        ]
                        
                        # Try to find VNIR cube
                        vnir_path = None
                        for path in vnir_paths:
                            if path in f:
                                vnir_path = path
                                break
                                
                        # Try to find SWIR cube
                        swir_path = None
                        for path in swir_paths:
                            if path in f:
                                swir_path = path
                                break
                            
                        bands = 0
                        rows = cols = 0
                        
                        if vnir_path in f and swir_path in f:
                            vnir_shape = f[vnir_path].shape
                            swir_shape = f[swir_path].shape
                            
                            # PRISMA cubes are (rows, bands, cols)
                            bands_vnir = vnir_shape[1]
                            bands_swir = swir_shape[1]
                            bands = bands_vnir + bands_swir
                            
                            # Spatial dimensions from VNIR (assuming same as SWIR after resampling)
                            rows = vnir_shape[0]
                            cols = vnir_shape[2]
                            
                            print(f"PRISMA bands - VNIR: {bands_vnir}, SWIR: {bands_swir}, Total: {bands}")
                            print(f"Spatial dimensions - Rows: {rows}, Cols: {cols}")
                        
                        # Try to get wavelength information
                        wavelength_paths = [
                            f'{root_path}Data Fields/VNIR_Cube_Wavelength',  # New potential path
                            f'{root_path}Data Fields/VNIR_Wavelength',
                            f'{root_path}Data_Fields/VNIR_Wavelength',
                            f'{root_path}VNIR_Wavelength',
                            f'{root_path}Band_Center_Wavelength'  # Alternative naming convention
                        ]
                        
                        for wl_path in wavelength_paths:
                            if wl_path in f:
                                try:
                                    vnir_wavelengths = f[wl_path][:]
                                    
                                    # Try to get SWIR wavelengths too
                                    swir_wl_path = wl_path.replace('VNIR', 'SWIR')
                                    if swir_wl_path in f:
                                        swir_wavelengths = f[swir_wl_path][:]
                                        wavelengths = np.concatenate((vnir_wavelengths, swir_wavelengths)).tolist()
                                    else:
                                        wavelengths = vnir_wavelengths.tolist()
                                    break
                                except Exception as e:
                                    print(f"Error reading wavelengths: {e}")
                        
                        # Try to get geolocation data
                        geo_paths = [
                            f'{root_path}Geolocation Fields/Latitude',
                            f'{root_path}Geolocation_Fields/Latitude',
                            f'{root_path}Latitude'
                        ]
                        
                        for geo_path in geo_paths:
                            if geo_path in f:
                                try:
                                    lat = f[geo_path][:]
                                    lon_path = geo_path.replace('Latitude', 'Longitude')
                                    
                                    if lon_path in f:
                                        lon = f[lon_path][:]
                                        
                                        if lat.size >= 4:  # Use corner points for better geolocation
                                            x_origin = lon[0, 0]
                                            y_origin = lat[0, 0]
                                            x_end = lon[-1, -1]
                                            y_end = lat[-1, -1]
                                            
                                            pixel_size_x = (x_end - x_origin) / (cols - 1)
                                            pixel_size_y = (y_end - y_origin) / (rows - 1)
                                            
                                            break
                                except Exception as e:
                                    print(f"Error reading geolocation: {e}")
                
                    # If we couldn't find structured data, try a more general approach
                    if rows == 0 or cols == 0 or bands == 0:
                        # Look for any 3D datasets that might be the hyperspectral cube
                        cube_datasets = []
                        
                        def find_cubes(name, obj):
                            if isinstance(obj, h5py.Dataset) and len(obj.shape) == 3:
                                cube_datasets.append((name, obj.shape))
                        
                        f.visititems(find_cubes)
                        
                        if cube_datasets:
                            # Sort by total size, largest first
                            cube_datasets.sort(key=lambda x: np.prod(x[1]), reverse=True)
                            
                            # Use the largest cube
                            cube_path, cube_shape = cube_datasets[0]
                            print(f"Using cube from path: {cube_path}, shape: {cube_shape}")
                            
                            # Determine data layout
                            if cube_shape[0] < cube_shape[1] and cube_shape[0] < cube_shape[2]:
                                # Format is (bands, rows, cols)
                                bands = cube_shape[0]
                                rows = cube_shape[1]
                                cols = cube_shape[2]
                            else:
                                # Format is (rows, cols, bands)
                                rows = cube_shape[0]
                                cols = cube_shape[1]
                                bands = cube_shape[2]
                
                except Exception as e:
                    print(f"Error extracting PRISMA metadata: {e}")
                    
                print(f"Extracted metadata - Rows: {rows}, Cols: {cols}, Bands: {bands}")
                print(f"Pixel size - X: {pixel_size_x}, Y: {pixel_size_y}")
                print(f"Origin - X: {x_origin}, Y: {y_origin}")
                print(f"Wavelengths: {wavelengths[:5]}... (truncated)" if wavelengths else "Wavelengths: None")
                
                if cords == "EPSG:4326":  # If we have WGS84 coordinates
                    try:
                        print(f"Converting WGS84 coordinates (lon: {x_origin}, lat: {y_origin})")
                        utm_coords = transform_prisma_coords(
                            x_origin, y_origin,
                            pixel_size_x, pixel_size_y,
                            rows, cols
                        )
                        x_origin = utm_coords['x_origin']
                        y_origin = utm_coords['y_origin']
                        pixel_size_x = utm_coords['pixel_size_x']
                        pixel_size_y = utm_coords['pixel_size_y']
                        cords = utm_coords['crs']
                        print(f"Transformed to {cords}")
                        print(f"New origin (meters) - X: {x_origin:.2f}, Y: {y_origin:.2f}")
                        print(f"New pixel size (meters) - X: {pixel_size_x:.2f}, Y: {pixel_size_y:.2f}")
                    except Exception as e:
                        print(f"Warning: Coordinate transformation failed, using original coordinates: {e}")
                
                return map_info, cords, cols, rows, bands, interleave, wavelengths, pixel_size_x, pixel_size_y, x_origin, y_origin
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        raise RuntimeError(f"Error loading image: {str(e)}")