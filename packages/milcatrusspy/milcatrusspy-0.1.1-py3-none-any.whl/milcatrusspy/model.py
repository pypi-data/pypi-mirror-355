
import matplotlib.pyplot as plt
import pandas as pd
from milcatrusspy.node import Node
from milcatrusspy.truss_element import TrussElement
from milcatrusspy.analasis import LinearStaticAnalysis
import numpy as np

class Model:
    def __init__(self, ndm: int = 3) -> None:
        self.ndm: int = ndm
        self.nodes: dict[int, Node] = {}
        self.elements: dict[int, TrussElement] = {}

    def add_node(self, tag: int, x: float, y: float, z: float = 0) -> Node:
        self.nodes[tag] = Node(tag, x, y, z, ndm=self.ndm)
        return self.nodes[tag]

    def add_element(self, tag: int, tag_node_i: int, tag_node_j: int, E: float, A: float) -> TrussElement:
        self.elements[tag] = TrussElement(
            tag, self.nodes[tag_node_i], self.nodes[tag_node_j], E, A)
        return self.elements[tag]

    def set_load(self, tag_node: int, fx: float = 0, fy: float = 0, fz: float = 0) -> None:
        self.nodes[tag_node].set_load(fx, fy, fz)

    def set_restraints(self, tag_node: int, ux: bool, uy: bool, uz: bool = False) -> None:
        self.nodes[tag_node].set_restraints(ux, uy, uz)

    def solve(self) -> tuple[np.ndarray, np.ndarray]:
        analysis = LinearStaticAnalysis(self)
        displacements, reactions = analysis.solve()
        # Asignar los desplazamientos y reacciones a los nodos
        for node in self.nodes.values():
            node.displacements = displacements[node.dofs - 1]
            node.reactions = reactions[node.dofs - 1]

        for element in self.elements.values():
            element.displacements = element.Tlg @ displacements[element.dofs - 1]
            element.forces = element.kl @ element.displacements
        return displacements, reactions

    def print_results(self) -> None:
        df1, df2 = self.get_results()

        print("\n")
        print("Resultados")
        print("\n")
        print("Resultados de los Nodos")
        print(df1)
        print("\n")
        print("Resultados de los Elementos")
        print(df2)
        print("\n")

    def get_results(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        data_node = {}
        for i in self.nodes.values():
            data_node[f"Node {i.tag}"] = np.concatenate((i.displacements, i.reactions))
        if self.ndm == 2:
            df1 = pd.DataFrame(data_node, index=['UX', 'UY', 'RX', 'RY'])
        else:
            df1 = pd.DataFrame(data_node, index=['UX', 'UY', 'UZ', 'RX', 'RY', 'RZ'])
        data_ele = {}
        for i in self.elements.values():
            estado = "Traccion" if i.forces[1] > 0 else "Compresion"
            data_ele[f"Element {i.tag}"] = np.concatenate(
                (i.displacements.round(6), i.forces.round(2), [estado], [i.length.round(2)]))
        df2 = pd.DataFrame(
            data_ele, index=['U1', 'U2', 'F1', 'F2', 'Estado', 'Longitud'])
        return df1, df2

    def plot_model(self, labels: bool = True) -> None:
        if self.ndm == 3:
            plt.close()
            self.figure = plt.figure(figsize=(10, 8))
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.set_title("Modelo", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if labels:
                    self.ax.text(node.coords[0], node.coords[1], node.coords[2], str(
                        node.tag), color="#ff0000")
                self.ax.scatter(node.coords[0], node.coords[1], node.coords[2], marker='o', s=20, c='#0000FF')
                if node.restraints != (False, False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], node.coords[2], marker='^', s=100, c='#762e99')
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                z = [element.node_i.coords[2], element.node_j.coords[2]]
                self.ax.plot(x, y, z, c='b')
                if labels:
                    self.ax.text((x[0]+x[1])/2, (y[0]+y[1])/2, (z[0]+z[1])/2,
                                 str(element.tag), color="#7e2fa1" )#, fontproperties="italic")
            self.__plot_ajuste_3d()
            plt.show()
        else:
            plt.close()
            self.figure, self.ax = plt.subplots(figsize=(10, 8))
            self.ax.set_title("Modelo", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if labels:
                    self.ax.text(node.coords[0], node.coords[1], str(
                        node.tag), color="#ff0000", zorder = 18)
                self.ax.scatter(node.coords[0], node.coords[1], marker='o', s=20, c='#0000FF', zorder = 4)
                if node.restraints != (False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], marker='^', s=150, c='#762e99', zorder = 14)
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                self.ax.plot(x, y, c='b')
                self.ax.text((x[0]+x[1])/2, (y[0]+y[1])/2, str(element.tag), fontproperties="italic",
                             color="#0000ff", horizontalalignment="right", verticalalignment="bottom")
            self.__plot_ajuste_2d()
            plt.show()

    def plot_deformed(self, scale: float = 1, labels: bool = True) -> None:
        if self.ndm == 3:
            plt.close()
            self.figure = plt.figure(figsize=(10, 8))
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.set_title("Modelo deformado", fontsize=16, fontweight="bold", color="#0000FF")
            for node in self.nodes.values():
                if node.restraints != (False, False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], node.coords[2], marker='^', s=50, c='#762e99')
                if labels:
                    x = node.coords[0] + node.displacements[0]*scale
                    y = node.coords[1] + node.displacements[1]*scale
                    z = node.coords[2] + node.displacements[2]*scale
                    self.ax.text(
                        x, y, z, f"UX: {node.displacements[0]:.6f}\nUY: {node.displacements[1]:.6f}\nUZ: {node.displacements[2]:.6f}", fontsize=6)
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                z = [element.node_i.coords[2], element.node_j.coords[2]]
                self.ax.plot(x, y, z, c='#762e99', linestyle=':')
                x = [element.node_i.coords[0] + element.node_i.displacements[0]*scale,
                     element.node_j.coords[0] + element.node_j.displacements[0]*scale]
                y = [element.node_i.coords[1] + element.node_i.displacements[1]*scale,
                     element.node_j.coords[1] + element.node_j.displacements[1]*scale]
                z = [element.node_i.coords[2] + element.node_i.displacements[2]*scale,
                     element.node_j.coords[2] + element.node_j.displacements[2]*scale]
                self.ax.plot(x, y, z, c='#0000FF')
            self.__plot_ajuste_3d()
            plt.show()

        else:
            plt.close()
            self.figure, self.ax = plt.subplots(figsize=(10, 8))
            self.ax.set_title("Modelo deformado", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if labels:
                    x = node.coords[0] + node.displacements[0]*scale
                    y = node.coords[1] + node.displacements[1]*scale
                    text = f"UX: {node.displacements[0]:.6f}\nUY: {node.displacements[1]:.6f}"
                    self.ax.text(x, y, text, color="#000000", fontsize=8)
                if node.restraints != (False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], marker='^', s=50, c='#762e99')
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                self.ax.plot(x, y, c='#762e99', linestyle=':')
                x = [element.node_i.coords[0] + element.node_i.displacements[0]*scale,
                     element.node_j.coords[0] + element.node_j.displacements[0]*scale]
                y = [element.node_i.coords[1] + element.node_i.displacements[1]*scale,
                     element.node_j.coords[1] + element.node_j.displacements[1]*scale]
                self.ax.plot(x, y, c='#0000FF')
            self.__plot_ajuste_2d()
            plt.show()

    def plot_axial_forces(self, scale: float = 1, labels: bool = True) -> None:
        if self.ndm == 3:
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            plt.close()
            self.figure = plt.figure(figsize=(10, 8))
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.set_title("Diagrama de Fuerzas Axiales", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if node.restraints != (False, False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], node.coords[2], marker='^', s=50, c='#762e99')
            for element in self.elements.values():
                if element.forces[0].round(6) == 0 and element.forces[1].round(6) == 0:
                    pass
                else:
                    a = element.node_i.coords
                    b = element.node_j.coords
                    f2 = element.forces[1]
                    f1 = np.sign(f2)*abs(element.forces[0])
                    forcetype = "Traccion" if f2 > 0 else "Compresion"
                    vect = b - a
                    x_axis = vect / np.linalg.norm(vect)
                    if a[0] == b[0] and a[1] == b[1]:
                        vec_xz = np.array([1, 0, 0])
                    else:
                        vec_xz = np.array([0, 0, 1])
                    vec_xz = vec_xz / np.linalg.norm(vec_xz)
                    z_axis = np.cross(x_axis, vec_xz)
                    z_axis = z_axis / np.linalg.norm(z_axis)
                    y_axis = np.cross(z_axis, x_axis)
                    y_axis = y_axis / np.linalg.norm(y_axis)
                    c = y_axis * scale*f1 + a
                    d = y_axis * scale*f2 + b
                    vertices = [[a, b, d, c]]
                    if forcetype == "Traccion":
                        self.ax.add_collection3d(Poly3DCollection(
                            vertices, alpha=0.9, facecolor='#7f7fff', zorder=4))
                        plt.plot([a[0], c[0], d[0], b[0]], [a[1], c[1], d[1], b[1]], [
                                 a[2], c[2], d[2], b[2]], c='b', alpha=1, zorder=4)
                    else:
                        self.ax.add_collection3d(Poly3DCollection(
                            vertices, alpha=0.9, facecolor='#ff7f7f', zorder=5))
                        plt.plot([a[0], c[0], d[0], b[0]], [a[1], c[1], d[1], b[1]], [
                                 a[2], c[2], d[2], b[2]], c='r', alpha=1, zorder=5)
                    if labels:
                        if abs(element.forces[0]) > 1e-6 or abs(element.forces[1]) > 1e-6:
                            sim = "T" if forcetype == "Traccion" else "C"
                            self.ax.text((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2,
                                         f"{sim}= {abs(f1):.2f}", fontsize=8, color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
                        else:
                            self.ax.text((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2, f"F1= {element.forces[0]:.2f}\nF2= {element.forces[1]:.2f}",
                                         fontsize=8, color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                z = [element.node_i.coords[2], element.node_j.coords[2]]
                self.ax.plot(x, y, z, c='b', zorder=16)
            self.__plot_ajuste_3d()
            plt.show()
        else:
            plt.close()
            self.figure, self.ax = plt.subplots(figsize=(10, 8))
            self.ax.set_title("Diagrama de Fuerzas Axiales", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if node.restraints != (False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], marker='^', s=50, c='#762e99')
            for element in self.elements.values():
                if element.forces[0].round(6) == 0 and element.forces[1].round(6) == 0:
                    pass
                else:
                    a = element.node_i.coords
                    b = element.node_j.coords
                    f2 = element.forces[1]
                    f1 = np.sign(f2)*abs(element.forces[0])
                    forcetype = "Traccion" if f2 > 0 else "Compresion"
                    theta = np.arctan2(b[1] - a[1], b[0] - a[0])
                    c = (a[0] - scale*f1*np.sin(theta),
                         a[1] + scale*f1*np.cos(theta))
                    d = (b[0] - scale*f2*np.sin(theta),
                         b[1] + scale*f2*np.cos(theta))
                    if forcetype == "Traccion":
                        self.ax.fill([a[0], b[0], d[0], c[0]], [
                                     a[1], b[1], d[1], c[1]], '#7f7fff', alpha=0.7, zorder=4)
                        self.ax.plot([a[0], c[0], d[0], b[0]], [
                                     a[1], c[1], d[1], b[1]], c='b', alpha=1, zorder=4)
                    else:
                        self.ax.fill([a[0], b[0], d[0], c[0]], [
                                     a[1], b[1], d[1], c[1]], '#ff7f7f', alpha=0.7, zorder=5)
                        self.ax.plot([a[0], c[0], d[0], b[0]], [
                                     a[1], c[1], d[1], b[1]], c='r', alpha=1, zorder=5)
                    if labels:
                        sim = "T" if forcetype == "Traccion" else "C"
                        if abs(f1) > 1e-6 or abs(f2) > 1e-6:
                            self.ax.text((a[0]+b[0])/2, (a[1]+b[1])/2, f"{sim}= {abs(f1):.2f}", fontsize=8,
                                         color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
                        else:
                            self.ax.text((a[0]+b[0])/2, (a[1]+b[1])/2, f"F1= {element.forces[0]:.2f}\nF2= {element.forces[1]:.2f}",
                                         fontsize=8, color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                self.ax.plot(x, y, c='b', zorder=6)
            self.__plot_ajuste_2d()
            plt.show()

    def plot_reactions(self) -> None:
        if self.ndm == 3:
            plt.close()
            self.figure = plt.figure(figsize=(10, 8))
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.set_title("Reacciones", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if node.restraints != (False, False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], node.coords[2], marker='^', s=50, c='#762e99')
                    reac = node.reactions
                    txt = f"FX= {reac[0]:.2f}\nFY= {reac[1]:.2f}\nFZ= {reac[2]:.2f}"
                    self.ax.text(node.coords[0], node.coords[1], node.coords[2], txt, fontsize=8, color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                z = [element.node_i.coords[2], element.node_j.coords[2]]
                self.ax.plot(x, y, z, c='b')
            self.__plot_ajuste_3d()
            plt.show()
        else:
            plt.close()
            self.figure, self.ax = plt.subplots(figsize=(10, 8))
            self.ax.set_title("Reacciones", fontsize=16, fontweight="bold", color="#0000FF")
            plt.tight_layout()
            for node in self.nodes.values():
                if node.restraints != (False, False):
                    self.ax.scatter(
                        node.coords[0], node.coords[1], marker='^', s=150, c='#762e99')
                    reac = node.reactions
                    txt = f"FX= {reac[0]:.2f}\nFY= {reac[1]:.2f}"
                    self.ax.text(node.coords[0], node.coords[1], txt, fontsize=8, color="k", zorder=17, horizontalalignment="right", verticalalignment="bottom")
            for element in self.elements.values():
                x = [element.node_i.coords[0], element.node_j.coords[0]]
                y = [element.node_i.coords[1], element.node_j.coords[1]]
                self.ax.plot(x, y, c='b')
            self.__plot_ajuste_2d()
            plt.show()

    def __plot_ajuste_3d(self) -> None:
        # --- LIMPIAR EL FONDO Y LA CUADRÍCULA ---
        # Eliminar el fondo gris
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False

        # Quitar los bordes (líneas de los paneles)
        self.ax.xaxis.pane.set_edgecolor('w')
        self.ax.yaxis.pane.set_edgecolor('w')
        self.ax.zaxis.pane.set_edgecolor('w')

        # Quitar las grillas
        self.ax.grid(False)

        # Opcional: ajustar el color del fondo general (figura)
        self.figure.patch.set_facecolor('white')
        self.ax.set_facecolor('white')

        # Mostrar solo los ejes (sin los cubos 3D)
        self.ax.xaxis.line.set_color("black")
        self.ax.yaxis.line.set_color("black")
        self.ax.zaxis.line.set_color("black")

        plt.axis('equal')
        plt.tight_layout()

    def __plot_ajuste_2d(self) -> None:
        from matplotlib.ticker import AutoMinorLocator

        # Configurar cuadrícula
        self.ax.grid(True, linestyle="--", alpha=0.1)

        # Activar los ticks secundarios en ambos ejes
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax.yaxis.set_minor_locator(AutoMinorLocator(5))

        # Activar ticks en los 4 lados (mayores y menores)
        self.ax.tick_params(
            which="both", direction="in", length=6, width=1,
            top=True, bottom=True, left=True, right=True
        )
        # Ticks menores más pequeños y rojos
        self.ax.tick_params(which="minor", length=2,
                            width=0.5, color="black")

        # Mostrar etiquetas en los 4 lados
        self.ax.tick_params(labeltop=True, labelbottom=True,
                            labelleft=True, labelright=True)

        # Asegurar que los ticks se muestran en ambos lados
        self.ax.xaxis.set_ticks_position("both")
        self.ax.yaxis.set_ticks_position("both")

        # Personalizar el color de los ejes
        for spine in ["top", "bottom", "left", "right"]:
            self.ax.spines[spine].set_color("#9bc1bc")  # Color personalizado
            self.ax.spines[spine].set_linewidth(0.5)  # Grosor del borde

        # Personalizar las etiquetas de los ejes
        plt.xticks(fontsize=8, fontfamily="serif",
                   fontstyle="italic", color="#103b58")
        plt.yticks(fontsize=8, fontfamily="serif",
                   fontstyle="italic", color="#103b58")

        # Personalizar los ticks del eje X e Y
        self.ax.tick_params(axis="x", direction="in",
                            length=3.5, width=0.7, color="#21273a")
        self.ax.tick_params(axis="y", direction="in",
                            length=3.5, width=0.7, color="#21273a")

        # Cambiar color del fondo exterior (Canvas)
        self.figure.patch.set_facecolor("#f5f5f5")  # Color gris oscuro

        plt.axis('equal')
        plt.tight_layout()
