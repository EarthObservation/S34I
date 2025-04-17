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

from sklearn.cluster import OPTICS
from sklearn.neighbors import NearestNeighbors

class AutomaticSelection:
    @staticmethod
    def select_parameters(pure_data):
        """Automatically determine OPTICS parameters based on data characteristics.
        
        Parameters:
            pure_data: numpy.ndarray
                Input data matrix of shape (n_samples, n_features)
                
        Returns:
            dict: Dictionary containing optimized OPTICS parameters
        """
        n_samples, n_features = pure_data.shape
        
        k = min(n_samples - 1, 10)  
        nbrs = NearestNeighbors(n_neighbors=k).fit(pure_data)
        distances, _ = nbrs.kneighbors(pure_data)
        avg_distance = np.mean(distances[:, 1:])  # Exclude self-distance
        
        min_samples = max(
            5,  # Absolute minimum
            2 * n_features,  # Scale with dimensionality
            int(np.sqrt(n_samples) * 0.1)  # Scale with dataset size
        )
        
        # Lower xi for sparse data, higher for dense data
        xi = min(0.1, max(0.01, avg_distance / np.std(distances[:, 1:])))
        
        if n_samples < 100:
            min_cluster_size = 0.1  # 10% for small datasets
        elif n_samples < 1000:
            min_cluster_size = 0.05  # 5% for medium datasets
        else:
            min_cluster_size = 0.02  # 2% for large datasets
            
        params = {
            'min_samples': min_samples,
            'xi': xi,
            'min_cluster_size': min_cluster_size
        }
        
        return params
        
    @staticmethod
    def run_optics_clustering(cloud_points, min_samples, xi, min_cluster_size):
        model = OPTICS(
            min_samples=min_samples,
            xi=xi,
            min_cluster_size=min_cluster_size,
            cluster_method='xi'
        )
        model.fit(cloud_points)
        labels = model.labels_

        return labels