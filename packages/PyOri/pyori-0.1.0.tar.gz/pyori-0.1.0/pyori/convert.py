import json
import svgwrite
from svgpathtools import svg2paths
import networkx as nx

#---------- CONFIGURATION ----------

DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 500

#---------- HELPERS ----------

def assignment_color(a):
    return {
        "M": "red",
        "V": "blue",
        "B": "black",
        "U": "gray"
    }.get(a, "green")

def round_point(p, tol=1e-4):
    return (round(p[0]/tol)*tol, round(p[1]/tol)*tol)

def find_or_add_vertex(vertices, point, tol=1e-4):
    rp = round_point(point, tol)
    for i, v in enumerate(vertices):
        if round_point(v, tol) == rp:
            return i
    vertices.append(point)
    return len(vertices) - 1

def extract_faces(edges, vertices):
    G = nx.Graph()
    for i, v in enumerate(vertices):
        G.add_node(i, coord=v)
    for u, v in edges:
        G.add_edge(u, v)

    is_planar, embedding = nx.check_planarity(G)
    if not is_planar:
        raise ValueError("Graph is not planar")

    embedding = embedding.copy()
    seen = set()
    faces = []

    for u in embedding:
        for v in embedding[u]:
            if (u, v) not in seen:
                face = embedding.traverse_face(u, v)
                faces.append(face)
                #mark both directions as seen
                for i in range(len(face)):
                    seen.add((face[i], face[(i+1)%len(face)]))

    return [list(face) for face in faces if len(face) >= 3]

#---------- FOLD → SVG ----------

def fold_to_svg(fold_path, svg_path, width=500, height=500, padding=10):
    with open(fold_path, 'r') as f:
        data = json.load(f)

    vertices = data["vertices_coords"]
    edges = data["edges_vertices"]
    assignments = data.get("edges_assignment", ["U"] * len(edges))

    #get bounds
    xs, ys = zip(*vertices)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    scale_x = (width - 2 * padding) / (max_x - min_x) if max_x > min_x else 1
    scale_y = (height - 2 * padding) / (max_y - min_y) if max_y > min_y else 1
    scale = min(scale_x, scale_y)

    #normalize and flip Y
    def transform(p):
        x, y = p
        nx = (x - min_x) * scale + padding
        ny = height - ((y - min_y) * scale + padding)
        return (nx, ny)

    transformed_vertices = [transform(v) for v in vertices]

    dwg = svgwrite.Drawing(svg_path, size=(width, height))

    for (v1, v2), a in zip(edges, assignments):
        x1, y1 = transformed_vertices[v1]
        x2, y2 = transformed_vertices[v2]
        color = assignment_color(a)
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=color, stroke_width=1))

    dwg.save()
    print(f"Saved SVG to {svg_path}")

#---------- SVG → FOLD ---------- 
#CURRENTLY NOT WORKING

import json
import os
import re
import xml.etree.ElementTree as ET
from svgpathtools import svg2paths
from pyori.graph import Graph

def round_point(p, tol=1e-3):
    return (round(p[0]/tol)*tol, round(p[1]/tol)*tol)

def validate_svg(svg_path):
    if not os.path.exists(svg_path):
        print(f"File does not exist: {svg_path}")
        return False
    try:
        paths, _ = svg2paths(svg_path)
        return any(segment.start != segment.end for path in paths for segment in path)
    except Exception as e:
        print(f"SVG parse error: {e}")
        return False

def parse_svg_to_edges(svg_path, tol=1e-3):
    paths, _ = svg2paths(svg_path)
    vertices = []
    vertex_map = {}
    edges = []

    def get_idx(pt):
        key = round_point((pt.real, pt.imag), tol)
        if key not in vertex_map:
            vertex_map[key] = len(vertices)
            vertices.append([pt.real, pt.imag])
        return vertex_map[key]

    for path in paths:
        for segment in path:
            if segment.start != segment.end:
                i = get_idx(segment.start)
                j = get_idx(segment.end)
                edges.append([i, j])
    return edges, vertices

def convert_svg_to_fold(svg_path, output_path):
    if not validate_svg(svg_path):
        print("Invalid SVG.")
        return

    edges, vertices = parse_svg_to_edges(svg_path)
    g = Graph.from_edges_vertices(edges, vertices)
    fold = g.to_foldfile()

    with open(output_path, "w") as f:
        json.dump(fold.data, f, indent=2)

    print(f".fold file saved to: {output_path}")


