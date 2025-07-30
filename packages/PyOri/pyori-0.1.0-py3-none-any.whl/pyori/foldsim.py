# simulator.py
import sys, numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from pyori.graph import Graph
from pyori.foldfile import FoldFile

class FoldSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fold Simulator")
        self.graph = None
        self.scale = 300
        self.offset = np.array([400, 400])
        self.selected_face = None

    def load_graph(self, path):
        fold = FoldFile.load(path)
        g = Graph()
        g.vertices = fold.data["vertices_coords"]
        g.edges = fold.data["edges_vertices"]
        g.assignments = fold.data["edges_assignment"]
        g.faces = fold.data["faces_vertices"]
        self.graph = g
        self.update()

    def paintEvent(self, ev):
        if not self.graph:
            return
        qp = QPainter(self)
        polygons = self.graph.face_polygons()
        for fi, poly in enumerate(polygons):
            pts = [(int(x*self.scale+self.offset[0]), int(-y*self.scale+self.offset[1])) for x,y in poly]
            color = QColor(200,200,255) if fi % 2 == 0 else QColor(255,255,200)
            qp.setBrush(color)
            qp.setPen(Qt.black)
            qp.drawPolygon(QPolygon([QPoint(*pt) for pt in pts]))

        # draw all creases
        qp.setPen(QPen(Qt.black, 1))
        for (u,v), a in zip(self.graph.edges, self.graph.assignments):
            p1 = self.graph.vertices[u]; p2 = self.graph.vertices[v]
            p1s = QPoint(int(p1[0]*self.scale+self.offset[0]), int(-p1[1]*self.scale+self.offset[1]))
            p2s = QPoint(int(p2[0]*self.scale+self.offset[0]), int(-p2[1]*self.scale+self.offset[1]))
            color = Qt.red if a=="M" else Qt.blue if a=="V" else Qt.black
            qp.setPen(QPen(color, 2))
            qp.drawLine(p1s, p2s)

    def mousePressEvent(self, ev: QMouseEvent):
        # Example: flip the first face across the first mountain crease
        if not self.graph:
            return
        for ei,(u,v) in enumerate(self.graph.edges):
            if self.graph.assignments[ei] == "M":
                # reflect face 1 across line (u,v)
                face = self.graph.faces[0]
                P0 = np.array(self.graph.vertices[u]); P1 = np.array(self.graph.vertices[v])
                axis = (P1 - P0) / np.linalg.norm(P1-P0)
                for i in face:
                    P = np.array(self.graph.vertices[i])
                    d = np.dot(P-P0, axis)
                    self.graph.vertices[i] = ((P - P0) - 2*d*(axis)) + P0
                break
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FoldSimulator()
    w.resize(800,800)
    w.show()
    path, _ = QFileDialog.getOpenFileName(w, "Open FOLD File", "", "FOLD (*.fold)")
    if path:
        w.load_graph(path)
    sys.exit(app.exec_())
