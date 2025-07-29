from milcatrusspy.node import Node
import numpy as np

class TrussElement:
    def __init__(self, tag: int, node_i: Node, node_j: Node, E: float, A: float) -> None:
        self.tag = tag
        self.node_i = node_i
        self.node_j = node_j
        self.E = E
        self.A = A
        self.dofs = np.concatenate((node_i.dofs, node_j.dofs))
        self.length = np.linalg.norm(self.node_j.coords - self.node_i.coords)

        self.Tlg = self.transform_matrix()

        self.kl = self.E*self.A/self.length*np.array([[1, -1], [-1, 1]])

        self.Ki = self.Tlg.T @ self.kl @ self.Tlg

        self.forces = None
        self.displacements = None

    def transform_matrix(self) -> np.ndarray:
        if self.node_i.ndm == 3:
            L = self.length
            cx = (self.node_j.x - self.node_i.x) / L
            cy = (self.node_j.y - self.node_i.y) / L
            cz = (self.node_j.z - self.node_i.z) / L
            T = np.array([
                [cx, cy, cz, 0, 0, 0],
                [0, 0, 0, cx, cy, cz],
            ])
            return T
        if self.node_i.ndm == 2:
            L = self.length
            cx = (self.node_j.x - self.node_i.x) / L
            cy = (self.node_j.y - self.node_i.y) / L
            T = np.array([
                [cx, cy, 0, 0],
                [0, 0, cx, cy],
            ])
            return T

    def get_global_stiffness_matrix(self) -> np.ndarray:
        return self.Ki