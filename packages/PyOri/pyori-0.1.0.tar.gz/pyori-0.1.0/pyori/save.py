#import libraries
import stl
import pyvista as pv
import numpy as np
import trimesh
from pyori.foldfile import FoldFile

#convert FOLD file to mesh
def fold_to_mesh(fold_path, out_path="output.obj"):
    fold = FoldFile.load(fold_path)
    vertices = fold.data["vertices_coords"]
    faces_raw = fold.data["faces_vertices"]

    #force 2D into 3D by padding zeros if needed
    vertices = [v + [0] if len(v) == 2 else v for v in vertices]

    #triangulate each face if needed
    all_faces = []

    for face in faces_raw:
        if len(face) == 3:
            all_faces.append(face)
        elif len(face) > 3:
            #convert polygon to triangles using convex hull approximation
            polygon = np.array([vertices[i] for i in face])
            if polygon.shape[1] == 2:
                polygon = np.pad(polygon, ((0, 0), (0, 1)), constant_values=0)  #force into 3D

            try:
                tri = trimesh.Trimesh(vertices=polygon).convex_hull
                for t in tri.faces:
                    tri_verts = tri.vertices[t]
                    new_idx = []
                    for v in tri_verts:
                        v = list(v)
                        if v in vertices:
                            new_idx.append(vertices.index(v))
                        else:
                            vertices.append(v)
                            new_idx.append(len(vertices) - 1)
                    all_faces.append(new_idx)
            except Exception as e:
                print(f"Failed to triangulate face {face}: {e}")

    #write mesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=all_faces, process=False)
    return mesh

    '''mesh.export(out_path) #export
    print(f"Mesh exported to {out_path}")'''

#export mesh to .obj
def fold_to_obj(fold_file, obj_file):
    mesh = fold_to_mesh(fold_file)
    with open(obj_file, 'w') as f:
        for v in mesh.vertices:
            f.write(f'v {v[0]} {v[1]} {v[2]}\n')
        for face in mesh.faces:
            f.write(f'f {face[0] + 1} {face[1] + 1} {face[2] + 1}\n')

#export mesh to .stl
def fold_to_stl(fold_file, stl_file):
   mesh = fold_to_mesh(fold_file)

   #using numpy-stl
   #stl_mesh = stl.mesh.Mesh(np.zeros(mesh.faces.shape[0], dtype=stl.mesh.Mesh.dtype))
   #for i, face in enumerate(mesh.faces):
   #    stl_mesh.vectors[i] = mesh.vertices[face]
   #stl_mesh.save(stl_file)

   #using pyvista
   poly = pv.PolyData(mesh.vertices, faces=np.hstack((np.full((mesh.faces.shape[0], 1), 3), mesh.faces)))
   poly.save(stl_file)

'''
#example usage:
fold_file = 'crane.fold'
obj_file = 'output.obj'
stl_file = 'output.stl'

fold_to_obj(fold_file, obj_file)
fold_to_stl(fold_file, stl_file)
'''