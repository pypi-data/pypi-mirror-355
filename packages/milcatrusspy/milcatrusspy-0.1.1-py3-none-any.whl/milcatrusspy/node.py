import numpy as np

class Node:
    _ID = 1
    def __init__(self, tag: int, x: float, y: float, z: float, ndm: int = 3) -> None:
        self.id = Node._ID
        Node._ID += 1
        self.ndm = ndm
        self.tag = tag
        self.x = x
        self.y = y
        self.z = z
        self.coords = np.array([x, y, z])[:ndm]
        self.forces = np.array([0, 0, 0])[:ndm]
        self.displacements = np.array([0, 0, 0])[:ndm]
        self.reactions = np.array([0, 0, 0])[:ndm]
        self.restraints = (False, False, False)[:ndm]
        self.dofs = np.array([
            self.id*ndm-2,
            self.id*ndm-1,
            self.id*ndm
        ]) if ndm == 3 else np.array([
            self.id*ndm-1,
            self.id*ndm,
        ])

    def set_load(self, fx: float, fy: float, fz: float) -> None:
        self.forces = np.array([fx, fy, fz])[:self.ndm]

    def set_restraints(self, ux: bool, uy: bool, uz: bool) -> None:
        self.restraints = (ux, uy, uz)[:self.ndm]

    def get_load_vector(self) -> np.ndarray:
        return self.forces