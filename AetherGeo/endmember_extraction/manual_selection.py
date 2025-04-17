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

from matplotlib.path import Path
from mpl_toolkits.mplot3d import proj3d
from collections import deque

class ManualSelection:
    """
    Encapsulates manual selection features such as lasso selection,
    freezing the view, and endmember tracking.
    """
    def __init__(self, figure, canvas, scatter, embedding, original_colors, text_display, labels=None):
        self.figure = figure
        self.canvas = canvas
        self.scatter = scatter
        self.embedding = embedding
        self.original_colors = original_colors.copy()
        self.text_display = text_display
        self.labels = labels
        self.view_frozen = False
        self.lasso_enabled = False
        self.current_path = []
        self.selected_indices = []
        self.original_view = None
        self.lasso_preview_line = None
        self._rotate_cid = None

        self.endmembers = {}  # {id: {"name": str, "indices": list, "color": list}}
        self.endmember_counter = 0
        self.endmember_colors = [
            [1, 0, 0, 1],     # Red
            [0, 0, 1, 1],     # Blue
            [0, 1, 0, 1],     # Green
            [1, 1, 0, 1],     # Yellow
            [1, 0, 1, 1],     # Magenta
            [0, 1, 1, 1],     # Cyan
            [0.5, 0.5, 0.5, 1],  # Gray
            [1, 0.5, 0, 1],   # Orange
            [0.5, 0, 0.5, 1]  # Purple
        ]
        self.available_colors = deque(self.endmember_colors.copy())

    def toggle_freeze(self):
        """Toggle freezing of the view to prevent rotation, pan, and zoom."""
        ax = self.figure.axes[0]
        if not self.view_frozen:
            self.original_view = {
                'elev': ax.elev,
                'azim': ax.azim,
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim(),
                'zlim': ax.get_zlim(),
                'dist': ax._dist  # Camera distance
            }
            self._rotate_cid = self.canvas.mpl_connect('motion_notify_event', self.prevent_rotation)
        else:
            if self._rotate_cid:
                self.canvas.mpl_disconnect(self._rotate_cid)
                self._rotate_cid = None
        self.view_frozen = not self.view_frozen
        self.canvas.draw_idle()

    def prevent_rotation(self, event):
        """Restore the original view parameters if any interaction occurs."""
        if self.view_frozen and self.original_view:
            ax = self.figure.axes[0]
            
            ax.view_init(elev=self.original_view['elev'], azim=self.original_view['azim'])
            ax.set_xlim(self.original_view['xlim'])
            ax.set_ylim(self.original_view['ylim'])
            ax.set_zlim(self.original_view['zlim'])
            ax.dist = self.original_view['dist']
            self.canvas.draw_idle()
            return True
        return False

    def toggle_lasso(self):
        """Toggle lasso selection mode."""
        self.lasso_enabled = not self.lasso_enabled
        if self.lasso_enabled:
            self.current_path = []
        else:
            self.clear_lasso_preview()

    def clear_lasso_preview(self):
        """Remove the temporary lasso path preview."""
        ax = self.figure.axes[0]
        if self.lasso_preview_line:
            try:
                self.lasso_preview_line.remove()
            except Exception:
                for line in ax.get_lines():
                    if line.get_color() == 'red':
                        line.remove()
            self.lasso_preview_line = None
            self.canvas.draw_idle()

    def on_mouse_press(self, event):
        """Start lasso selection on left-click when frozen and enabled."""
        if event.inaxes != self.figure.axes[0]:
            return
        if event.button == 1 and self.view_frozen and self.lasso_enabled:
            self.current_path = [(event.xdata, event.ydata)]
            self.draw_lasso_preview()
        return self.view_frozen

    def on_mouse_move(self, event):
        """Handle mouse movement for lasso drawing and enforce frozen view."""
        if self.view_frozen and event.button == 1:
            if self.original_view:
                ax = self.figure.axes[0]
                ax.view_init(elev=self.original_view['elev'], azim=self.original_view['azim'])
                self.canvas.draw_idle()
            if self.lasso_enabled and self.current_path:
                self.current_path.append((event.xdata, event.ydata))
                self.draw_lasso_preview()
            return True
        return False

    def on_mouse_release(self, event):
        """Finalize the lasso selection and process selected points."""
        if event.inaxes != self.figure.axes[0]:
            return
        if self.view_frozen and self.lasso_enabled and len(self.current_path) > 2 and event.button == 1:
            path = Path(self.current_path)
            self.process_lasso_selection(path)
        self.current_path = []
        self.clear_lasso_preview()
        return self.view_frozen

    def draw_lasso_preview(self):
        """Draw a temporary red line to preview the lasso selection."""
        ax = self.figure.axes[0]
        self.clear_lasso_preview()
        if len(self.current_path) > 1:
            x_coords, y_coords = zip(*self.current_path)
            self.lasso_preview_line = ax.plot(x_coords, y_coords, color='red', lw=1)[0]
            self.canvas.draw_idle()

    def all_selected_indices(self):
        """Return a set of indices already selected in any endmember."""
        selected = set()
        for em_data in self.endmembers.values():
            selected.update(em_data['indices'])
        return selected

    def process_lasso_selection(self, path):
        """Determine which points fall inside the lasso path and update endmembers."""
        ax = self.figure.axes[0]
        selected_indices = []
        
        for i, point in enumerate(self.embedding):
            x, y, _ = proj3d.proj_transform(*point, ax.get_proj())
            if path.contains_point((x, y)):
                selected_indices.append(i)
                
        if not selected_indices:
            return

        colors = self.original_colors.copy()
        
        self.endmember_counter += 1
        endmember_id = self.endmember_counter
        endmember_name = f"Endmember {endmember_id}"
        
        if not self.available_colors:
            self.available_colors = deque(self.endmember_colors.copy())
        endmember_color = self.available_colors.popleft()
        
        self.endmembers[endmember_id] = {
            "name": endmember_name,
            "indices": selected_indices,
            "color": endmember_color
        }
        
        for idx in selected_indices:
            colors[idx] = endmember_color
            
        self.scatter.set_facecolors(colors)
        self.update_endmember_display()

    def reset_endmembers(self):
        """Clear all selections and restore original colors."""
        self.endmembers = {}
        self.endmember_counter = 0
        self.available_colors = deque(self.endmember_colors.copy())
        
        gray_colors = np.tile([0.7, 0.7, 0.7, 0.6], (len(self.embedding), 1))
        self.scatter.set_facecolors(gray_colors)
        self.text_display.clear()
        self.canvas.draw_idle()

    def clear_last_endmember(self):
        """Remove the most recently added endmember and update colors."""
        if not self.endmembers:
            return
            
        last_id = max(self.endmembers.keys())
        last_em = self.endmembers.pop(last_id)
        self.available_colors.appendleft(last_em["color"])
        
        colors = self.original_colors.copy()
        
        if self.endmembers:
            new_last_id = max(self.endmembers.keys())
            new_last_em = self.endmembers[new_last_id]
            for idx in new_last_em["indices"]:
                colors[idx] = new_last_em["color"]
                
        self.scatter.set_facecolors(colors)
        self.update_endmember_display()

    def update_endmember_display(self):
        """Update the text display with current endmember selections."""
        text = "Endmembers:\n"
        for em_id, em_data in sorted(self.endmembers.items()):
            text += f"{em_data['name']}: {len(em_data['indices'])} pixels\n"
        self.text_display.setText(text)
        self.canvas.draw_idle()
