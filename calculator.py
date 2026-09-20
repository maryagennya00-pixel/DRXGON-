"""
simple_renderer.py

A minimal 3‑D rendering helper that draws a mesh defined by vertices
and triangular faces using matplotlib's mplot3d toolkit.

Features
--------
* Encapsulated in the `MeshRenderer` class.
* Accepts NumPy arrays for vertices (N×3) and faces (M×3).
* Provides a `render` method that opens an interactive window.
* Includes a usage example that draws a colored cube.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class MeshRenderer:
    """
    Render a triangular mesh in a 3‑D matplotlib figure.

    Parameters
    ----------
    vertices : np.ndarray
        Array of shape (N, 3) containing the XYZ coordinates of each vertex.
    faces : np.ndarray
        Array of shape (M, 3) containing indices into `vertices` that form
        each triangular face. Indices are zero‑based.
    face_colors : sequence, optional
        Sequence of colors (e.g., ``['red', 'green', ...]``) matching the
        number of faces. If omitted, a default colormap is applied.
    """

    def __init__(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        face_colors: list | None = None,
    ) -> None:
        self._validate_input(vertices, faces)
        self.vertices = vertices
        self.faces = faces
        self.face_colors = face_colors

    @staticmethod
    def _validate_input(vertices: np.ndarray, faces: np.ndarray) -> None:
        """Raise informative errors if inputs are malformed."""
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError("`vertices` must be a 2‑D array with shape (N, 3).")
        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError("`faces` must be a 2‑D array with shape (M, 3).")
        if not np.issubdtype(faces.dtype, np.integer):
            raise TypeError("`faces` must contain integer indices.")
        if np.any(faces < 0) or np.any(faces >= len(vertices)):
            raise IndexError("Face indices are out of bounds for the vertex array.")

    def _build_face_collection(self) -> Poly3DCollection:
        """Create a Poly3DCollection from the mesh data."""
        # Extract the XYZ coordinates for each face
        face_vertices = self.vertices[self.faces]
        collection = Poly3DCollection(face_vertices, linewidths=0.5, edgecolor="k")

        if self.face_colors:
            if len(self.face_colors) != len(self.faces):
                raise ValueError("Length of `face_colors` must match number of faces.")
            collection.set_facecolor(self.face_colors)
        else:
            # Default colormap based on face index
            cmap = plt.get_cmap("viridis")
            colors = cmap(np.linspace(0, 1, len(self.faces)))
            collection.set_facecolor(colors)

        return collection

    def render(self, title: str = "3‑D Mesh") -> None:
        """
        Display the mesh in an interactive 3‑D plot.

        Parameters
        ----------
        title : str, optional
            Window title.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.set_title(title)

        collection = self._build_face_collection()
        ax.add_collection3d(collection)

        # Auto‑scale axes to the mesh extents
        scale = self.vertices.flatten()
        ax.auto_scale_xyz(scale, scale, scale)

        # Enable equal aspect ratio for all axes
        ax.set_box_aspect([1, 1, 1])

        plt.show()


def _example_cube() -> None:
    """Create and render a simple colored cube."""
    # Define 8 cube vertices
    v = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 1],
        ],
        dtype=float,
    )

    # Define 12 triangular faces (two per cube side)
    f = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],  # bottom
            [4, 5, 6],
            [4, 6, 7],  # top
            [0, 1, 5],
            [0, 5, 4],  # front
            [1, 2, 6],
            [1, 6, 5],  # right
            [2, 3, 7],
            [2, 7, 6],  # back
            [3, 0, 4],
            [3, 4, 7],  # left
        ],
        dtype=int,
    )

    # Optional per‑face colors
    colors = [
        "lightcoral",
        "lightcoral",
        "lightgreen",
        "lightgreen",
        "lightskyblue",
        "lightskyblue",
        "khaki",
        "khaki",
        "plum",
        "plum",
        "orange",
        "orange",
    ]

    renderer = MeshRenderer(vertices=v, faces=f, face_colors=colors)
    renderer.render(title="Colored Cube Example")


if __name__ == "__main__":
    _example_cube()