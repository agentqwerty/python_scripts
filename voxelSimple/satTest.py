__doc__ = """
Implementation of SAT (separating axis theorem) to test polygon-bounding box
intersection.
"""
# Standard Imports
import math, unittest

# Classes
class SimpleVec(object):
    """
    A simple vector class for use if we're not in maya.
    """
    def __init__(self, x,y,z):
        self.x = x
        self.y = y
        self.z = z
        self._invert_zeroes()

    def __add__(self, v):
        return SimpleVec(self.x+v.x, self.y+v.y, self.z+v.z)

    def __eq__(self, v):
        eq_x = self.x == v.x
        eq_y = self.y == v.y
        eq_z = self.z == v.z
        return all([eq_x, eq_y, eq_z])

    def __sub__(self, v):
        return SimpleVec(self.x-v.x, self.y-v.y,self.z-v.z)

    def __mul__(self, v):
        if type(v) == SimpleVec:
            return self.cross(v)
        else:
            return SimpleVec(self.x*v, self.y*v, self.z*v)

    def __rmul__(self, v):
        if type(v) == SimpleVec:
            return v.cross(self)
        else:
            return SimpleVec(self.x*v, self.y*v, self.z*v)

    def __iter__(self):
        for v in [self.x, self.y, self.z]:
            yield v

    def __str__(self):
        return '[%s]'%','.join([str(i) for i in [self.x,self.y,self.z]])

    def _invert_zeroes(self):
        """
        Inverts the sign of any vector components valued at -0.0. This is to
        ensure that equality statements evaluate correctly.
        """
        if self.x == -0.0:
            self.x = 0.0
        if self.y == -0.0:
            self.y = 0.0
        if self.z == -0.0:
            self.z = 0.0

    def cross(self, v):
        """
        Cross product.
        | i   j   k   |
        | s.x s.y s.z |
        | v.x v.y v.z |
        """
        x_comp = self.y*v.z - v.y*self.z
        y_comp = self.x*v.z - v.x*self.z
        z_comp = self.x*v.y - v.x*self.y
        return SimpleVec(x_comp, -y_comp, z_comp)

    def dot(self, v):
        """
        Dot product.
        """
        return self.x*v.x + self.y*v.y + self.z*v.z

    def normalize(self):
        """
        Normalize this vector.
        """
        magnitude = math.sqrt(self.x**2+self.y**2+self.z**2)
        self.x = self.x/magnitude
        self.y = self.y/magnitude
        self.z = self.z/magnitude


# Import vector class
try:
    from pymel.core.datatypes import Vector as Vec3d
except ImportError:
    Vec3d = SimpleVec


# Intersection Classes
class Shape(object):
    """
    A generalized representation of a shape. A shape is defined as a collection
    of vertices.
    """
    # Define a zero vector for identifying degenerate cross products
    zero_vector = Vec3d(0.0,0.0,0.0)

    def __init__(self, vertices):
        """
        vertices: a list of Vec3d objects representing the vertices of the
        shape
        """
        self.vertices = vertices
        self._max_values(vertices)

    def __str__(self):
        return str('(%s)'%','.join([str(v) for v in self.vertices]))

    def __getitem__(self, key):
        return self.vertices[key]

    def __setitem__(self, key, value):
        self.vertices[key] = value

    def _max_values(self, vertices):
        """
        Obtains the max x,y,z values among the given verts.
        vertices: a list of vertices.
        """
        max_x = vertices[0].x
        min_x = vertices[0].x
        max_y = vertices[0].y
        min_y = vertices[0].y
        max_z = vertices[0].z
        min_z = vertices[0].z

        for v in vertices:
            x,y,z = v
            if x > max_x:
                max_x = x
            elif x < min_x:
                min_x = x

            if y > max_y:
                max_y = y
            elif y < min_y:
                min_y = y

            if z > max_z:
                max_z = z
            elif z < min_z:
                min_z = z

        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.min_z = min_z
        self.max_z = max_z

    def _quick_rejection(self, shape):
        """
        Tests the min/max values of the given shape with this one, and if
        returns True if intersection is not possible.
        """
        if self.max_x < shape.min_x:
            return True
        if self.min_x > shape.max_x:
            return True
        if self.max_y < shape.min_y:
            return True
        if self.min_y > shape.max_y:
            return True
        if self.max_z < shape.min_z:
            return True
        if self.min_z > shape.max_z:
            return True
        return False

    def project(self, axis):
        """
        Project this shape onto the given axis. Returns the minimum and maximum
        values for the projection.

        axis: a Vec3d object representing the projection axis.
        """
        minVal = axis.dot(self.vertices[0])
        maxVal = minVal
        for v in self.vertices:
            p = axis.dot(v)
            if p < minVal:
                minVal = p
            elif p > maxVal:
                maxVal = p
        return (minVal, maxVal)

    def _overlap(self, min_max0, min_max1):
        """
        Returns True if overlap exists between the min-max ranges of minMax0
        and min_max1, False otherwise.
        minMax<0,1>: Tuples containing (minValue, maxValue)
        """
        min0, max0 = min_max0
        min1, max1 = min_max1
        if min0 < min1 and max0 > min1:
            return True
        elif min1 < min0 and max1 > min0: 
            return True
        elif max1 > max0 and min1 < min0: # 1 contains 0
            return True
        elif max0 > max1 and min0 < min1: # 0 contains 1
            return True
        else:
            return False

    def intersects(self, shape):
        """
        Returns true if this shape intersects the given shape, False otherwise.
        shape: A Shape to test for intersection.
        """
        # First check using _quick_rejection, so we don't have to do all the
        # projections for nothing.
        if self._quick_rejection(shape):
            return False

        # Check for overlap on each of the axes.
        for axis in self.axes+shape.axes:
            p0 = self.project(axis)
            p1 = shape.project(axis)
            if not self._overlap(p0, p1):
                return False
        return True


class AABB(Shape):
    """
    An axis alligned bounding box.
    """
    # AABB surface normals can be shared since they're all the same (e.g the
    # cardinal axes)
    axes = [Vec3d(1,0,0), Vec3d(0,1,0), Vec3d(0,0,1)]

    def __init__(self, cx, cy, cz, hx, hy, hz, subdivs=0):
        """
        c<x,y,z>: The location of the center of the bounding box.
        h<x,y,z>: The half lengths of the bounding box in each cardinal
        direction.
        """
        self.subdivs = subdivs
        # Get the vertices for the aabb.
        vertices = []
        for i in [cx-hx, cx+hx]:
            for j in [cy-hy, cy+hy]:
                for k in [cz-hz, cz+hz]:
                    vertices.append(Vec3d(i,j,k))
        super(AABB, self).__init__(vertices)
        self.center = Vec3d(cx,cy,cz)
        self.half_vector = Vec3d(hx,hy,hz)

    def subdivide(self):
        """
        Divides this AABB into 8 sub-AABBs. Returns a list of those.
        """
        bounding_boxes = []
        cx,cy,cz = self.center
        hx,hy,hz = self.half_vector
        x_vals = [cx-hx/2.0, cx+hx/2.0]
        y_vals = [cy-hy/2.0, cy+hy/2.0]
        z_vals = [cz-hz/2.0, cz+hz/2.0] 
        new_half_vector = [hx/2.0, hy/2.0, hz/2.0]

        # The new centers are the 8 combinations of x,y,z.
        for new_cx in x_vals:
            for new_cy in y_vals:
                for new_cz in z_vals:
                    bounding_boxes.append(AABB(new_cx, new_cy, new_cz, 
                        *new_half_vector, subdivs=self.subdivs+1))

        return bounding_boxes


class Triangle(Shape):
    """
    A trangle.
    """
    def __init__(self, x0, y0, z0, x1, y1, z1, x2, y2, z2):
        """
        <x,y,z>0: the x,y,z coordinates of the first triangle vertex.
        <x,y,z>1: the x,y,z coordinates of the second triangle vertex.
        <x,y,z>2: the x,y,z coordinates of the third triangle vertex.
        """
        # Triangle vertices.
        super(Triangle, self).__init__([Vec3d(x0,y0,z0),
                                        Vec3d(x1,y1,z1),
                                        Vec3d(x2,y2,z2)])

        self.axes = self._find_axes()

    def _find_axes(self):
        """
        Finds the axes that we'll need to test against for overlap. They
        include the triangle surface normal, and the 3 edge normals.
        """
        # Edge vectors.
        f0 = self.vertices[1] - self.vertices[0]
        f1 = self.vertices[2] - self.vertices[1]
        f2 = self.vertices[0] - self.vertices[2]

        # Surface Normal
        surf_normal = f0.cross(f1)
        surf_normal.normalize()

        # Edges x AABB normals
        normals = [surf_normal]
        for e in [f0, f1, f2]:
            for n in AABB.axes:
                n_cross_e = n.cross(e)
                # Don't want degenerate cross products
                if n_cross_e == self.zero_vector:
                    continue
                normals.append(n.cross(e))

        # Normalize the edge normals.
        for n in normals:
            n.normalize()
        return normals

# Unit Tests.
class SimpleVecTester(unittest.TestCase):
    """
    A group of unit tests for the SimpleVec class.
    """
    def setUp(self):
        self.test_vec0 = SimpleVec(1.0, 0.0, 0.0)
        self.test_vec1 = SimpleVec(0.0, 1.0, 0.0)
        self.test_vec2 = SimpleVec(0.0, 0.0, 1.0)
        self.test_vec3 = SimpleVec(1.0, 1.0, 1.0)
        self.test_vec4 = SimpleVec(2.0, 0.0, 3.0)

    def test_add(self):
        """
        test_add -- ensure v0 + v1 produces a vector with correct values.
        """
        check_vector = SimpleVec(1.0, 1.0, 0.0)
        result_vector = self.test_vec0 + self.test_vec1
        self.assertEqual(check_vector, result_vector)

    def test_sub(self):
        """
        test_sub -- ensure v0 - v1 produces a vector with correct values.
        """
        check_vector = SimpleVec(1.0, 0.0, 1.0)
        result_vector = self.test_vec3 - self.test_vec1
        self.assertEqual(check_vector, result_vector)

    def test_mult(self):
        """
        test_mult -- ensure v0*v1 yields a cross product, and v0*scalar yields
        the correct scaled vector.
        """
        check_vector_cross = SimpleVec(0.0, 0.0, 1.0)
        result_vector_cross = self.test_vec0*self.test_vec1
        self.assertEqual(check_vector_cross, result_vector_cross)

        check_vector_scalar = SimpleVec(3.0, 0.0, 0.0)
        result_vector_scalar = 3.0*self.test_vec0
        self.assertEqual(check_vector_scalar, result_vector_scalar)

    def test_dot(self):
        """
        test_dot -- ensure v0 . v1 retuns the correct scalar value.
        """
        check_value = 5.0
        result_value = self.test_vec3.dot(self.test_vec4)
        self.assertEqual(check_value, result_value)

class ShapeTester(unittest.TestCase):

    def setUp(self):
        self.test_vec0 = SimpleVec(1.0, 0.0, 0.0)
        self.test_vec1 = SimpleVec(0.0, 1.0, 0.0)
        self.test_vec2 = SimpleVec(0.0, 0.0, 1.0)
        self.test_vec3 = SimpleVec(1.0, 1.0, 1.0)
        self.test_vec4 = SimpleVec(2.0, 0.0, 3.0)
        self.test_aabb = AABB(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.test_triangle0 = Triangle(2.0, 0.9, -2.0, 
                                      -2.0, 0.9, -2.0,
                                       0.0, 0.9, 2.0)
        self.test_triangle1 = Triangle(2.0, 1.1, -2.0,
                                      -2.0, 1.1, -2.0,
                                       0.0, 1.1, 2.0)

    def test_max_values(self):
        """
        test_max_values -- ensures that the correct min and max values are
        being collected from shapes.
        """
        check_values = {'max_x':2.0, 'min_x':-2.0, 'max_y':0.9, 'min_y':0.9,
                'max_z':2.0, 'min_z':-2.0}
        for component, value in check_values.items():
            self.assertEqual(getattr(self.test_triangle0, component), 
                             check_values[component])

    def test_quick_rejection(self):
        """
        test_quick_rejection -- ensure that shapes outside of bounding values
        are rejected correctly.
        """
        self.assertFalse(self.test_aabb._quick_rejection(self.test_triangle0))
        self.assertTrue(self.test_aabb._quick_rejection(self.test_triangle1))

    def test_project(self):
        """
        test_project -- ensure that min/max values returned by projection
        are correct.
        """
        projection_axis0 = self.test_vec1
        projection_axis1 = self.test_vec2
        check_values0 = (1.1, 1.1)
        check_values1 = (-2.0, 2.0)
        self.assertEqual(self.test_triangle1.project(projection_axis0),
                         check_values0)
        self.assertEqual(self.test_triangle1.project(projection_axis1),
                         check_values1)

    def test_overlap(self):
        """
        test_overlap -- ensure that overlapping geo is correctly
        identified.
        """
        # overlap: 1 contains 0
        overlap_checks0 = [(1.1, 1.1), (-2.0, 2.0)]
        self.assertTrue(self.test_triangle1._overlap(*overlap_checks0))

        # overlap: 0 contains 1
        overlap_checks1 = [(-2.0, 2.0), (1.1, 1.1)]
        self.assertTrue(self.test_triangle1._overlap(*overlap_checks1))

        # overlap: 0 max > 1 min
        overlap_checks2 = [(0.0, 2.0), (1.1, 3.0)]
        self.assertTrue(self.test_triangle1._overlap(*overlap_checks2))

        # overlap: 1 max > 0 min
        overlap_checks3 = [(1.1, 3.0), (0.0, 2.0)]
        self.assertTrue(self.test_triangle1._overlap(*overlap_checks3))


        # no overlap.
        overlap_checks4 = [(1.1, 1.9), (2.0, 3.0)]
        self.assertFalse(self.test_triangle1._overlap(*overlap_checks4))


if __name__ == '__main__':
    unittest.main(verbosity=2)
