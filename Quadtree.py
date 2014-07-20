import math
from bigfloat import *

import _norm
import _angular_dist
import geom_utils as gu
import Quadtree_Utilities as utils

MAX = 70
class Quadtree(object):
    """
    Quadtree base class. Only functions that are agnostic to
    the type of coordinate system or source object used. Must
    use a subclass.
    """
    def __init__(self, xmin, ymin, xmax, ymax):
        self.top = Node(xmin, ymin, xmax, ymax)
        self.num_subdivides = 0
        self.num_insert = 0
        self.num_inserttonodes = 0
        self.num_matched = 0
        self.num_inserttoquads = 0
        self.num_nearersources = 0

    def debug(self):
        print "Number of subdivides: %d" % self.num_subdivides
        print "Inserttonode was called %d times" % self.num_inserttonodes
        print "Matched was called %d times" % self.num_matched
        print "Inserttoquad was called %d times" % self.num_inserttoquads
        print "Nearer sources was called %d times" % self.num_nearersources
        print "Insert was called %d times" % self.num_insert

    def inserttonode(self, node, source):
        self.num_inserttonodes+=1
        if len(node.contents) == MAX:
            self.subdivide(node)
        if node.q1:
            self.inserttoquad(node, source)
        else:
            # If no subquads exist add source to the list in CONTENTS element
            node.contents.append(source)

    def inserttoquad(self, node, source):
        self.num_inserttoquads+=1
        if source.x >= node.xmid:
            if source.y >= node.ymid:
                quadrant = node.q1
            else:
                quadrant = node.q4
        else:
            if source.y >= node.ymid:
                quadrant = node.q2
            else:
                quadrant = node.q3
        self.inserttonode(quadrant, source)

    def subdivide(self, node):
        self.num_subdivides+=1
        node.q1 = Node(node.xmid, node.ymid, node.xmax, node.ymax)
        node.q2 = Node(node.xmin, node.ymid, node.xmid, node.ymax)
        node.q3 = Node(node.xmin, node.ymin, node.xmid, node.ymid)
        node.q4 = Node(node.xmid, node.ymin, node.xmax, node.ymid)
        # Pop the list and insert the sources as they come off
        while node.contents:
            self.inserttoquad(node, node.contents.pop())

    def match(self, x, y):
        self.num_matched+=1
        return self.nearestsource(self, x, y)

    def nearestsource(self, tree, x, y):
        nearest = utils.Nearest(self.initial_dist(tree.top.xmax, tree.top.xmin,
                                                  tree.top.ymax, tree.top.ymin))

        interest = utils.Interest(x, y, nearest.dist, tree.top)

        self.nearersource(tree, tree.top, x, y, nearest, interest)
        return nearest.source

    def nearersource(self, tree, node, x, y, nearest, interest):
        self.num_nearersources+=1
        if gu.intersecting(node.xmin, node.xmax,
                           node.ymin, node.ymax,
                           interest.xmin, interest.xmax,
                           interest.ymin, interest.ymax):
            if node.q1 == None:
               for s in node.contents:
                    s_dist = self.norm2(s.x, s.y, x, y)
                    if s_dist < nearest.dist:
                        nearest.source = s.source
                        nearest.dist = s_dist
                        s_dist = sqrt(s_dist)
                        interest.xmin = x - s_dist
                        interest.ymin = y - s_dist
                        interest.xmax = x + s_dist
                        interest.ymax = y + s_dist
                        interest = utils.Interest.clip(tree.top)

            else:
                self.nearersource(tree, node.q1, x, y, nearest, interest)
                self.nearersource(tree, node.q2, x, y, nearest, interest)
                self.nearersource(tree, node.q3, x, y, nearest, interest)
                self.nearersource(tree, node.q4, x, y, nearest, interest)

class Node(object):
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = BigFloat(xmin)
        self.ymin = BigFloat(ymin)
        self.xmax = BigFloat(xmax)
        self.ymax = BigFloat(ymax)
        self.xmid = BigFloat((self.xmin + self.xmax)/2.0)
        self.ymid = BigFloat((self.ymin + self.ymax)/2.0)
        self.q1 = self.q2 = self.q3 = self.q4 = None
        self.contents = []

class Point(object):
    """
    The point of Point (heh.) is to have a uniform object that
    can be passed around the Quadtree. This makes for
    easy switching between equatorial and pixel coordinate
    systems or different objects.
    """
    def __init__(self, source, x, y):
        self.source = source
        self.x = BigFloat(x)
        self.y = BigFloat(y)

class ScamPixelQuadtree(Quadtree):
    def __init__(self, xmin, ymin, xmax, ymax):
        super(ScamPixelQuadtree, self).__init__(xmin, ymin, xmax, ymax)

    def insert(self, source):
        self.num_insert+=1
        self.inserttonode(self.top, Point(source, source.ximg, source.yimg))

    def norm2(self, x1, y1, x2, y2):
#        return gu.pixnorm2(x1, y1, x2, y2)
        return _norm.norm2(x1, y1, x2, y2)

    def initial_dist(self, x2, x1, y2, y1):
        return  (min(BigFloat(x2) - BigFloat(x1), BigFloat(y2) - BigFloat(y1))/1000.0)**2

class ScamEquatorialQuadtree(Quadtree):
    def __init__(self, xmin, ymin, xmax, ymax):
        super(ScamEquatorialQuadtree, self).__init__(xmin, ymin, xmax, ymax)

    def insert(self, source):
        self.num_insert+=1
        self.inserttonode(self.top, Point(source, source.ra, source.dec))

    def norm2(self, x1, y1, x2, y2):
#        return gu.equnorm2(x1, y1, x2, y2)
        return _angular_dist.angular_dist2(x1, y1, x2, y2)

    def initial_dist(self, x2, x1, y2, y1):
        return  (min(BigFloat(x2) - BigFloat(x1), BigFloat(y2) - BigFloat(y1))/100.0)**2

