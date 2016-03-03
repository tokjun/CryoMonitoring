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
import SimpleITK as sitk
import sitkUtils
import csv

import LabelStatistics
import ComputeT2Star
import ComputeTemp

lowerThreshold = -1000000.0
upperThreshold =  1000000.0

slicer.util.selectModule('LabelStatistics')

### Setup modules
#slicer.util.selectModule('ComputeT2Star')
T2StarLogic = ComputeT2Star.ComputeT2StarLogic()

#slicer.util.selectModule('ComputeTemp')
TempLogic = ComputeTemp.ComputeTempLogic()

def CalcNoise(imageDir, image1Name, image2Name, ROIName):
    
    image1File = image1Name+'.nrrd'
    image2File = image2Name+'.nrrd'
    ROIFile = ROIName+'.nrrd'
    
    if os.path.isfile(imageDir+'/'+image1File) and os.path.isfile(imageDir+'/'+image2File):
        (r, image1Node) = slicer.util.loadVolume(imageDir+'/'+image1File, {}, True)
        (r, image2Node) = slicer.util.loadVolume(imageDir+'/'+image2File, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)

        image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
        image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
        subImage = sitk.Subtract(image1, image2)
        absImage = sitk.Abs(subImage)
        
        absVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(absVolumeNode)
        absVolumeNode.SetName('abs')
        sitkUtils.PushToSlicer(absImage, absVolumeNode.GetName(), 0, True)

        absVolumeNode = slicer.util.getNode('abs')
        lslogic = LabelStatistics.LabelStatisticsLogic(absVolumeNode, ROINode)
        meanAbsDiff = lslogic.labelStats[1,"Mean"]

        slicer.mrmlScene.RemoveNode(image1Node)
        slicer.mrmlScene.RemoveNode(image2Node)
        slicer.mrmlScene.RemoveNode(ROINode)
        slicer.mrmlScene.RemoveNode(absVolumeNode)
        
        return (meanAbsDiff/math.sqrt(math.pi/2.0))
    else:
        print "ERROR: Could not calculate noise level"
        return -1.0


def CorrectNoise(inputName, outputName, noiseLevel):
    
    inputFile = inputName+'.nrrd'
    outputFile = outputName+'.nrrd'
    
    if os.path.isfile(imageDir+'/'+inputFile):
        (r, inputNode) = slicer.util.loadVolume(imageDir+'/'+inputFile, {}, True)
    
        inputImage = sitk.Cast(sitkUtils.PullFromSlicer(inputNode.GetID()), sitk.sitkFloat32)
        squareImage = sitk.Pow(inputImage, 2)
        subImage = sitk.Subtract(squareImage, noiseLevel*noiseLevel)
        correctedImage = sitk.Sqrt(subImage)

        correctedVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(correctedVolumeNode)
        correctedVolumeNode.SetName(outputName)
        sitkUtils.PushToSlicer(correctedImage, correctedVolumeNode.GetName(), 0, True)

        correctedVolumeNode = slicer.util.getNode(outputName)
        slicer.util.saveNode(correctedVolumeNode, imageDir+'/'+correctedVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(inputNode)
        slicer.mrmlScene.RemoveNode(correctedVolumeNode)

    else:
        
        print "ERROR: Could not correct noise."
        
        
def CalcR2Star(imageDir, firstEchoName, secondEchoName, t2StarName, r2StarName, TE1, TE2, scaleFactor):

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

        T2StarLogic.run(firstEchoNode, secondEchoNode, t2StarVolumeNode, r2StarVolumeNode, TE1, TE2, scaleFactor, upperThreshold, lowerThreshold)

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
    

def CalcTemp(imageDir, baselineName, referenceName, tempName, r2StarName, paramA, paramB):

    # Assume the unit for R2* data is s^-1
    # Temp = A * R2Star + B
    paramA = 0.15798
    paramB = -9.92

    baselineFile = baselineName+'.nrrd'
    referenceFile = referenceName+'.nrrd'
    print 'reading %s' % baselineFile

    if os.path.isfile(imageDir+'/'+baselineFile) and os.path.isfile(imageDir+'/'+referenceFile):
        (r, baselineNode) = slicer.util.loadVolume(imageDir+'/'+baselineFile, {}, True)
        (r, referenceNode) = slicer.util.loadVolume(imageDir+'/'+referenceFile, {}, True)

        tempVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        slicer.mrmlScene.AddNode(tempVolumeNode)
        tempVolumeNode.SetName(tempName)

        TempLogic.run(baselineR2Star, referenceR2Star, tempVolumeNode, paramA, paramB, upperThreshold, lowerThreshold)

        ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
        ### reset the selector.
        tempVolumeNode = slicer.util.getNode(tempName)
        
        slicer.util.saveNode(tempVolumeNode, imageDir+'/'+tempVolumeNode.GetName()+'.nrrd')

        slicer.mrmlScene.RemoveNode(tempVolumeNode)
        slicer.mrmlScene.RemoveNode(baselineNode)
        slicer.mrmlScene.RemoveNode(referenceNode)

        
        
def CalcScalingFactor(imageDir, echo1Name, echo2Name, ROIName):
    
    image1File = echo1Name+'.nrrd'
    image2File = echo2Name+'.nrrd'
    ROIFile = ROIName+'.nrrd'

    if os.path.isfile(imageDir+'/'+image1File) and os.path.isfile(imageDir+'/'+image2File):
        (r, image1Node) = slicer.util.loadVolume(imageDir+'/'+image1File, {}, True)
        (r, image2Node) = slicer.util.loadVolume(imageDir+'/'+image2File, {}, True)
        (r, ROINode) = slicer.util.loadVolume(imageDir+'/'+ROIFile, {}, True)

        image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
        image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
        
        #absVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
        #slicer.mrmlScene.AddNode(absVolumeNode)
        #absVolumeNode.SetName('abs')
        #sitkUtils.PushToSlicer(absImage, absVolumeNode.GetName(), 0, True)
        #absVolumeNode = slicer.util.getNode('abs')
        
        lslogic1 = LabelStatistics.LabelStatisticsLogic(image1Node, ROINode)
        mean1 = lslogic1.labelStats[1,"Mean"]

        lslogic2 = LabelStatistics.LabelStatisticsLogic(image2Node, ROINode)
        mean2 = lslogic2.labelStats[1,"Mean"]

        slicer.mrmlScene.RemoveNode(image1Node)
        slicer.mrmlScene.RemoveNode(image2Node)
        slicer.mrmlScene.RemoveNode(ROINode)

        ## NOTE: We assume the T2* in the ROI is long enough to assume that intensities in image1 and image2 are supposed to be similar.
        return (mean1/mean2)
    else:
        print "ERROR: scaling factor"
        return -1.0
    

def CalcScalingFactorBatch(imageDir, imageIndices, prefixEcho1, prefixEcho2, ROIName):

    factors = numpy.array([])

    for idx in imageIndices:
        fileEcho1 = '%s%03d' % (prefixEcho1, idx)
        fileEcho2 = '%s%03d' % (prefixEcho2, idx)
        factor = CalcScalingFactor(imageDir, fileEcho1, fileEcho2, ROIName)
        print 'Scaling factor for %s%03d.nrrd: %f' % (prefixEcho1, idx, factor)
        if factor > 0.0:
            factors = numpy.append(factors, factor)
    print 'factor = %f +/- %f' % (numpy.mean(factors), numpy.std(factors))


def LoadImageList(imageListCSV):

    imageList = [[],[]]
    with open(imageListCSV,'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            #imageList.append([int(csvreader[0]), float(csvreader[1])])
            if row != [] and row[0] != 'Se':
                imageList[0].append(int(row[0]))
                imageList[1].append(float(row[1]))
    return imageList
            

def GenerateR2StarMaps(imageDir, imageIndices, prefixEcho1, prefixEcho2, TE1, TE2, prefixT2Star, prefixR2Star, scaleFactor):

    ### Parameters
    #workingDir = '/Users/junichi/Experiments/UTE/UTE-Clinical/ISMRM2015/'
    #imageIndices = [2, 5, 7, 8, 9, 10, 11, 12]

    if TE1 == None:
        TE1 = 0.00007  ## s
    if TE2 == None:
        TE2 = 0.002    ## s
    
    for idx in imageIndices:

        print 'processing %s/%s%03d.nrrd ...' % (imageDir, prefixEcho1, idx)

        fileEcho1 = '%s%03d' % (prefixEcho1, idx)
        fileEcho2 = '%s%03d' % (prefixEcho2, idx)
        fileR2Star = '%s%03d' % (prefixR2Star, idx)
        fileT2Star = '%s%03d' % (prefixT2Star, idx)

        ### Skip noise correction for now...
        #
        #echo1Noise = CalcNoise(imageDir, 'baseline-petra-echo1', 'fz1-max-petra-echo1', 'noise-roi-label')
        #if echo1Noise < 0:
        #    echo1Noise = CalcNoise(imageDir, 'baseline-petra-echo1', 'fz2-max-petra-echo1', 'noise-roi-label')
        #
        #echo2Noise = CalcNoise(imageDir, 'baseline-petra-echo2', 'fz1-max-petra-echo2', 'noise-roi-label')
        #if echo2Noise < 0:
        #    echo2Noise = CalcNoise(imageDir, 'baseline-petra-echo2', 'fz2-max-petra-echo2', 'noise-roi-label')
        #
        #CorrectNoise('baseline-petra-echo1', 'baseline-petra-echo1-nc', echo1Noise)
        #CorrectNoise('baseline-petra-echo2', 'baseline-petra-echo2-nc', echo2Noise)
        #CorrectNoise('fz1-max-petra-echo1', 'fz1-max-petra-echo1-nc', echo1Noise)
        #CorrectNoise('fz1-max-petra-echo2', 'fz1-max-petra-echo2-nc', echo2Noise)
        #CorrectNoise('fz2-max-petra-echo1', 'fz2-max-petra-echo1-nc', echo1Noise)
        #CorrectNoise('fz2-max-petra-echo2', 'fz2-max-petra-echo2-nc', echo2Noise)

        ## Intensity clibration for echoes 1 and 2
        CalcR2Star(imageDir, fileEcho1, fileEcho2, fileT2Star, fileR2Star, TE1, TE2, scaleFactor)
