import maya.cmds as cmds
import random
import math
import sys

"""
STUFF OF NOTE:
cmds.polySelectConstraint(pp=1) will select connected faces, edges, verts
parent plane for buildPlanes needs to be at the origin
Using Planes: Remember to freeze transforms on the plane you're highlighting faces on
"""

random.seed(256)

class cityBlock:
    name = ""
    centerFace = ""
    parentPlane = ""
    parentMesh = ""
    faceList = []
    faceDistances = {}
    maxDistance = 0.0
    heightRange = range(1,2)
    levelRange = range(1,2)
    dropRate = 0.0
    def __init__(self):
        print "Block Created"
    def __init__(self,n):
        self.name = n
        print "Block Created, name: " + self.name
    def setParent(self, parent):
        self.parentPlane = parent
    def setDrop(self, drop):
        self.dropRate = drop
    def setCenter(self):
        self.centerFace = cmds.ls(sl=True, fl=True)[0]
        print "centerFace set to: " + self.centerFace
    def setFaces(self):
        self.faceList = getFaces()
        print "faceList set to: " + str(self.faceList)
    def setDists(self):
        self.faceDistances = getFaceDistances(self.centerFace, self.faceList)
        self.maxDistance = self.faceDistances[max(self.faceDistances, key=self.faceDistances.get)]
        print "Max Distance: " + str(self.maxDistance)
    def setRanges(self, h1, h2, l1, l2):
        self.heightRange = range(h1, h2)
        self.levelRange = range(l1,l2)
    def setMesh(self):
        self.parentMesh = getParentMesh(self.faceList[0])
    def setup(self, p, d):
        self.setRanges(3,6,2,5)
        self.setCenter()
        self.setFaces()
        self.setDists()
        self.setDrop(d)
        self.setParent(p)
        self.setMesh()

#when called with a face selected, returns the mesh that the face is a part of
def getMesh():
    face = cmds.ls(sl=True, fl=True)[0]
    shape = cmds.listRelatives(face, p=True)
    mesh = cmds.listRelatives(shape, p=True)
    return mesh

def getParentMesh(face):
    shape = cmds.listRelatives(face, p=True)
    mesh = cmds.listRelatives(shape, p=True)
    return mesh

"""********************************************************
| MIDPOINT SOLVER FUNCTIONS                               |
********************************************************"""
#given a list of vertices, gets the maximum x,y, or z value
def getMax(vertList, index):
    max = -sys.maxint
    for v in vertList:
        if v[index] > max:
            max = v[index]
    return max

#given a list of vertices, gets the minimum x,y, or z value
def getMin(vertList, index):
    min = sys.maxint
    for v in vertList:
        if v[index] < min:
            min = v[index]
    return min

#returns the midpoint of a quad.  useMinZ is a boolean that decides 
#whether the midpoint z value or the minimum z value is used.
def getMidpoint(vertList, useMinZ):
    maxX = getMax(vertList, 0); minX = getMin(vertList, 0)
    maxY = getMax(vertList, 1); minY = getMin(vertList, 1)
    maxZ = getMax(vertList, 2); minZ = getMin(vertList, 2)
    x = (maxX + minX)/2.0; y = (maxY + minY)/2.0; z = (maxZ + minZ)/2.0
    if (useMinZ): 
        z = minZ
    return [x,y,z]

"""********************************************************
| FACE DISTANCES FUNCTIONS                                |
********************************************************"""
def distBetween(v1, v2, useSquareDistance):
    x1,y1,z1 = v1; x2,y2,z2 = v2;
    squareDist = (x2-x1)**2+(y2-y1)**2+(z2-z1)**2
    if(useSquareDistance):
        return squareDist
    else:
        return math.sqrt(squareDist)

def getFaceDistances(centerFace, otherFaces):
    distDic = {}
    centerPoint = getMidpoint(makeVertList(cmds.xform(centerFace, q=True, t=True)), True)
    for f in otherFaces:
        faceMidpoint = getMidpoint(makeVertList(cmds.xform(f, q=True, t=True)), True)
        distDic[f] = distBetween(faceMidpoint, centerPoint, False)
    return distDic

#given a list of floats, returns a list of corresponding vertices
def makeVertList(numList):
    vertList = []
    numCount = len(numList)
    i = 0
    while i < numCount:
        x = numList[i]; y = numList[i+1]; z = numList[i+2]
        vert = [x,y,z]
        vertList += [vert]
        i += 3
    return vertList

"""********************************************************
| EXTRUDE PRESETS                                         |
********************************************************"""
def getFaces():
    faces = cmds.ls(sl=True, fl=True)
    return faces

def makeSidewalk(face, walkHeight):
    extrudeList(face, ['up'], [walkHeight], [])

def makeRim(face, rimHeight):
    extrudeList(face, ['out', 'up', 'in', 'down', 'in'], [rimHeight, rimHeight*0.25], [1.05, 0.95, 0.95])

def makeWell(face, wellDepth):
    extrudeList(face, ['in', 'down', 'in'], [wellDepth], [0.95, 0.95])

def makeIndent(face, indentDepth):
    extrudeList(face, ['in','up'], [indentDepth], [0.95])

def makeAntenna(face, antennaHeight):
    extrudeList(face, ['in', 'antenna'], [antennaHeight], [0.05])

"""********************************************************
| SHADER FUNCTIONS                                        |
********************************************************"""
def addShader(face, shader):
    cmds.select(face)
    cmds.polySelectConstraint(pp=1)
    selection = cmds.ls(sl=True)
    selection.remove(face)
    faces = selection[0]
    cmds.sets(faces, e=True, forceElement=shader+"SG")

def addShaderTop(face, shader):
    cmds.sets(face, e=True, forceElement=shader+"SG")

"""********************************************************
| BUILDING FUNCTIONS                                      |
********************************************************"""
#given a face and a list of extrusions ('up', 'down', 'in', 'out'), performs
#the extrudes in order using the given heights and scales
#NOTE: height for down is a positive number
def extrudeList(face, extrudes, heights, scales):
    if(len(extrudes) != len(heights) + len(scales)):
        return
    i = 0 #for heights
    j = 0 #for scales
    for e in extrudes:
        if(e == "up" or e == "down" or e == "antenna"):
            h = heights[i]
            if(e == "down"):
                h = -1.0*h
            extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude1+".localTranslateZ", h)
            if(e == "antenna"):
                cmds.setAttr(extrude1+".localScaleX", 0.5)
                cmds.setAttr(extrude1+".localScaleY", 0.5)
            i += 1
        elif(e == "in" or e == "out"):
            s = scales[j]
            extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
            cmds.setAttr(extrude1+".localScaleX", s)
            cmds.setAttr(extrude1+".localScaleY", s)
            j += 1
        else:
            print "e was not a valid extrude type"
    
def makeBuilding(face, levels, height, sidewalkHeight):
    hl = height/levels
    type = random.choice(['indent', 'rim','well'])
    makeSidewalk(face, sidewalkHeight)
    for i in range(1, levels):
        dHeight = height/(2*i)
        #extrude in
        extrude1 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
        cmds.setAttr(extrude1+".localScaleX", 0.5+(0.5*random.random())); 
        cmds.setAttr(extrude1+".localScaleY", 0.5+(0.5*random.random()));
        #extrude again and translate up
        extrude2 = cmds.polyExtrudeFacet(face, ch=1, kft=0)[0]
        cmds.setAttr(extrude2+".localTranslateZ",  dHeight)
        if type == 'indent':
            makeIndent(face, hl/10.0)
        if type == 'rim':
            makeRim(face, hl/10.0)
        if type == 'well':
            makeWell(face, hl/30.0)
        if(i == levels-1 and random.random() > 0.6):
            makeAntenna(face, dHeight/2.0)

#creates buildings on selected faces with probability 1-droprate
def buildMesh(block):
    mesh = getMesh()
    faces = block.faceList
    sidewalkHeight = max(block.heightRange)/160.0
    i = 0
    for f in faces:
        drop = block.dropRate
        if(random.random() >= drop):
            cmds.select(f)
            height = 1.0*random.choice(block.heightRange)
            levels = random.choice(block.levelRange)
            makeBuilding(f,levels, height, sidewalkHeight)
        if(not updateProgressWindow(i, len(faces))):
            break
        i += 1
        cmds.delete(mesh, constructionHistory=True)
    killProgressWindow()

#creates buildings on new planes with probablity 1-droprate
def buildPlanes(block):
    buildings = []
    faces = block.faceList
    drop = block.dropRate
    i = 0
    sidewalkHeight = max(block.heightRange)/160.0
    for f in faces:
        if(random.random() >= block.dropRate):
            height = 1.0*random.choice(block.heightRange)
            levels = random.choice(block.levelRange)
            #get the midpoint of the current face
            verts = makeVertList(cmds.xform(f, q=True, t=True))
            midpoint = getMidpoint(verts, True)
            #make a duplicate of the parent plane
            cmds.select(block.parentPlane)
            dupName = block.name + "building_"+str(i)
            dupFace = dupName + ".f[0]"
            cmds.duplicate(name=dupName)
            cmds.xform(t=midpoint)
            #create building and add it to building list
            makeBuilding(dupFace, levels, height, sidewalkHeight)
            buildings += [dupName]
            i += 1
        if(not updateProgressWindow(i, len(faces))):
            break
    cmds.group(buildings, name=block.name + "_buildings")
    killProgressWindow()

"""********************************************************
| UI FUNCTIONS                                            |
********************************************************"""
def initializeProgressWindow(t, maxSize):
    cmds.progressWindow(title=t, progress=0, max=maxSize, isInterruptable=True)

def updateProgressWindow(i, maxSize):
    if(cmds.progressWindow(q=True, ic=True)):
        return False
    else:
        cmds.progressWindow(e=True, pr=i, st=("Building: " + str(i) + "/" + str(maxSize)))
        return True

def killProgressWindow():
    cmds.progressWindow(ep=True)
    print "Build Completed"
                            

"""********************************************************
| TESTING FUNCTIONS                                       |
********************************************************"""
def testPlanes(dropRate,plane):
    blah = cityBlock("blah")
    blah.setup(plane, 0.1)
    initializeProgressWindow("Building Planes", len(blah.faceList))
    buildPlanes(blah)

def testMesh(dropRate):
    blah = cityBlock("blah")
    blah.setup("", 0.1)
    initializeProgressWindow("Building Mesh", len(blah.faceList))
    buildMesh(blah)
