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
        self.nodes = [OctTreeNode(self.bp_min, self.bp_max, dl=0, parent=self)]

    def subdivide_node(self, node):
        """
        Divides an OctTreeNode into 8 octants. The subdivided node is replaced
        in the nodelist by the octants.
        node: an OctTreeNode to subdivide.
        """
        # Divide the node into octants.
        octant_list = []
        dl = node.division_level+1
        max_x, max_y, max_z = node.bp_max
        min_x, min_y, min_z = node.bp_min

        half_x = (max_x+min_x)/2.0
        half_y = (max_y+min_y)/2.0
        half_z = (max_z+min_z)/2.0

        oct_1_min = node.bp_min
        oct_1_max = (half_x, half_y, half_z)
        octant_list.append(OctTreeNode(oct_1_min, oct_1_max, dl=dl, parent=self))

        oct_2_min = (half_x, min_y, min_z)
        oct_2_max = (max_x, half_y, half_z)
        octant_list.append(OctTreeNode(oct_2_min, oct_2_max, dl=dl, parent=self))

        oct_3_min = (min_x, min_y, half_z)
        oct_3_max = (half_x, half_y, max_z)
        octant_list.append(OctTreeNode(oct_3_min, oct_3_max, dl=dl, parent=self))

        oct_4_min = (half_x, min_y, half_z)
        oct_4_max = (max_x, half_y, max_z)
        octant_list.append(OctTreeNode(oct_4_min, oct_4_max, dl=dl, parent=self))

        oct_5_min = (min_x, half_y, min_z)
        oct_5_max = (half_x, max_y, half_z)
        octant_list.append(OctTreeNode(oct_5_min, oct_5_max, dl=dl, parent=self))

        oct_6_min = (half_x, half_y, min_z)
        oct_6_max = (max_x, max_y, half_z)
        octant_list.append(OctTreeNode(oct_6_min, oct_6_max, dl=dl, parent=self))

        oct_7_min = (min_x, half_y, half_z)
        oct_7_max = (half_x, max_y, max_z)
        octant_list.append(OctTreeNode(oct_7_min, oct_7_max, dl=dl, parent=self))

        oct_8_min = (half_x, half_y, half_z)
        oct_8_max = node.bp_max
        octant_list.append(OctTreeNode(oct_8_min, oct_8_max, dl=dl, parent=self))

        # Remove the original node and add the octants
        self.nodes.remove(node)
        self.nodes.extend(octant_list)


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
        self.parent = parent
        self.division_level = dl

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
