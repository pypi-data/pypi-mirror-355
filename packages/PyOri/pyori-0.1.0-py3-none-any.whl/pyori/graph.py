# rabbitpy/graph.py

from pyori.foldfile import FoldFile

#graph, graph to fold & svg

class Graph:
    def __init__(self): #type = list 
        self.vertices = []    #[x, y] coords
        self.edges = []       #list of [vertex_idx1, vertex_idx2]
        self.assignments = [] #fold type 'M', 'V', 'F', etc.
        self.faces = []       #face list (vertex indices list)

    def add_vertex(self, coord):
        self.vertices.append(coord)
        return len(self.vertices) - 1

    def add_edge(self, v1_idx, v2_idx, assignment=None):
        self.edges.append([v1_idx, v2_idx])
        if assignment is None:
            self.assignments.append("F")  #default to Flat
        else:
            self.assignments.append(assignment)

    def add_face(self, vertices_idx):
        self.faces.append(vertices_idx)

    def remove_vertex(self, idx):
        if 0 <= idx < len(self.vertices):
            self.vertices.pop(idx)
            #IMPORTANT ADD: UPDATE EDGES AND FACES
        else:
            raise IndexError(f"Vertex {idx} does not exist.")

    def remove_edge(self, idx):
        if 0 <= idx < len(self.edges):
            self.edges.pop(idx)
            self.assignments.pop(idx)
        else:
            raise IndexError(f"Edge {idx} does not exist.")

    def to_dict(self):
        return {
            "vertices_coords": self.vertices,
            "edges_vertices": self.edges,
            "edges_assignment": self.assignments,
            "faces_vertices": self.faces
        }

    def to_foldfile(self):
        fold = FoldFile()
        fold.data["vertices_coords"] = self.vertices
        fold.data["edges_vertices"] = self.edges
        fold.data["edges_assignment"] = self.assignments
        fold.data["faces_vertices"] = self.faces
        return fold
    
    def auto_detect_faces_simple_traversal(self):
    #simple method (for convex, well-formed graphs)
    #assumes graph is simple & all edges form faces
    #like BFS/DFS but without backtracking & recursion
        if not self.edges:
            return

        edge_map = {}
        for idx, (v0, v1) in enumerate(self.edges):
            edge_map.setdefault(v0, []).append(v1)
            edge_map.setdefault(v1, []).append(v0)

        visited = set()
        faces = []

        for start_vertex in range(len(self.vertices)):
            if start_vertex in visited:
                continue

            current_face = [start_vertex]
            current_vertex = start_vertex

            while True: #uses simple loop instead of resusion like BFS/DFS
                neighbors = edge_map.get(current_vertex, [])
                #pick the first neighbor that is not yet visited (simple rule)
                next_vertices = [v for v in neighbors if v not in current_face]
                if not next_vertices:
                    break
                next_vertex = next_vertices[0]
                current_face.append(next_vertex)
                current_vertex = next_vertex

                if next_vertex == start_vertex:
                    break

            if len(current_face) > 2:
                faces.append(current_face)
                visited.update(current_face)

        self.faces = faces

    @staticmethod
    def from_edges_vertices(edges, vertices):
        g = Graph()
        g.vertices = vertices
        g.edges = edges
        g.assignments = ["F"] * len(edges)
        g.auto_detect_faces()
        return g

    def auto_detect_faces(self):
        import networkx as nx
        import networkx.algorithms.planarity as nxp

        g_nx = nx.Graph()
        for idx, coord in enumerate(self.vertices):
            g_nx.add_node(idx, coord=coord)
        for (i, j) in self.edges:
            g_nx.add_edge(i, j)

        try:
            is_planar, embedding = nxp.check_planarity(g_nx)
            if not is_planar:
                print("Graph is not planar. Cannot detect faces.")
                return

            faces = []
            #traverse to find faces
            for face in nxp.planar_faces(embedding):
                if len(face) > 2:
                    faces.append(face)
            self.faces = faces
            print(f"Auto-detected {len(faces)} faces.")
        except Exception as e:
            print(f"Face detection failed: {e}")

    def to_networkx(self):
        import networkx as nx
        G = nx.Graph()

        # add nodes with 2D positions
        for idx, coord in enumerate(self.vertices):
            if (
                isinstance(coord, (list, tuple)) and
                len(coord) == 2 and
                all(isinstance(c, (int, float)) for c in coord)
            ):
                G.add_node(idx, pos=coord)
            else:
                print(f"⚠️ Skipping invalid vertex {idx}: {coord}")

        # add edges with assignments
        for (v1, v2), assignment in zip(self.edges, self.assignments):
            G.add_edge(v1, v2, assignment=assignment)

        return G
    
    def face_polygons(self):
        #list of 2D polygons (lists of [x, y] coords) for each face
        return [[self.vertices[i] for i in face] for face in self.faces]

