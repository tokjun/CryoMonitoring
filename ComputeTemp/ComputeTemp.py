import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import ComputeT2Star
import LabelStatistics
import numpy

#
# ComputeTemp
#

class ComputeTemp(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ComputeTemp" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda (Brigham and Women's Hospital)"] # replace with "Firvstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This module was developed based on a template created by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# ComputeTempWidget
#

class ComputeTempWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):

    ScriptedLoadableModuleWidget.setup(self)

    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "ComputeTemp Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    ioCollapsibleButton = ctk.ctkCollapsibleButton()
    ioCollapsibleButton.text = "I/O"
    self.layout.addWidget(ioCollapsibleButton)

    # Layout within the dummy collapsible button
    ioFormLayout = qt.QFormLayout(ioCollapsibleButton)

    #
    # input volume selector
    #
    self.echo1ImageSelector = slicer.qMRMLNodeComboBox()
    self.echo1ImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.echo1ImageSelector.selectNodeUponCreation = True
    self.echo1ImageSelector.addEnabled = False
    self.echo1ImageSelector.removeEnabled = False
    self.echo1ImageSelector.noneEnabled = False
    self.echo1ImageSelector.showHidden = False
    self.echo1ImageSelector.showChildNodeTypes = False
    self.echo1ImageSelector.setMRMLScene( slicer.mrmlScene )
    self.echo1ImageSelector.setToolTip( "Pick the 1st echo image" )
    ioFormLayout.addRow("Echo 1 Image: ", self.echo1ImageSelector)

    #
    # input volume selector
    #
    self.echo2ImageSelector = slicer.qMRMLNodeComboBox()
    self.echo2ImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.echo2ImageSelector.selectNodeUponCreation = True
    self.echo2ImageSelector.addEnabled = False
    self.echo2ImageSelector.removeEnabled = False
    self.echo2ImageSelector.noneEnabled = False
    self.echo2ImageSelector.showHidden = False
    self.echo2ImageSelector.showChildNodeTypes = False
    self.echo2ImageSelector.setMRMLScene( slicer.mrmlScene )
    self.echo2ImageSelector.setToolTip( "Pick the 2nd echo image" )
    ioFormLayout.addRow("Echo 2 image: ", self.echo2ImageSelector)

    #
    # reference ROI selector
    #
    self.referenceROISelector = slicer.qMRMLNodeComboBox()
    self.referenceROISelector.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.referenceROISelector.selectNodeUponCreation = False
    self.referenceROISelector.addEnabled = True
    self.referenceROISelector.removeEnabled = True
    self.referenceROISelector.noneEnabled = True
    self.referenceROISelector.renameEnabled = True
    self.referenceROISelector.showHidden = False
    self.referenceROISelector.showChildNodeTypes = False
    self.referenceROISelector.setMRMLScene( slicer.mrmlScene )
    self.referenceROISelector.setToolTip( "Reference ROI for scaling factor and noise estimation" )
    ioFormLayout.addRow("Reference ROI: ", self.referenceROISelector)

    #
    # tempMap volume selector
    #
    self.tempMapSelector = slicer.qMRMLNodeComboBox()
    self.tempMapSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.tempMapSelector.selectNodeUponCreation = True
    self.tempMapSelector.addEnabled = True
    self.tempMapSelector.removeEnabled = True
    self.tempMapSelector.noneEnabled = True
    self.tempMapSelector.renameEnabled = True
    self.tempMapSelector.showHidden = False
    self.tempMapSelector.showChildNodeTypes = False
    self.tempMapSelector.setMRMLScene( slicer.mrmlScene )
    self.tempMapSelector.setToolTip( "Pick the 2nd echo image" )
    ioFormLayout.addRow("Output (Temp. Map): ", self.tempMapSelector)


    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    
    #
    # First TE
    #
    self.TE1SpinBox = qt.QDoubleSpinBox()
    self.TE1SpinBox.objectName = 'TE1SpinBox'
    self.TE1SpinBox.setMaximum(100.0)
    self.TE1SpinBox.setMinimum(0.0000)
    self.TE1SpinBox.setDecimals(8)
    self.TE1SpinBox.setValue(0.00007)
    self.TE1SpinBox.setToolTip("TE for Input Volume 1")
    parametersFormLayout.addRow("TE1 (s): ", self.TE1SpinBox)

    #
    # Second TE
    #
    self.TE2SpinBox = qt.QDoubleSpinBox()
    self.TE2SpinBox.objectName = 'TE2SpinBox'
    self.TE2SpinBox.setMaximum(100.0)
    self.TE2SpinBox.setMinimum(0.0000)
    self.TE2SpinBox.setDecimals(8)
    self.TE2SpinBox.setValue(0.002)
    self.TE2SpinBox.setToolTip("TE for Input Volume 2")
    parametersFormLayout.addRow("TE2 (s): ", self.TE2SpinBox)

    #
    # Scale factor for second image
    #
    self.scaleFactorSpinBox = qt.QDoubleSpinBox()
    self.scaleFactorSpinBox.objectName = 'scaleFactorSpinBox'
    self.scaleFactorSpinBox.setMaximum(10.0)
    self.scaleFactorSpinBox.setMinimum(0.0)
    self.scaleFactorSpinBox.setDecimals(8)
    self.scaleFactorSpinBox.setValue(0.8)
    self.scaleFactorSpinBox.setToolTip("Scale factor for the second echo")
    parametersFormLayout.addRow("Scale factor: ", self.scaleFactorSpinBox)

    #
    # Check box to correct noise
    #
    self.useNoiseCorrectionFlagCheckBox = qt.QCheckBox()
    self.useNoiseCorrectionFlagCheckBox.checked = 1
    self.useNoiseCorrectionFlagCheckBox.setToolTip("If checked, correct noise based on the estimated noise level.")
    parametersFormLayout.addRow("Use Noise Correction", self.useNoiseCorrectionFlagCheckBox)

    #
    # Noise Level
    #
    self.Echo1NoiseSpinBox = qt.QDoubleSpinBox()
    self.Echo1NoiseSpinBox.objectName = 'Echo1NoiseSpinBox'
    self.Echo1NoiseSpinBox.setMaximum(500.0)
    self.Echo1NoiseSpinBox.setMinimum(0.0)
    self.Echo1NoiseSpinBox.setDecimals(6)
    self.Echo1NoiseSpinBox.setValue(0.0)
    self.Echo1NoiseSpinBox.setToolTip("Noise level for 1st echo noise correction.")
    parametersFormLayout.addRow("Noise Level (Echo 1): ", self.Echo1NoiseSpinBox)

    self.Echo2NoiseSpinBox = qt.QDoubleSpinBox()
    self.Echo2NoiseSpinBox.objectName = 'Echo2NoiseSpinBox'
    self.Echo2NoiseSpinBox.setMaximum(500.0)
    self.Echo2NoiseSpinBox.setMinimum(0.0)
    self.Echo2NoiseSpinBox.setDecimals(6)
    self.Echo2NoiseSpinBox.setValue(0.0)
    self.Echo2NoiseSpinBox.setToolTip("Noise level for 1st echo noise correction.")
    parametersFormLayout.addRow("Noise Level (Echo 2): ", self.Echo2NoiseSpinBox)

    
    #
    # Echo 1/2 signal lower input threshold
    #
    self.Echo1InputThresholdSpinBox = qt.QDoubleSpinBox()
    self.Echo1InputThresholdSpinBox.objectName = 'Echo1InputThresholdSpinBox'
    self.Echo1InputThresholdSpinBox.setMaximum(65536.000)
    self.Echo1InputThresholdSpinBox.setMinimum(0.000)
    self.Echo1InputThresholdSpinBox.setDecimals(6)
    self.Echo1InputThresholdSpinBox.setValue(0.000)
    self.Echo1InputThresholdSpinBox.setToolTip("Lower input threshold for echo 1.")
    parametersFormLayout.addRow("Lower Input Threshold (Echo 1): ", self.Echo1InputThresholdSpinBox)

    self.Echo2InputThresholdSpinBox = qt.QDoubleSpinBox()
    self.Echo2InputThresholdSpinBox.objectName = 'Echo2InputThresholdSpinBox'
    self.Echo2InputThresholdSpinBox.setMaximum(65536.000)
    self.Echo2InputThresholdSpinBox.setMinimum(0.000)
    self.Echo2InputThresholdSpinBox.setDecimals(6)
    self.Echo2InputThresholdSpinBox.setValue(0.000)
    self.Echo2InputThresholdSpinBox.setToolTip("Lower input threshold for echo 2.")
    parametersFormLayout.addRow("Lower Input Threshold (Echo 2): ", self.Echo2InputThresholdSpinBox)

    self.MinT2sSpinBox = qt.QDoubleSpinBox()
    self.MinT2sSpinBox.objectName = 'MinT2sSpinBox'
    self.MinT2sSpinBox.setMinimum(1.000)
    self.MinT2sSpinBox.setMinimum(0.000)
    self.MinT2sSpinBox.setDecimals(6)
    self.MinT2sSpinBox.setValue(0.00125)
    self.MinT2sSpinBox.setToolTip("Minimum T2* for output (maximum R2* = 1 / (minimum T2*)).")
    parametersFormLayout.addRow("Minimum T2* for output (s): ", self.MinT2sSpinBox)

    #
    # Parameter A (Temp = A * R2Star + B)
    #
    self.paramASpinBox = qt.QDoubleSpinBox()
    self.paramASpinBox.objectName = 'paramASpinBox'
    self.paramASpinBox.setMaximum(100.0)
    self.paramASpinBox.setMinimum(-100.0)
    self.paramASpinBox.setDecimals(8)
    self.paramASpinBox.setValue(-0.089465444)
    self.paramASpinBox.setToolTip("TE for Input Volume 1")
    parametersFormLayout.addRow("Param A: ", self.paramASpinBox)

    #
    # Parameter B (Temp = A * R2Star + B)
    #
    self.paramBSpinBox = qt.QDoubleSpinBox()
    self.paramBSpinBox.objectName = 'paramBSpinBox'
    self.paramBSpinBox.setMaximum(100.0)
    self.paramBSpinBox.setMinimum(-100.0)
    self.paramBSpinBox.setDecimals(8)
    self.paramBSpinBox.setValue(31.06195482)
    self.paramBSpinBox.setToolTip("TE for Input Volume 2")
    parametersFormLayout.addRow("Param B: ", self.paramBSpinBox)

    #
    # Parameter B (Temp = A * R2Star + B)
    #
    self.scaleCalibrationR2sSpinBox = qt.QDoubleSpinBox()
    self.scaleCalibrationR2sSpinBox.objectName = 'scaleCalibrationR2sSpinBox'
    self.scaleCalibrationR2sSpinBox.setMaximum(1000.0)
    self.scaleCalibrationR2sSpinBox.setMinimum(0.0)
    self.scaleCalibrationR2sSpinBox.setDecimals(8)
    self.scaleCalibrationR2sSpinBox.setValue(129.565)
    self.scaleCalibrationR2sSpinBox.setToolTip("Scale Calibration")
    parametersFormLayout.addRow("Scale Clibration R2* (s^-1): ", self.scaleCalibrationR2sSpinBox)
   
    #
    # Limit value range? 
    #
    self.useOutputThresholdFlagCheckBox = qt.QCheckBox()
    self.useOutputThresholdFlagCheckBox.checked = 1
    self.useOutputThresholdFlagCheckBox.setToolTip("If checked, apply the threshold to limit the pixel value ranges.")
    parametersFormLayout.addRow("Use OutputThreshold", self.useOutputThresholdFlagCheckBox)
    
    #
    # Upper threshold - We set threshold value to limit the range of intensity 
    #
    self.upperOutputThresholdSpinBox = qt.QDoubleSpinBox()
    self.upperOutputThresholdSpinBox.objectName = 'upperOutputThresholdSpinBox'
    self.upperOutputThresholdSpinBox.setMaximum(1000000.0)
    self.upperOutputThresholdSpinBox.setMinimum(-1000000.0)
    self.upperOutputThresholdSpinBox.setDecimals(6)
    self.upperOutputThresholdSpinBox.setValue(1000000.0)
    self.upperOutputThresholdSpinBox.setToolTip("Upper threshold for the output")
    parametersFormLayout.addRow("Upper OutputThreshold: ", self.upperOutputThresholdSpinBox)

    #
    # Lower threshold - We set threshold value to limit the range of intensity 
    #
    self.lowerOutputThresholdSpinBox = qt.QDoubleSpinBox()
    self.lowerOutputThresholdSpinBox.objectName = 'lowerOutputThresholdSpinBox'
    self.lowerOutputThresholdSpinBox.setMaximum(1000000.0)
    self.lowerOutputThresholdSpinBox.setMinimum(-1000000.0)
    self.lowerOutputThresholdSpinBox.setDecimals(6)
    self.lowerOutputThresholdSpinBox.setValue(-1000000.0)
    self.lowerOutputThresholdSpinBox.setToolTip("Lower threshold for the output")
    parametersFormLayout.addRow("Lower OutputThreshold: ", self.lowerOutputThresholdSpinBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.echo1ImageSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.echo2ImageSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.referenceROISelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.tempMapSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.useOutputThresholdFlagCheckBox.connect('toggled(bool)', self.onUseOutputThreshold)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    if self.referenceROISelector.currentNode():
      self.scaleFactorSpinBox.enabled = False
    else:
      self.scaleFactorSpinBox.enabled = True

    if self.useNoiseCorrectionFlagCheckBox.checked and self.referenceROISelector.currentNode() == None:
      self.Echo1NoiseSpinBox.enabled = True
      self.Echo2NoiseSpinBox.enabled = True
    else:
      self.Echo1NoiseSpinBox.enabled = False
      self.Echo2NoiseSpinBox.enabled = False

    self.applyButton.enabled = self.echo1ImageSelector.currentNode() and self.echo1ImageSelector.currentNode() and self.tempMapSelector.currentNode()


  def onUseOutputThreshold(self):
    if self.useOutputThresholdFlagCheckBox.checked == True:
      self.lowerOutputThresholdSpinBox.enabled = True;      
      self.upperOutputThresholdSpinBox.enabled = True;      
    else:
      self.lowerOutputThresholdSpinBox.enabled = False;      
      self.upperOutputThresholdSpinBox.enabled = False;      


  def onApplyButton(self):
    logic = ComputeTempLogic()
    logic.setScaleCalibrationR2s(self.scaleCalibrationR2sSpinBox.value,
                                 self.TE1SpinBox.value, self.TE2SpinBox.value)

    outputThreshold = None
    inputThreshold = [self.Echo1InputThresholdSpinBox.value, self.Echo2InputThresholdSpinBox.value]

    minT2s = self.MinT2sSpinBox.value

    if self.useOutputThresholdFlagCheckBox.checked == True:
      outputThreshold = [self.lowerOutputThresholdSpinBox.value, self.upperOutputThresholdSpinBox.value]

    scaleFactor = self.scaleFactorSpinBox.value
    noiseLevel = None

    if self.referenceROISelector.currentNode():
      scaleFactor = logic.CalcScalingFactor(self.echo1ImageSelector.currentNode(),
                                            self.echo2ImageSelector.currentNode(),
                                            self.referenceROISelector.currentNode())
      noiseEcho1 = logic.CalcNoise(self.echo1ImageSelector.currentNode(), None,
                                   self.referenceROISelector.currentNode())
      noiseEcho2 = logic.CalcNoise(self.echo2ImageSelector.currentNode(), None,
                                   self.referenceROISelector.currentNode())
      noiseLevel = [noiseEcho1, noiseEcho2]
      self.scaleFactorSpinBox.value = scaleFactor
      self.Echo1NoiseSpinBox.value = noiseEcho1
      self.Echo2NoiseSpinBox.value = noiseEcho2
    else:
      if self.useNoiseCorrectionFlagCheckBox.checked:
        noiseLevel = [self.Echo1NoiseSpinBox.value, self.Echo2NoiseSpinBox.value]

    logic.run(self.echo1ImageSelector.currentNode(), self.echo2ImageSelector.currentNode(),
              self.tempMapSelector.currentNode(),
              self.TE1SpinBox.value, self.TE2SpinBox.value, scaleFactor,
              self.paramASpinBox.value, self.paramBSpinBox.value,
              noiseLevel, outputThreshold, inputThreshold, minT2s)

  def onReload(self, moduleName="ComputeTemp"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


#
# ComputeTempLogic
#

class ComputeTempLogic(ScriptedLoadableModuleLogic):

  def isValidInputOutputData(self, echo1ImageVolumeNode, echo2ImageVolumeNode):
    """Validates if the output is not the same as input
    """
    if not echo1ImageVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for ParamA image defined')
      return False
    if not echo2ImageVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for ParamB image defined')
      return False
    return True
  
  def setScaleCalibrationR2s(self, r2s, TE1, TE2):
    self.scaleCalibrationR2s = r2s
    self.TE1 = TE1
    self.TE2 = TE2

  def CalcNoise(self, image1Node, image2Node, ROINode):
    
    if image2Node:
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
        
      lslogic = LabelStatistics.LabelStatisticsLogic(image1Node, ROINode)
      SD = lslogic.labelStats[1,"StdDev"]
            
      return SD


  def CalcScalingFactor(self, image1Node, image2Node, ROINode):

    image1 = sitk.Cast(sitkUtils.PullFromSlicer(image1Node.GetID()), sitk.sitkFloat32)
    image2 = sitk.Cast(sitkUtils.PullFromSlicer(image2Node.GetID()), sitk.sitkFloat32)
    roiImage = sitk.Cast(sitkUtils.PullFromSlicer(ROINode.GetID()), sitk.sitkInt8)
    
    LabelStatistics = sitk.LabelStatisticsImageFilter()
    LabelStatistics.Execute(image1, roiImage)
    echo1 = LabelStatistics.GetMean(1)
    LabelStatistics.Execute(image2, roiImage)
    echo2 = LabelStatistics.GetMean(1)

    scale = echo1 / (echo2 * numpy.exp(self.scaleCalibrationR2s*(self.TE2-self.TE1)))

    return (scale)


  def run(self, echo1ImageVolumeNode, echo2ImageVolumeNode, tempMapVolumeNode, te1, te2, scaleFactor, paramA, paramB, noiseLevel, outputThreshold, inputThreshold, minT2s):
    """
    Run the actual algorithm
    """
    if not self.isValidInputOutputData(echo1ImageVolumeNode, echo2ImageVolumeNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    slicer.mrmlScene.AddNode(r2StarVolumeNode)
    r2StarVolumeNode.SetName("R2Star-temp")

    T2StarLogic = ComputeT2Star.ComputeT2StarLogic()
    T2StarLogic.run(echo1ImageVolumeNode, echo2ImageVolumeNode, None, r2StarVolumeNode, te1, te2, scaleFactor, noiseLevel, None, inputThreshold, minT2s)

    ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
    ### reset the selector.
    r2StarVolumeNode = slicer.util.getNode("R2Star-temp")

    # Get R2* image
    r2StarImage = sitk.Cast(sitkUtils.PullFromSlicer(r2StarVolumeNode.GetID()), sitk.sitkFloat64)

    #if outputThreshold!=None:
    #  mask = sitk.BinaryThreshold(r2StarImage, 0.000001, float('Inf'), 1, 0) 
    #  nmask = sitk.BinaryThreshold(r2StarImage, -10e-6, 10e-6, 1, 0) 
    #  nmask = sitk.Cast(nmask, sitk.sitkFloat64)
    #  nmask = nmask * threshold[0] # multiply lower limit

    if tempMapVolumeNode:
      imageTemp = paramA * (r2StarImage) + paramB

      if outputThreshold!=None:
        # Mask out invalid pixels (ComputeT2Star module output zero, when R2* cannot be
        # computed accurately.
        #imageTemp = sitk.Mask(imageTemp, mask)
        #imageTemp = sitk.Add(imageTemp, nmask)
        print outputThreshold
        lowerOutputThreshold = outputThreshold[0]
        upperOutputThreshold = outputThreshold[1]
        imageTempThreshold = sitk.Threshold(imageTemp, lowerOutputThreshold, upperOutputThreshold, 0.0)
        sitkUtils.PushToSlicer(imageTempThreshold, tempMapVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageTemp, tempMapVolumeNode.GetName(), 0, True)

    slicer.mrmlScene.RemoveNode(r2StarVolumeNode)
    
    logging.info('Processing completed')

    return True


class ComputeTempTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ComputeTemp1()

  def test_ComputeTemp1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    pass

    #self.delayDisplay("Starting the test")
    ##
    ## first, get some data
    ##
    #import urllib
    #downloads = (
    #    ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
    #    )
    #
    #for url,name,loader in downloads:
    #  filePath = slicer.app.temporaryPath + '/' + name
    #  if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
    #    logging.info('Requesting download %s from %s...\n' % (name, url))
    #    urllib.urlretrieve(url, filePath)
    #  if loader:
    #    logging.info('Loading %s...' % (name,))
    #    loader(filePath)
    #self.delayDisplay('Finished with download and loading')
    #
    #volumeNode = slicer.util.getNode(pattern="FA")
    #logic = ComputeTempLogic()
    #self.assertTrue( logic.hasImageData(volumeNode) )
    #self.delayDisplay('Test passed!')
