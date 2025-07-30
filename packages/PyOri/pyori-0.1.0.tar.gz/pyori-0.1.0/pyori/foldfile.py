import json

class FoldFile:
    def __init__(self):
        self.data = {
            "file_spec": 1.1,
            "file_creator": "rabbitpy",
            "file_author": "you",
            "file_title": "Generated Origami",
            "vertices_coords": [],
            "edges_vertices": [],
            "edges_assignment": [],
            "faces_vertices": []
        }

    def add_vertex(self, coord):
        self.data["vertices_coords"].append(coord)

    def add_edge(self, v1, v2, assignment="F"):
        self.data["edges_vertices"].append([v1, v2])
        self.data["edges_assignment"].append(assignment)

    def add_face(self, vertices):
        self.data["faces_vertices"].append(vertices)

    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.data, f, indent=2)

    @staticmethod
    def load(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        ffile = FoldFile()
        ffile.data = data
        return ffile
