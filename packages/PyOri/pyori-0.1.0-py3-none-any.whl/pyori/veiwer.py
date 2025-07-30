# view/graph_viewer.py
# rabbitpy/viewer.py
#pip install trimesh matplotlib open3d pythreejs vedo
import trimesh #uses pyglet: 'pip install "pyglet<2"'
import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(G, show_labels=True, save_path="graph_output.png"):
    #try: extract positions from node attributes, else fallback
    try:
        pos = nx.get_node_attributes(G, "coord")
        if not pos:
            raise ValueError("No 'coord' attribute found.")
    except Exception:
        pos = nx.spring_layout(G, seed=42)
        print("Warning: No valid node positions. Using spring layout instead.")

    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, with_labels=show_labels, node_size=300,
            node_color="skyblue", edge_color="black", linewidths=1.5)

    if show_labels:
        labels = {node: str(node) for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=10)

    plt.title('Graph Viewer')
    plt.axis('equal')
    plt.savefig(save_path)
    print(f"Graph saved to {save_path}")
    plt.close()



'''
# Load or create a mesh (example: icosphere)
mesh = trimesh.creation.icosphere(subdivisions=2, radius=1.0)

# Quick 3D plot using Trimesh’s built-in viewer
mesh.show()  # Opens in browser or GUI viewer

# For Matplotlib 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_trisurf(mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2], triangles=mesh.faces, color='lightblue')
plt.show()
'''
'''
import trimesh
import open3d as o3d
import numpy as np

# Convert Trimesh to Open3D format
mesh = trimesh.creation.icosphere()
o3d_mesh = o3d.geometry.TriangleMesh()
o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)
o3d_mesh.compute_vertex_normals()

o3d.visualization.draw_geometries([o3d_mesh])

'''

