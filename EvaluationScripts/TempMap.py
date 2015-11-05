import os
import os.path
import unittest
import random
import math
import tempfile
import time
import numpy
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *


### Parameters
workingDir = '/Users/junichi/Experiments/UTE/UTE-Clinical/ISMRM2015/'

TE1 = 0.00007  ## s
TE2 = 0.002    ## s
lowerThreshold = -1000000.0
upperThreshold =  1000000.0

# Assume the unit for R2* data is s^-1
# Temp = A * R2Star + B
paramA = 0.15798
paramB = -9.92

imageIndeces = [2, 5, 7, 8, 9, 10, 11, 12, 13]

### Setup modules
slicer.util.selectModule('ComputeT2Star')
T2StarLogic = ComputeT2StarLogic()

slicer.util.selectModule('ComputeTemp')
TempLogic = ComputeTempLogic()

def CalcR2Star(imageDir, firstEchoName, secondEchoName, t2StarName, r2StarName):

    firstEchoFile = firstEchoName+'.nrrd'
    secondEchoFile = secondEchoName+'.nrrd'
    print 'reading %s' % firstEchoFile

    if os.path.isfile(imageDir+'/'+firstEchoFile) and os.path.isfile(imageDir+'/'+secondEchoFile):
        (r, firstEchoNode) = slicer.util.loadVolume(imageDir+'/'+firstEchoFile, {}, True)
        (r, secondEchoNode) = slicer.util.loadVolume(imageDir+'/'+secondEchoFile, {}, True)

        t2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(t2StarVolumeNode)
        t2StarVolumeNode.SetName(t2StarName)

        r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(r2StarVolumeNode)
        r2StarVolumeNode.SetName(r2StarName)

        T2StarLogic.run(firstEchoNode, secondEchoNode, t2StarVolumeNode, r2StarVolumeNode,
                        TE1, TE2, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        t2StarVolumeNode = slicer.util.getNode(t2StarName)
        r2StarVolumeNode = slicer.util.getNode(r2StarName)
        
        slicer.util.saveNode(t2StarVolumeNode, imageDir+'/'+t2StarVolumeNode.GetName()+'.nrrd')
        slicer.util.saveNode(r2StarVolumeNode, imageDir+'/'+r2StarVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(t2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(r2StarVolumeNode)
        slicer.mrmlScene.RemoveNode(firstEchoNode)
        slicer.mrmlScene.RemoveNode(secondEchoNode)
    


def CalcR2Star(imageDir, baselineName, referenceName, tempName, r2StarName):

    baselineFile = baselineName+'.nrrd'
    referenceFile = referenceName+'.nrrd'
    print 'reading %s' % baselineFile

    if os.path.isfile(imageDir+'/'+baselineFile) and os.path.isfile(imageDir+'/'+referenceFile):
        (r, baselineNode) = slicer.util.loadVolume(imageDir+'/'+baselineFile, {}, True)
        (r, referenceNode) = slicer.util.loadVolume(imageDir+'/'+referenceFile, {}, True)

        tempVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(tempVolumeNode)
        tempVolumeNode.SetName(tempName)

        TempLogic.run(baselineR2Star, referenceR2Star,
                      tempVolumeNode, paramA, paramB, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(baselineNode)
        slicer.mrmlScene.RemoveNode(referenceNode)



for idx in imageIndeces:

    imageDir = '%s/cryo-%03d/' % (workingDir, idx)
    CalcR2Star(imageDir, 'baseline-petra-echo1', 'baseline-petra-echo2', 'baseline-t2s', 'baseline-r2s')
    CalcR2Star(imageDir, 'fz1-max-petra-echo1', 'fz1-max-petra-echo2', 'fz1-max-t2s', 'fz1-max-r2s')
    CalcR2Star(imageDir, 'fz2-max-petra-echo1', 'fz2-max-petra-echo2', 'fz2-max-t2s', 'fz2-max-r2s')

