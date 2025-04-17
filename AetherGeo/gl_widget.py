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
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPoint, QPointF
from OpenGL import GL
from skimage.transform import resize

class ImageGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.texture_id = None
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.last_pos = QPoint()
        self.image_size = (0, 0)
        self.init_zoom = True
        self.max_tex_size = 4096
        self.full_image = None
        self.current_tile = None
        self.image_aspect = 1.0
        self.widget_aspect = 1.0
        self.true_image_size = (0, 0)
        self.non_masked = None
        self.setMouseTracking(True)
        self.last_mouse_pos = QPointF()
        self.original_width = 0  
        self.original_height = 0
        self.saturation = 1.5
        self.gamma = 0.7

    def initializeGL(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        self.max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
        #print(f"Max texture size supported: {self.max_tex_size}")

    def setImageData(self, data):
        """
        If data is a tuple (non_masked_indices, image_array),
        store the mask and use the array for further processing.
        """
        if data is None or not isinstance(data, (tuple, np.ndarray)):
            return

        self.original_width = 0
        self.original_height = 0

        if isinstance(data, tuple) and len(data) == 2:
            self.non_masked = data[0]
            original_data = data[1]
            if isinstance(original_data, np.ndarray) and original_data.ndim >= 2:
                self.original_height, self.original_width = original_data.shape[:2]
            data = original_data
        else:
            self.non_masked = None
            if isinstance(data, np.ndarray) and data.ndim >= 2:
                self.original_height, self.original_width = data.shape[:2]

        if not isinstance(data, np.ndarray) or data.ndim != 3:
            return

        h, w = data.shape[:2]
        # Ensure new dimensions are at least 1x1 to prevent division by zero later
        if w > self.max_tex_size or h > self.max_tex_size:
            scale = min(self.max_tex_size / max(w, 1), self.max_tex_size / max(h, 1))
            new_w = max(1, int(w * scale)) 
            new_h = max(1, int(h * scale))
            data = resize(data, (new_h, new_w, data.shape[2]),
                          preserve_range=True, anti_aliasing=True)

        #print(f"Processed shape: {data.shape}")
        self.full_image = data
        self.current_tile = self.get_visible_tile()
        self.update_texture(self.current_tile)

        self.true_image_size = (data.shape[1], data.shape[0])
        self.image_aspect = self.true_image_size[0] / self.true_image_size[1]
        if self.current_tile is not None:
            self.scale_factor = (
                self.true_image_size[0] / max(self.current_tile.shape[1], 1),
                self.true_image_size[1] / max(self.current_tile.shape[0], 1)
            )
        else:
            self.scale_factor = (1.0, 1.0)
        
    def get_visible_tile(self):
        if self.full_image is None:
            return None
        h, w = self.full_image.shape[:2]
        
        if w <= self.max_tex_size and h <= self.max_tex_size:
            return self.full_image
        
        scale = min(self.max_tex_size / w, self.max_tex_size / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        from skimage.transform import resize
        tile = resize(self.full_image, (new_h, new_w, self.full_image.shape[2]),
                    preserve_range=True, anti_aliasing=True)
        return tile.astype(self.full_image.dtype)

    def update_texture(self, data):
        if data is None or data.size == 0:
            return

        try:
            # Detect single-band mask (0s and 1s)
            is_single_band_mask = False
            if data.shape[2] == 1:
                unique_vals = np.unique(data[~np.isnan(data)])
                if set(unique_vals).issubset({0, 1}):
                    is_single_band_mask = True

            if is_single_band_mask:
                if data.shape[2] < 3:
                    rgb_data = np.concatenate([data] * 3, axis=2)[:, :, :3]
                else:
                    rgb_data = data[:, :, :3].copy()

                valid_mask = ~np.isnan(rgb_data)
                if np.any(valid_mask):
                    rgb_min = np.nanmin(rgb_data)
                    rgb_max = np.nanmax(rgb_data)
                    if rgb_max > rgb_min:
                        rgb_data = ((rgb_data - rgb_min) / (rgb_max - rgb_min) * 255).astype(np.uint8)
                    else:
                        rgb_data = np.zeros_like(rgb_data, dtype=np.uint8)
                else:
                    rgb_data = np.zeros_like(rgb_data, dtype=np.uint8)

                texture_filter = GL.GL_NEAREST

            else:
                if data.shape[2] < 3:
                    rgb_data = np.concatenate([data] * 3, axis=2)[:, :, :3]
                else:
                    rgb_data = data[:, :, :3].copy()

                if rgb_data.shape[0] > self.max_tex_size or rgb_data.shape[1] > self.max_tex_size:
                    from skimage.transform import resize
                    rgb_data = resize(rgb_data, (self.max_tex_size, self.max_tex_size, 3),
                                    preserve_range=True, anti_aliasing=True)

                valid_mask = ~np.isnan(rgb_data)
                if np.any(valid_mask):
                    processed = np.zeros_like(rgb_data, dtype=np.float32)
                    
                    for i in range(3):
                        channel = rgb_data[:, :, i].astype(np.float32)
                        valid_channel = channel[valid_mask[:, :, i]]
                        
                        p_low, p_high = np.nanpercentile(valid_channel, [2, 98])
                        if p_high <= p_low:
                            p_low, p_high = np.nanmin(valid_channel), np.nanmax(valid_channel)
                        
                        channel_norm = np.clip((channel - p_low) / (p_high - p_low), 0, 1)
                        
                        gamma = self.gamma
                        channel_norm = np.power(channel_norm, gamma)
                        
                        processed[:, :, i] = channel_norm

                    saturation = self.saturation
                    gray = np.mean(processed, axis=2, keepdims=True)
                    processed = gray + (processed - gray) * saturation
                    processed = np.clip(processed, 0, 1)
                    
                    rgb_data = (processed * 255).astype(np.uint8)
                else:
                    rgb_data = np.zeros_like(rgb_data, dtype=np.uint8)

                texture_filter = GL.GL_LINEAR

            if self.non_masked is not None and self.original_width > 0 and self.original_height > 0:
                h_tile, w_tile = data.shape[:2]

                scale_x = w_tile / self.original_width
                scale_y = h_tile / self.original_height

                valid = np.zeros((h_tile, w_tile), dtype=bool)
                non_masked_arr = np.array(self.non_masked)
                if non_masked_arr.size > 0:
                    r_indices = np.clip((non_masked_arr[:, 0] * scale_y).astype(int), 0, h_tile - 1)
                    c_indices = np.clip((non_masked_arr[:, 1] * scale_x).astype(int), 0, w_tile - 1)
                    valid[r_indices, c_indices] = True

                #non-valid pixels to black
                masked_color = np.array([0, 0, 0], dtype=rgb_data.dtype)
                rgb_data[~valid] = masked_color
            
            rgb_data = np.ascontiguousarray(np.flipud(rgb_data))
            self.image_size = (rgb_data.shape[1], rgb_data.shape[0])

            if self.texture_id is not None:
                GL.glDeleteTextures([self.texture_id])
            self.texture_id = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
            
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, texture_filter)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, texture_filter)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB,
                            self.image_size[0], self.image_size[1], 0,
                            GL.GL_RGB, GL.GL_UNSIGNED_BYTE, rgb_data)
        except Exception as e:
            #print(f"Texture processing error: {str(e)}")
            self.texture_id = None
        finally:
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self.init_zoom = True
        self.update()

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        
        if self.texture_id is None or self.image_size[0] <= 0 or self.image_size[1] <= 0:
            return

        widget_width = self.width()
        widget_height = self.height()
        image_width, image_height = self.image_size

        if self.init_zoom:
            self.zoom = min(widget_width/image_width, widget_height/image_height) 
            self.pan = QPointF(0, 0)
            self.init_zoom = False

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        
        visible_width = widget_width / self.zoom
        visible_height = widget_height / self.zoom
        
        left = self.pan.x()
        right = left + visible_width
        bottom = self.pan.y() + visible_height
        top = self.pan.y()

        GL.glOrtho(left, right, bottom, top, -1, 1)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0, 1)  
        GL.glVertex2f(0, 0)
        GL.glTexCoord2f(1, 1)  
        GL.glVertex2f(image_width, 0)
        GL.glTexCoord2f(1, 0)  
        GL.glVertex2f(image_width, image_height)
        GL.glTexCoord2f(0, 0)  
        GL.glVertex2f(0, image_height)
        GL.glEnd()
        
    def update_tile(self):
        if self.full_image is None:
            return
        
        x_start = int(max(0, -self.pan.x() / self.zoom))
        y_start = int(max(0, -self.pan.y() / self.zoom))
        tile_size = min(self.max_tex_size, self.full_image.shape[1], self.full_image.shape[0])
        
        tile = self.full_image[
            y_start:y_start + tile_size,
            x_start:x_start + tile_size,
            :
        ]
        self.update_texture(tile)

    def wheelEvent(self, event):
        old_zoom = self.zoom
        self.zoom *= 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom = np.clip(self.zoom, 0.1, 100.0)
        
        mouse_pos = event.position()
        self.pan += QPointF(
            (mouse_pos.x()/old_zoom - mouse_pos.x()/self.zoom),
            (mouse_pos.y()/old_zoom - mouse_pos.y()/self.zoom)
        )
        self.update()

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.position() - self.last_mouse_pos
            self.pan += QPointF(-delta.x() / self.zoom, -delta.y() / self.zoom)
            self.update()
        self.last_mouse_pos = event.position()