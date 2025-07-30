import svgwrite

#graph to svg

def edge_color(assignment):
    if assignment == "M":
        return "red"
    elif assignment == "V":
        return "blue"
    else:
        return "black"

def edge_color(assignment, mode="all"):
    if mode == "base":
        return "black"
    if mode == "mountain" and assignment == "M":
        return "red"
    if mode == "valley" and assignment == "V":
        return "blue"
    if mode == "cut" and assignment == "F":
        return "black"
    return None  #don't draw

def export_graph_as_svg( #contains modes, ex. coloring/black-white
    graph,
    filename="output.svg",
    width=500,
    height=500,
    mode="all",
    draw_faces=False,
    draw_vertices=False,
    face_fill_color="#e0e0e0"
):
    dwg = svgwrite.Drawing(filename, size=(width, height))

    #scaling
    min_x = min((v[0] for v in graph.vertices), default=0)
    min_y = min((v[1] for v in graph.vertices), default=0)
    max_x = max((v[0] for v in graph.vertices), default=1)
    max_y = max((v[1] for v in graph.vertices), default=1)

    def scale(x, y):
        sx = (x - min_x) / (max_x - min_x) * width * 0.8 + width * 0.1
        sy = (y - min_y) / (max_y - min_y) * height * 0.8 + height * 0.1
        return sx, sy

    #draw faces if enabled
    if draw_faces and hasattr(graph, 'faces'):
        for face in graph.faces:
            points = [scale(*graph.vertices[idx]) for idx in face]
            dwg.add(dwg.polygon(points, fill=face_fill_color, stroke="none"))

    #draw edges loop
    for edge, assignment in zip(graph.edges, graph.assignments):
        v0, v1 = edge
        x0, y0 = scale(*graph.vertices[v0])
        x1, y1 = scale(*graph.vertices[v1])

        color = edge_color(assignment, mode)
        if color is None:
            continue  #skip this edge if it doesn't match mode

        line_args = {
            "start": (x0, y0),
            "end": (x1, y1),
            "stroke": color,
            "stroke_width": 2,
        }
        if assignment == "V" and (mode in ["all", "valley"]):
            line_args["stroke_dasharray"] = [5, 5]

        line = dwg.line(**line_args)
        dwg.add(line)

    #draw vertices if enabled
    if draw_vertices:
        for idx, (x, y) in enumerate(graph.vertices):
            sx, sy = scale(x, y)
            dwg.add(dwg.circle(center=(sx, sy), r=2, fill="black"))

    dwg.save()
    print(f"SVG saved to {filename}")


'''
#Example usage of library

#from rabbitpy.svg import export_graph_as_svg
from rabbitpy.graph import Graph

g = Graph()
#add vertices + edges

#full base
export_graph_as_svg(g, filename="base.svg", mode="base")

#only mountain
export_graph_as_svg(g, filename="mountain.svg", mode="mountain")

#only valley
export_graph_as_svg(g, filename="valley.svg", mode="valley")

#only cuts for Cricut
export_graph_as_svg(g, filename="cut.svg", mode="cut")

#with faces colored and vertices shown
export_graph_as_svg(g, filename="colored.svg", draw_faces=True, draw_vertices=True)
'''
