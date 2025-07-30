#import open3d as o3d
import numpy as np
import time
'''
# Create mesh
mesh = o3d.geometry.TriangleMesh.create_sphere()
mesh.compute_vertex_normals()

# Create visualizer
vis = o3d.visualization.Visualizer()
vis.create_window()
vis.add_geometry(mesh)

# Rotate mesh for animation
for i in range(100):
    mesh.rotate(mesh.get_rotation_matrix_from_xyz((0, 0.1, 0)), center=(0, 0, 0))
    vis.update_geometry(mesh)
    vis.poll_events()
    vis.update_renderer()
    time.sleep(0.05)

vis.destroy_window()
'''
'''
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import trimesh

mesh = trimesh.creation.icosphere()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

trisurf = ax.plot_trisurf([], [], [], triangles=mesh.faces, color='lightblue')

def init():
    trisurf.set_verts([])
    return trisurf,

def update(frame):
    angle = frame * 4
    ax.view_init(elev=30, azim=angle)
    trisurf.set_verts(mesh.vertices)
    return trisurf,

ani = FuncAnimation(fig, update, init_func=init, frames=90, interval=50, blit=False)
plt.show()
'''

from vedo import Sphere, show
import numpy as np

mesh = Sphere()
plt = show(mesh, interactive=True)

for i in range(100):
    mesh.rotate_x(1)
    plt.render()
    
time.sleep(0.2)

