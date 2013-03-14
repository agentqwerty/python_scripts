# Standard Imports
import random
import math
import sys

# Maya Imports
import maya.cmds as cmds

__doc__ = """
This is a library for generating random buildings from a plane in maya.
STUFF OF NOTE:
cmds.polySelectConstraint(pp=1) will select connected faces, edges, verts
parent plane for buildPlanes needs to be at the origin
Using Planes: Remember to freeze transforms on the plane you're highlighting 
faces on.
"""

# Globals
ANTENNA_CHANCE = 0.6
SPAWN_CHANCE = 0.1

# Seed those randoms!
random.seed(256)

# Classes
class CityBlock(object):
    """
    A class for encapsulating the data for a group of buildings spawned from
    a single plane. Contains methods for creating a single building, and for
    creating multiple buildings from a mesh.
    """
    def __init__(self, name, parent, faceList, 
            minHeight, maxHeight, minLevels, maxLevels):
        """
        @param name string
            The name of the block. Determines the group name in Maya.

        @param parent string
            The name of the parent mesh.

        @param minHeight float
            The minimum height of a building.

        @param maxHeight float
            The maximum height of a building.

        @param minLevels int
            The minimum number of levels a building will spawn with.

        @param maxLevels int
            The maximum number of levels a bulding will spawn with.
        """
        self.name = name
        self.centerFace = cmds.ls(sl=True, fl=True)[0]
        self.parentPlane = parent
        self.faceList = faceList
        self.parentMesh = getParentMesh(self.faceList[0])
        self.faceDistances = getFaceDistances(self.centerFace, self.faceList)
        self.maxDistance = max(self.faceDistances.values())
        self.heightRange = range(minHeight, maxHeight)
        self.levelRange = range(minLevels, maxLevels)
        self.dropRate = SPAWN_CHANCE

    def makeBuilding(self, face, levels, height, sidewalkHeight):
        """
        Creates a building frm a supplied polygon face.

        @param face string
            The face from which to create the building.
        @param levels float
            The number of levels to extrude.
        @param height float
            The total height of the building.
        @param sidewalkHeight float
            The height of the sidewalk.
        """
        hl = height/levels
        presetType = random.choice(['indent', 'rim','well'])
        self.makeSidewalk(face, sidewalkHeight)
        for i in range(1, levels):
            dHeight = height/(2*i)

            # Extrude in.
            extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude1+".localScaleX", 0.5+(0.5*random.random())); 
            cmds.setAttr(extrude1+".localScaleY", 0.5+(0.5*random.random()));

            # Extrude again and translate up.
            extrude2 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude2+".localTranslateZ",  dHeight)

            # Add a preset.
            if presetType == 'indent':
                makeIndent(face, hl/10.0)
            if presetType == 'rim':
                makeRim(face, hl/10.0)
            if presetType == 'well':
                makeWell(face, hl/30.0)

            # If we're at the top level, add an antenna.
            if(i == levels-1 and random.random() > ANTENNA_CHANCE):
                makeAntenna(face, dHeight/2.0)

    def buildMesh(self):
        """
        Creates buildings on selected faces with probability 1-dropRate.
        """
        sidewalkHeight = max(self.heightRange)/160.0
        i = 0
        for f in self.faceList:
            if random.random() >= self.dropRate:
                height = 1.0*random.choice(self.heightRange)
                levels = random.choice(self.levelRange)
                self.makeBuilding(f, levels, height, sidewalkHeight)
            if not updateProgressWindow(i, len(self.faceList)):
                break
            i += 1
            cmds.delete(self.parentMesh, constructionHistory=True)
        killProgressWindow()


    def buildPlanes(self):
        """
        Creates buildings on new planes with probability of 1-SPAWN_CHANCE
        """
        buildings = []
        i = 0
        sidewalkHeight = max(self.heightRange)/160.0
        for f in self.faceListj:
            if(random.random() >= self.dropRate):
                height = 1.0*random.choice(self.heightRange)
                levels = random.choice(self.levelRange)
                #get the midpoint of the current face
                verts = makeVertList(cmds.xform(f, q=True, t=True))
                midpoint = getMidpoint(verts, True)
                #make a duplicate of the parent plane
                cmds.select(self.parentPlane)
                dupName = self.name + "building_"+str(i)
                dupFace = dupName + ".f[0]"
                cmds.duplicate(name=dupName)
                cmds.xform(t=midpoint)
                #create building and add it to building list
                self.makeBuilding(dupFace, levels, height, sidewalkHeight)
                buildings += [dupName]
                i += 1
            if(not updateProgressWindow(i, len(self.faceList))):
                break
        cmds.group(buildings, name=self.name + "_buildings")
        killProgressWindow()


# Functions
def getParentMesh(face):
    """
    Returns the parent mesh of the face.
    """
    shape = cmds.listRelatives(face, p=True)
    mesh = cmds.listRelatives(shape, p=True)
    return mesh

#********************************************************
# MIDPOINT SOLVER FUNCTIONS                             |
#********************************************************
def getMax(vertList, index):
    """
    Given a list of vertices, gets the maximum x,y, or z value
    """
    max = -sys.maxint
    for v in vertList:
        if v[index] > max:
            max = v[index]
    return max

def getMin(vertList, index):
    """
    Given a list of vertices, gets the minimum x,y, or z value
    """
    min = sys.maxint
    for v in vertList:
        if v[index] < min:
            min = v[index]
    return min

def getMidpoint(vertList, useMinZ):
    """
    Returns the midpoint of a quad.  useMinZ is a boolean that decides 
    whether the midpoint z value or the minimum z value is used.
    """
    maxX = getMax(vertList, 0); minX = getMin(vertList, 0)
    maxY = getMax(vertList, 1); minY = getMin(vertList, 1)
    maxZ = getMax(vertList, 2); minZ = getMin(vertList, 2)
    x = (maxX + minX)/2.0; y = (maxY + minY)/2.0; z = (maxZ + minZ)/2.0
    if (useMinZ): 
        z = minZ
    return [x,y,z]

#********************************************************
# FACE DISTANCE FUNCTIONS                               |
#********************************************************
def distBetween(v1, v2, useSquareDistance=False):
    """
    Returns the distance between v1 and v2, or the distance squared if 
    useSquareDistance is True.
    """
    x1,y1,z1 = v1; x2,y2,z2 = v2;
    squareDist = (x2-x1)**2+(y2-y1)**2+(z2-z1)**2
    if useSquareDistance:
        return squareDist
    else:
        return math.sqrt(squareDist)

def getFaceDistances(centerFace, otherFaces):
    """
    Gets the distance between the centerFace and each of the faces in the
    otherFaces list.
    """
    distDict = {}
    centerPoint = getMidpoint(makeVertList(cmds.xform(centerFace, 
        q=True, t=True)), True)
    for f in otherFaces:
        faceMidpoint = getMidpoint(makeVertList(cmds.xform(f, 
            q=True, t=True)), True)
        distDict[f] = distBetween(faceMidpoint, centerPoint, False)
    return distDict

def makeVertList(numList):
    """
    Given a list of floats, returns a list of corresponding vertices.
    """
    vertList = []
    numCount = len(numList)
    i = 0
    while i < numCount:
        x = numList[i]; y = numList[i+1]; z = numList[i+2]
        vert = [x,y,z]
        vertList += [vert]
        i += 3
    return vertList


#********************************************************
# EXTRUDE PRESETS                                       |
#********************************************************
def getFaces():
    """
    Returns a list of currently selected faces.
    """
    faces = cmds.ls(sl=True, fl=True)
    return faces

def makeSidewalk(face, walkHeight):
    """
    Creates a sidewalk from the given face of height walkHeight.
    """
    extrudeList(face, ['up'], [walkHeight], [])

def makeRim(face, rimHeight):
    """
    Creates a building rim on face of height rimHeight
    """
    extrudeList(face, ['out', 'up', 'in', 'down', 'in'], [rimHeight, rimHeight*0.25], [1.05, 0.95, 0.95])

def makeWell(face, wellDepth):
    """
    Creates a building well on face of depth wellDepth
    """
    extrudeList(face, ['in', 'down', 'in'], [wellDepth], [0.95, 0.95])

def makeIndent(face, indentDepth):
    """
    Creates an indent in face of depth indentDepth.
    """
    extrudeList(face, ['in','up'], [indentDepth], [0.95])

def makeAntenna(face, antennaHeight):
    """
    Creates an antenna on face of height antennaHeight.
    """
    extrudeList(face, ['in', 'antenna'], [antennaHeight], [0.05])


#********************************************************
# SHADER FUNCTIONS                                      |
#********************************************************
def addShader(face, shader):
    """
    Adds shader to the given face.

    @param face string
        A polygon face.
    @param shader string
        The shader to apply.
    """
    cmds.select(face)
    cmds.polySelectConstraint(pp=1)
    selection = cmds.ls(sl=True)
    selection.remove(face)
    faces = selection[0]
    cmds.sets(faces, e=True, forceElement=shader+"SG")

def addShaderTop(face, shader):
    """
    Add a shader to the top of a face
    """
    cmds.sets(face, e=True, forceElement=shader+"SG")


#********************************************************
# BUILDING FUNCTIONS                                    |
#********************************************************
def extrudeList(face, extrudes, heights, scales):
    """
    Given a face and a list of extrusions, performs the extrudes in order,
    applying the given heights and scales. NOTE: The height for down is a
    positive number.

    @param face string
        The start face to extrude.
    @param extrudes list
        A list containing extrude keywords to apply to face.
    @param heights list
        A list of height values corresponding to 'up' or 'down' extrusion 
        keywords.
    @param scales list
        A list of scale values corresponding to 'out' and 'in' keywords.
    """
    if len(extrudes) != len(heights) + len(scales):
        return
    heightIndex = 0
    scaleIndex = 0
    for e in extrudes:
        if e in ["up", "down", "antenna"]:
            h = heights[heightIndex]
            if e == "down":
                h = -1.0*h
            extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude1+".localTranslateZ", h)
            if e == "antenna":
                cmds.setAttr(extrude1+".localScaleX", 0.5)
                cmds.setAttr(extrude1+".localScaleY", 0.5)
            heightIndex += 1
        elif e in ["in", "out"]:
            s = scales[scaleIndex]
            extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude1+".localScaleX", s)
            cmds.setAttr(extrude1+".localScaleY", s)
            scaleIndex += 1
        else:
            print "e was not a valid extrude type"


#creates buildings on new planes with probablity 1-droprate

#********************************************************
# UI FUNCTIONS                                          |
#********************************************************
def initializeProgressWindow(t, maxSize):
    cmds.progressWindow(title=t, progress=0, max=maxSize, isInterruptable=True)

def updateProgressWindow(i, maxSize):
    if(cmds.progressWindow(q=True, ic=True)):
        return False
    else:
        cmds.progressWindow(e=True, pr=i, st=("Building: " +
            str(i) + "/" + str(maxSize)))
        return True

def killProgressWindow():
    cmds.progressWindow(ep=True)
    print "Build Completed"
                            

#********************************************************
# TESTING FUNCTIONS                                     |
#********************************************************
"""def testPlanes(dropRate,plane):
    blah = cityBlock("blah")
    blah.setup(plane, 0.1)
    initializeProgressWindow("Building Planes", len(blah.faceList))
    buildPlanes(blah)

def testMesh(dropRate):
    blah = cityBlock("blah")
    blah.setup("", 0.1)
    initializeProgressWindow("Building Mesh", len(blah.faceList))
    buildMesh(blah)"""
