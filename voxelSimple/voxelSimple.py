__doc__ = """
This is a mesh voxelizer implementation for Maya. Given a mesh and a division
level, the script will create a voxelized version of the mesh.
"""

# Imports
import satTest
import maya.cmds as cmds

def voxelize(mesh_name, division_level):
    """
    Voxelize the given mesh.
    mesh_name: the name of the mesh
    division_level: the number of times to subdivide the initial bounding box.
    """
    # Get the bouding box for the mesh
    min_x, min_y, min_z, max_x, max_y, max_z =\
            cmds.exactWorldBoundingBox(mesh_name)

    cx = (max_x + min_x)/2.0
    cy = (max_y + min_y)/2.0
    cz = (max_z + min_z)/2.0
    hx = (max_x - min_x)/2.0
    hy = (max_y - min_y)/2.0
    hz = (max_z - min_z)/2.0
    hl = max([hx, hy, hz])

    # Subdivide the bounding boxes until we've reached the desired subdiv level
    root_aabb = satTest.AABB(cx,cy,cz,hl,hl,hl)
    voxel_lattice = [root_aabb]
    while voxel_lattice:
        current_voxel = voxel_lattice.pop(0)
        if current_voxel.subdivs < division_level:
            voxel_lattice.extend(current_voxel.subdivide())
            continue
        voxel_lattice.append(current_voxel)
        break

    # Triangluate the mesh.
    #@TODO: probably best to implment this without modifying the original mesh,
    # but then we need to implement our own polygon --> triangle subdivison.
    cmds.polyTriangulate(mesh_name, ch=1)
    
    # Loop over each face in the mesh, and find which boxes it intersects.
    vox_map = {}
    faces = cmds.ls('%s.f[*]'%mesh_name, fl=True)
    
    i = 0
    initializeProgressWindow("Voxelizing Mesh", len(faces))
    for face in faces:
        if not updateProgressWindow(i, len(faces)):
            break
        verts = cmds.ls(cmds.polyListComponentConversion(face, tv=True), fl=True)
        v0 = cmds.xform(verts[0], t=True, q=True)
        v1 = cmds.xform(verts[1], t=True, q=True)
        v2 = cmds.xform(verts[2], t=True, q=True)
        tri_verts = v0+v1+v2
        tri = satTest.Triangle(*tri_verts)
        for voxel in voxel_lattice:
            try:
                is_filled = vox_map[voxel.center]
                continue
            except KeyError:
                pass

            if tri.intersects(voxel):
                vox_map[voxel.center] = voxel.half_vector

        i += 1

    # Fill in the voxels
    voxel_group = '%s_vox_group'%mesh_name
    cmds.group(name=voxel_group, em=True)
    for i, ((lx, ly, lz), (sx, sy, sz)) in enumerate(vox_map.items()):
        scale_factor = sx/hx
        cname = '%s_vox_%d'%(mesh_name, i)
        cmds.polyCube(name=cname)
        cmds.xform(cname, translation=[lx,ly,lz])
        cmds.parent(cname, voxel_group)

    killProgressWindow()


# UI Functions
def initializeProgressWindow(title, max_size):
    cmds.progressWindow(title=title, progress=0, max=max_size,
            isInterruptable=True)

def updateProgressWindow(i, max_size):
    if cmds.progressWindow(q=True, ic=True):
        return False
    else:
        cmds.progressWindow(e=True, pr=i, st=("Face: %d/%d"%(i,max_size)))
        return True

def killProgressWindow():
    cmds.progressWindow(ep=True)
    print "Voxel generation complete."
        
