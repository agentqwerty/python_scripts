#!/usr/bin/env python

# Standard imports
import math, random

# Non-standard imports
import maya.cmds as cmds

__doc__ = """
This is a library for taking a mesh and 'voxelizing' it. It will create cubes 
at each vertex, giving it a voxel like appearance.
"""

# Functions.
def baseCube(cubeName, avgEdgeLength):
    """
    Creates a cube with l,w,h equal to 1.5.*avgEdgeLength.
    """
    cmds.polyCube(name=cubeName)
    cmds.scale(1.5*avgEdgeLength, 1.5*avgEdgeLength, 1.5*avgEdgeLength, cubeName)

def scaleToEdgeLength(meshName, avgEdgeLength):
    """
    Scales the mesh to fit the unit cube (useful for minecraft style voxelizer).
    NOTE: you still have to freeze transforms.
    """
    scaleFactor = 1/(1.5*avgEdgeLength)         
    cmds.select(meshName)
    cmds.scale(scaleFactor, scaleFactor, scaleFactor)

def makeInstance(name, instanceName,  hiddenFlag):
    """
    Create an instance of name that will be called instanceName.
    hiddenFlag: If True, run a cmds.showHidden() command after duplication.
    """
    cmds.duplicate(name, name=instanceName)
    if(hiddenFlag):
        cmds.showHidden()

def parseline(file_line):
    """
    Parse a line from the obj file. If it's a vert, get the xyz values and 
    return them in a tuple.
    """
    values = file_line.split(" ")
    dataType = values[0]
    if(dataType == "v"):
        x,y,z = [float(v) for v in values[1:4]]
        return (dataType, x, y, z)
    else:
        return (dataType, 0.0, 0.0, 0.0)

def squaredDistanceBetween(v1, v2): 
    """
    Get the distance between v1 and v2 squared. We can use squared distance
    with comparisons to avoid having to do the square root.
    """
    l1 = cmds.xform(v1, q=True, t=True)
    l2 = cmds.xform(v2, q=True, t=True)
    x1,y1,z1 = l1
    x2,y2,z2 = l2
    return (x1-x2)**2+(y1-y2)**2+(z1-z2)**2

def averageEdgeLength(meshName, useRandomSample=True): 
    """
    Calculate the average edge length of the provided mesh.
    useRandomSample: If True, takes a random sampling of 10% of the verts,
    rather than using all of them, as that would take a while for hi poly models.
    """
    edges = grabEdges(meshName)                  
    numEdges = len(edges)
    n = 1
    avg = 0
    if not useRandomSample:
        print "Sampling %s edges." % numEdges
        for e in edges:
            cmds.select(e)
            cmds.ConvertSelectionToVertices()

            #fl flattens list so you get both verts instead of edge.vtx[0:1]
            verts = cmds.ls(sl=True, fl=True) 
            sample = squaredDistanceBetween(verts[0], verts[1])
            avg = ((n-1)*avg + sample)/n
            n += 1
    else:
        print "Sampling %s edges." % 0.1*numEdges
        for i in range(0, int(numEdges*0.1)): 
            e = random.choice(edges)

            # Sampling without replacement, so remove e
            edges.remove(e) 
            cmds.select(e)
            cmds.ConvertSelectionToVertices()
            verts = cmds.ls(sl=True, fl=True)
            sample = squaredDistanceBetween(verts[0], verts[1])
            avg = ((n-1)*avg + sample)/n
            n += 1
    return math.sqrt(avg)
        
        
def grabVertices(mesh):
    """
    Given a mesh, returns a list of the vertices of that mesh.
    """
    verts = []
    numVerts = cmds.polyEvaluate(mesh, v=True)
    for v in range(numVerts):
        verts += [mesh+".vtx[%s]"%v]
    return verts

def grabEdges(mesh):
    """
    Given a mesh, returns a list of the edges of that mesh.
    """
    edges = []
    numEdges = cmds.polyEvaluate(mesh, e=True)
    for e in range(numEdges):
        edges += [mesh+".e[%s]"%e]
    return edges

def voxelizeMesh(meshName, avgEdgeLength, minecraft=True):
    """
    Given a mesh and the avg edge length of that mesh, generate a set of cubes
    to 'voxelize' that mesh.
    """
    voxels = []
    voxelMap = {}
    baseCube(meshName+"base", avgEdgeLength)
    verts = grabVertices(meshName)
    vertcount = len(verts)
    initializeProgressWindow("voxelizing " + meshName, vertcount)
    print "Vertex Count: %s"%len(verts)
    i = 0

    # If minecraft style, restrict locations to integer values.
    if minecraft:
        for v in verts:
            location = cmds.xform(v, q=True, t=True)
            location = [int(location[0]), int(location[1]), int(location[2])]
            key = str(location[0])+","+str(location[1])+","+str(location[2])
            if not key in voxelMap:
                instanceName = meshName+"voxel"+str(i)
                makeInstance(meshName+"base", instanceName, True)
                cmds.xform(instanceName, t=location)
                voxels += [instanceName]
                voxelMap[key] = True
                i += 1
                if(not updateProgressWindow(i, vertcount)):
                    break
    else:
        for v in verts:
            location = cmds.xform(v, q=True, t=True)
            instanceName = meshName+"voxel"+str(i)
            makeInstance(meshName+"base",instanceName, True)
            cmds.xform(instanceName, t=location)
            voxels += [instanceName]
            i += 1
    killProgressWindow()
    cmds.group(voxels, name=meshName+"voxels")
        
def voxelizeObjFile(objectFile, groupName, intFlag, scaleFactor):
    """
    Given an objFile, 
    """
    voxMap = {}
    try:
        f = open(objectFile, 'r')
        lines = f.readlines()
    except IOError:
        return

    i = 0
    for line in lines:
        dataType, x, y, z = parseline(line)
        tx, ty, tz = [scaleFactor * t for t in [x,y,z]]
        if(intFlag):
            tx = int(tx); ty = int(ty); tz = int(tz)
        if(type != "v"):
            continue
        else:
            key = str(tx) + "," + str(ty) + "," + str(tz)
            if(not (key in voxMap.keys())):
                instanceName = groupName + "_" + "cubeInstance" + str(i)
                makeInstance("baseCube", instanceName, True)
                cmds.select(instanceName)
                cmds.xform(t=(tx,ty,tz))
                voxMap[key] = True
                i += 1
    cmds.select(groupName + "_"+"cubeInstance*")
    cmds.group(name=groupName)


# UI Functions.
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


# Main functions.
def runMaya(minecraft=False):
    """
    Runs the voxelizer using the currently selected mesh in maya.
    """
    try:
        selectedMesh = cmds.ls(sl=True)[0]
    except IndexError:
        print "No mesh selected."
        return

    # Determine whether or not to use a random sample.
    numVerts = grabVertices(selectedMesh)
    randomSample = numVerts > 10000
    avLen = averageEdgeLength(selectedMesh, useRandomSample=randomSample)

    # Scale the mesh down if minecraft style.
    if minecraft:
        scaleToEdgeLength(selectedMesh, avLen)

    # Voxelize!
    voxelizeMesh(selectedMesh, avLen, minecraft=minecraft)
