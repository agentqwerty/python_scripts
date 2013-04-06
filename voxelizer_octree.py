# Standard Imports
import re

# Non-standard Imports
import octTree

# Maya Imports
MAYA_MODE = True
try:
    import maya.cmds as cmds
except ImportError:
    MAYA_MODE = False

__doc__ = """
This is a script for generating a voxel representation of a mesh.
"""

# Globals
VERT_SPLIT_RE = re.compile(".*\[(\d*):(\d*)\]")


def _flatten_vert_list(mesh_name, vert_list):
    """
    Given a list containing vertices which may appear as ranges, return a list
    containing only exact vertices. (e.g converts [pPlane1.vtx[0:2]] to 
    [pPlane1.vtx[0], pPlane1.vtx[1] pPlane1.vtx[2]]
    NOTE: The ranges maya returns are inclusive on both ends.
    """
    flattened_verts = []
    for vert_item in vert_list:
        match = VERT_SPLIT_RE.match(vert_item)
        if not match:
            continue
        for vert_index in match.groups():
            flattened_verts.append('%s.vtx[%d]'%(mesh_name, vert_index))
    return flattened_verts

# Functions.
def _voxelize_mesh(mesh_name, num_divisions):
    """
    Given a mesh name, and a number of division levels, will create a voxelized
    version of the mesh.
    mesh_name: the name of the mesh
    num_divisions: the number of times to subdivide the octTree. Each
    subdivision results in voxels 1/2 the size of the previous subdivision.
    """
    # Get the bouding box of the mesh and create an octTree using the bounds
    min_x, min_y, min_z, max_x, max_y, max_z =\
            cmds.exactWorldBoundingBox(mesh_name)
    oct_tree = octTree.OctTree((min_x,min_y,min_z), (max_x,max_y,max_z))
    oct_tree_nodes = [oct_tree.root]

    # Subdivide the octTree to desired division level.
    while oct_tree_nodes:
        tree_node = oct_tree_nodes.pop(0)
        if tree_node.division_level < num_divisions:
            tree_node.subdivide()
            oct_tree_nodes.append(tree_node.children())
        break

    voxel_locations = set()
    # For each face in the mesh, find the node(s) containing that face.
    for face_index in xrange(cmds.polyEvaluate(mesh_name, f=True)):
        verts = cmds.polyListComponentConversion('%s.f[%d]'%(mesh_name, 
            face_index), ff=True, tv=True)

        #Flatten the vertex list
        vert_list = _flatten_vert_list(mesh_name, verts)

        # Find the leaf node containing this vert.
        for vert in vert_list:
            node = oct_tree.root
            while node.children:
                node = node.child_containing(vert)

            # Add the midpoint of the leaf node to the voxel set
            voxel_locations.add(node.half_values)

    # Create a cube at each of the voxel_locations
    for i, (lx, ly, lz) in enumerate(voxel_locations):
        cname = '%s_vox_%d'%(mesh_name, i)
        cmds.polyCube(name=cname)
        cmds.xform(cname, translation=[lx,ly,lz])

def runMaya():
    """
    Voxelizes the currently selected mesh(es).
    """
    if not MAYA_MODE:
        print "Tool must be run within Maya."
        return

    selected_objs = cmds.ls(sl=True)
    for obj in selected_objs:
        # Try and get the shape node to verify it's a mesh
        try:
            shape_node = cmds.listRelatives(obj, children=True, shapes=True)[0]
            node_type = cmds.nodeType(shape_node)
            if not node_type == 'mesh':
                continue
        except IndexError:
            continue

        # Voxelize!
        _voxelize_mesh(obj)
