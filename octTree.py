__doc__ = """
This library is an implementation of an oct tree data structure. 
"""

class OctTree(object):
    """
    A data structure for partitioning space into octants.
    """
    def __init__(self, bounding_point_min, bounding_point_max):
        """
        bounding_point_min: a tuple containing the minimum x,y,z values of the
            initial bounding box.
        bounding_point_max: a tuple containing the maximum x,y,z values of the
            initial bounding box.
        """
        self.bp_max = bounding_point_max
        self.bp_min = bounding_point_min
        self.root = OctTreeNode(self.bp_min, self.bp_max, dl=0, parent=self)

class OctTreeNode(object):
    """
    Represents an octant.
    """
    def __init__(self, bp_min, bp_max, dl=0, parent=None):
        """
        bp_min: a tuple containing the minimum x,y,z values of the initial 
            bounding box.
        bp_max: a tuple containing the maximum x,y,z values of the initial 
            bounding box.
        dl: the divison level of this node. e.g this node is 2**dl times
            smaller than the original octTree bounding box size.
        parent: the parent octree for this node.
        """
        self.bp_min = bp_min
        self.bp_max = bp_max
        self.half_values = self._half_values()
        self.parent = parent
        self.division_level = dl
        self.children = []

    def _half_values(self):
        """
        Returns the values halfway between max and min x,y,z.
        """
        max_x, max_y, max_z = self.bp_max
        min_x, min_y, min_z = self.bp_min
        half_x = (max_x+min_x)/2.0
        half_y = (max_y+min_y)/2.0
        half_z = (max_z+min_z)/2.0
        return (half_x, half_y, half_z)

    def node_containing(self, point):
        """
        Returns the child node containing the given point.
        point: (x,y,z)
        """
        px,py,pz = point
        half_x, half_y, half_z = self.half_values

        # Figure out which octant the point is in. gt = greater than
        gt_half_x = int(px >= half_x)
        gt_half_y = int(py >= half_y)
        gt_half_z = int(pz >= half_z)

        # yeah, use those bits.
        child_index = 4*gt_half_z + 2*gt_half_y + gt_half_x
        return self.children[child_index]

    def is_inside(self, point):
        """
        Returns True if the given point lies inside this OctTreeNode, False
        otherwise.
        point: A tuple containing (x,y,z) positions of the point.
        """
        x,y,z = point
        in_x = self.bp_min[0] <= x < self.bp_max[0]
        in_y = self.bp_min[1] <= y < self.bp_max[1]
        in_z = self.bp_min[2] <= z < self.bp_max[2]
        return all(in_x, in_y, in_z)

    def subdivide(self):
        """
        Divides an OctTreeNode into 8 octants. The subdivided node is replaced
        in the nodelist by the octants.
        node: an OctTreeNode to subdivide.
        """
        # Divide the node into octants.
        octant_list = []
        dl = self.division_level+1
        max_x, max_y, max_z = self.bp_max
        min_x, min_y, min_z = self.bp_min
        half_x, half_y, half_z = self.half_values

        oct_0_min = node.bp_min #000
        oct_0_max = (half_x, half_y, half_z)
        octant_list.append(OctTreeNode(oct_0_min, oct_0_max, dl=dl, parent=self))

        oct_1_min = (half_x, min_y, min_z) #001
        oct_1_max = (max_x, half_y, half_z)
        octant_list.append(OctTreeNode(oct_1_min, oct_1_max, dl=dl, parent=self))

        oct_2_min = (min_x, half_y, min_z) #010
        oct_2_max = (half_x, max_y, half_z)
        octant_list.append(OctTreeNode(oct_2_min, oct_2_max, dl=dl, parent=self))

        oct_3_min = (half_x, half_y, min_z) #011
        oct_3_max = (max_x, max_y, half_z)
        octant_list.append(OctTreeNode(oct_3_min, oct_3_max, dl=dl, parent=self))

        oct_4_min = (min_x, min_y, half_z) #100
        oct_4_max = (half_x, half_y, max_z)
        octant_list.append(OctTreeNode(oct_4_min, oct_4_max, dl=dl, parent=self))

        oct_5_min = (half_x, min_y, half_z) #101
        oct_5_max = (max_x, half_y, max_z)
        octant_list.append(OctTreeNode(oct_5_min, oct_5_max, dl=dl, parent=self))

        oct_6_min = (min_x, half_y, half_z) #110
        oct_6_max = (half_x, max_y, max_z)
        octant_list.append(OctTreeNode(oct_6_min, oct_6_max, dl=dl, parent=self))

        oct_7_min = (half_x, half_y, half_z) #111
        oct_7_max = node.bp_max
        octant_list.append(OctTreeNode(oct_7_min, oct_7_max, dl=dl, parent=self))

        # Remove the original node and add the octants
        self.children = octant_list
