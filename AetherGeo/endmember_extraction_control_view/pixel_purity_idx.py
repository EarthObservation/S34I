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
from scipy.stats.qmc import Sobol

from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar

from image_manipulation import manipulation

class PixelPurityIdxOperations:
    def __init__(self, parent):
        self.parent = parent
        self.main_window = parent.parent
        self.dialog = None
        self.info_label = None
        self.progress_label = None
        self.results_label = None
        self.progress_bar = None

    def execute(self, path, mask_path, n_projections):
        """Execute point cloud generation with given parameters"""
        try:
            if mask_path is not None:
                input_array = self.main_window.image_data[path]["array"]
                non_masked_indices = self.main_window.image_data[mask_path]["non_masked_indices"]
            else:
                input_array = self.main_window.image_data[path]["array"]
                non_masked_indices = self.main_window.image_data[path]["non_masked_indices"]

            non_masked_pixels = manipulation.apply_mask(input_array, non_masked_indices)
            input_array = np.array([pixels for _, pixels in non_masked_pixels])

            if input_array is not None:
                self.setup_visualization()
                
                pure_pixel_indices = self.Fast_Pixel_Purity_Idx(input_array, n_projections)
                
                PPI_array = np.full(len(input_array), np.nan)
                PPI_array[pure_pixel_indices] = 1
                                
                if "Pixel Purity Index" in self.parent.control_views:
                    control_view = self.parent.control_views["Pixel Purity Index"].widget()
                    control_view.result_data = PPI_array
                else:
                    print("Warning: PCA control view not found to store results.")
            else:
                QMessageBox.warning(self.parent, "Error", "PPI processing failed.")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"PPI processing failed: {str(e)}")
            
    def setup_visualization(self):
        """Setup the visualization window"""
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle("PPI Processing Progress")
        self.dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(self.dialog)
        
        self.info_label = QLabel()
        self.progress_label = QLabel()
        self.results_label = QLabel()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        layout.addWidget(self.info_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.results_label)
        
        self.dialog.show()
        
    def update_progress(self, n_pixels, progress, current_hits):
        """Update progress display"""
        self.info_label.setText(f"Total pixels to process: {n_pixels:,}")
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"Processing: {progress:.1f}%\nCurrent hits found: {current_hits:,}")

    def show_final_results(self, n_pixels, n_candidates, percentage):
        """Show final results"""
        results_text = (
            f"Results:\n"
            f"Total pixels processed: {n_pixels:,}\n"
            f"Pure pixels found: {n_candidates:,}\n"
            f"Selection percentage: {percentage:.2f}%"
        )
        self.progress_label.setText("Processing completed")
        self.results_label.setText(results_text)

    def Slow_Pixel_Purity_Idx(self, input_array, n_projections=2048):
        """
        Args:
            input_array: 2D array of shape [n_pixels, n_components] 
            n_projections: Number of quasi-random projections to generate (power of 2).
        Returns:
            candidates: Indices of pixels exceeding the adaptive threshold.
        """
        # Normalize input array to [0,1] range
        input_array = (input_array - np.min(input_array)) / (np.max(input_array) - np.min(input_array))
        
        n_pixels, n_components = input_array.shape
        
        if n_components < 1:
            raise ValueError("Number of components must be positive")
        
        self.update_progress(n_pixels, 0, 0)
        
        sobol = Sobol(d=n_components, scramble=True)
        projections = sobol.random(n_projections).astype(np.float32)
        projections /= np.linalg.norm(projections, axis=1)[:, np.newaxis]
        
        hit_counts = np.zeros(n_pixels, dtype=np.float32)
        
        # Track which projections each pixel was extreme in (for diversity)
        projection_hits = np.zeros((n_pixels, n_projections), dtype=bool)
        
        batch_size = 128
        for i in range(0, n_projections, batch_size):
            batch_end = min(i + batch_size, n_projections)
            batch_proj = projections[i:batch_end]
            
            projected = np.dot(input_array, batch_proj.T)
            
            for j in range(batch_end - i):
                proj_idx = i + j  
                proj_values = projected[:, j]
                
                # Use dual-level thresholding for better candidate identification
                # Very extreme pixels - high confidence
                top_extreme = np.percentile(proj_values, 99)
                bottom_extreme = np.percentile(proj_values, 1)
                # Moderate extreme pixels - lower confidence
                top_moderate = np.percentile(proj_values, 97)
                bottom_moderate = np.percentile(proj_values, 3)
                
                high_extreme_points = (proj_values >= top_extreme) | (proj_values <= bottom_extreme)
                moderate_extreme_points = (proj_values >= top_moderate) | (proj_values <= bottom_moderate)
                
                # Higher weight to more extreme points
                hit_counts[high_extreme_points] += 1.0
                
                moderate_only = moderate_extreme_points & ~high_extreme_points
                hit_counts[moderate_only] += 0.5
                
                projection_hits[moderate_extreme_points, proj_idx] = True
                
                progress = (batch_end / n_projections) * 100
                self.update_progress(n_pixels, progress, np.count_nonzero(hit_counts > 0))
        
        purity_scores = hit_counts / n_projections 
        
        mean_score = np.mean(purity_scores)
        std_score = np.std(purity_scores)
        strict_threshold = mean_score + 2.0 * std_score

        high_quality_candidates = np.where(purity_scores > strict_threshold)[0]
        
        if len(high_quality_candidates) < 100:
            moderate_threshold = mean_score + 1.5 * std_score
            candidates = np.where(purity_scores > moderate_threshold)[0]
            
            # If still not enough, use percentile
            if len(candidates) < 200:
                fallback_threshold = np.percentile(purity_scores, 97)
                candidates = np.where(purity_scores > fallback_threshold)[0]
                
                # Last resort, use top 5% of scores
                if len(candidates) < 300:
                    candidates = np.where(purity_scores > np.percentile(purity_scores, 95))[0]
        else:
            candidates = high_quality_candidates
        
        original_scores = purity_scores[candidates].copy()
        
        if len(candidates) > 20:
            # Calculate projection signature similarity matrix
            sig_similarity = np.zeros((len(candidates), len(candidates)))
            for k in range(len(candidates)):
                for l in range(k+1, len(candidates)):
                    # Calculate Jaccard similarity between projection signatures
                    a = projection_hits[candidates[k]]
                    b = projection_hits[candidates[l]]
                    intersection = np.sum(a & b)
                    union = np.sum(a | b)
                    if union > 0:
                        sig_similarity[k, l] = intersection / union
                        sig_similarity[l, k] = sig_similarity[k, l]
            
            # Calculate spectral similarity
            spec_similarity = np.zeros((len(candidates), len(candidates)))
            for k in range(len(candidates)):
                for l in range(k+1, len(candidates)):
                    # Use cosine similarity between spectra
                    a = input_array[candidates[k]]
                    b = input_array[candidates[l]]
                    dot_product = np.dot(a, b)
                    norm_a = np.linalg.norm(a)
                    norm_b = np.linalg.norm(b)
                    if norm_a > 0 and norm_b > 0:
                        spec_similarity[k, l] = dot_product / (norm_a * norm_b)
                        spec_similarity[l, k] = spec_similarity[k, l]
            
            # Combine similarities with more weight on spectral difference
            combined_similarity = 0.4 * sig_similarity + 0.6 * spec_similarity
            
            max_candidates = min(500, len(candidates))
            
            num_high_purity = max(10, int(0.1 * max_candidates))
            top_indices = np.argsort(original_scores)[-num_high_purity:]
            selected_indices = list(top_indices)
            
            remaining = list(range(len(candidates)))
            for idx in selected_indices:
                if idx in remaining:
                    remaining.remove(idx)
            
            while len(selected_indices) < max_candidates and remaining:
                best_score = -float('inf')
                best_idx = -1
                
                recent_selected = selected_indices[-15:] if len(selected_indices) > 15 else selected_indices
                
                for idx in remaining:
                    max_sim = max([combined_similarity[idx, sel_idx] for sel_idx in recent_selected])
                    diversity_score = 1.0 - max_sim  # Convert similarity to diversity
                    
                    quality_score = (original_scores[idx] - np.min(original_scores)) / (np.max(original_scores) - np.min(original_scores))
                    
                    combined_score = 0.65 * quality_score + 0.35 * diversity_score
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_idx = idx
                
                if best_idx >= 0:
                    selected_indices.append(best_idx)
                    remaining.remove(best_idx)
                else:
                    break
            
            candidates = candidates[selected_indices]
        
        percentage = (len(candidates)/n_pixels) * 100
        self.show_final_results(n_pixels, len(candidates), percentage)
        
        return candidates
     
    def Fast_Pixel_Purity_Idx(self, input_array, n_projections=2048):
        """
        Args:
            input_array: 2D array of shape [n_pixels, n_components] 
            n_projections: Number of quasi-random projections to generate (power of 2).
        Returns:
            candidates: Indices of pixels exceeding the adaptive threshold.
        """
        # Normalize input array to [0,1] range
        input_array = (input_array - np.min(input_array)) / (np.max(input_array) - np.min(input_array))
        
        n_pixels, n_components = input_array.shape  
        if n_components < 1:
            raise ValueError("Number of components must be positive")

        self.update_progress(n_pixels, 0, 0)

        sobol = Sobol(d=n_components, scramble=True)
        projections = sobol.random(n_projections).astype(np.float32)
        projections /= np.linalg.norm(projections, axis=1)[:, np.newaxis]

        hit_counts = np.zeros(n_pixels, dtype=np.float32)
        
        batch_size = 128
        for i in range(0, n_projections, batch_size):
            batch_end = min(i + batch_size, n_projections)
            batch_proj = projections[i:batch_end]

            projected = np.dot(input_array, batch_proj.T)
            
            for j in range(batch_end - i):
                proj_values = projected[:, j]
                
                top_threshold = np.percentile(proj_values, 99)
                bottom_threshold = np.percentile(proj_values, 1)
                
                extreme_points = (proj_values >= top_threshold) | (proj_values <= bottom_threshold)
                hit_counts[extreme_points] += 1
                
                progress = (batch_end / n_projections) * 100
                self.update_progress(n_pixels, progress, np.count_nonzero(hit_counts))

        # Calculate purity scores
        purity_scores = hit_counts / n_projections  # Normalize by number of projections
        
        # Dinamic thresholding
        mean_score = np.mean(purity_scores)
        std_score = np.std(purity_scores)
        threshold = mean_score + 2 * std_score
        
        candidates = np.where(purity_scores > threshold)[0]
        
        if len(candidates) < 10:
            threshold = np.percentile(purity_scores, 98)
            candidates = np.where(purity_scores > threshold)[0]

        percentage = (len(candidates)/n_pixels) * 100
        self.show_final_results(n_pixels, len(candidates), percentage)

        return candidates