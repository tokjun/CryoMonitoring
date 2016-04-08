import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import math

#
# ComputeT2Star
#

class ComputeT2Star(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ComputeT2Star" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda (Brigham and Women's Hospital)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This module was developed based on a template created by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# ComputeT2StarWidget
#

class ComputeT2StarWidget(ScriptedLoadableModuleWidget):
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
    self.reloadButton.name = "ComputeT2Star Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputTE1Selector = slicer.qMRMLNodeComboBox()
    self.inputTE1Selector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputTE1Selector.selectNodeUponCreation = True
    self.inputTE1Selector.addEnabled = True
    self.inputTE1Selector.removeEnabled = True
    self.inputTE1Selector.noneEnabled = True
    self.inputTE1Selector.renameEnabled = True
    self.inputTE1Selector.showHidden = False
    self.inputTE1Selector.showChildNodeTypes = False
    self.inputTE1Selector.setMRMLScene( slicer.mrmlScene )
    self.inputTE1Selector.setToolTip( "Pick the first volume" )
    parametersFormLayout.addRow("Input Volume 1: ", self.inputTE1Selector)

    #
    # input volume selector
    #
    self.inputTE2Selector = slicer.qMRMLNodeComboBox()
    self.inputTE2Selector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputTE2Selector.selectNodeUponCreation = True
    self.inputTE2Selector.addEnabled = True
    self.inputTE2Selector.removeEnabled = True
    self.inputTE2Selector.noneEnabled = True
    self.inputTE2Selector.renameEnabled = True
    self.inputTE2Selector.showHidden = False
    self.inputTE2Selector.showChildNodeTypes = False
    self.inputTE2Selector.setMRMLScene( slicer.mrmlScene )
    self.inputTE2Selector.setToolTip( "Pick the second volume" )
    parametersFormLayout.addRow("Input Volume 2: ", self.inputTE2Selector)

    #
    # outputT2Star volume selector
    #
    self.outputT2StarSelector = slicer.qMRMLNodeComboBox()
    self.outputT2StarSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputT2StarSelector.selectNodeUponCreation = True
    self.outputT2StarSelector.addEnabled = True
    self.outputT2StarSelector.removeEnabled = True
    self.outputT2StarSelector.noneEnabled = True
    self.outputT2StarSelector.renameEnabled = True
    self.outputT2StarSelector.showHidden = False
    self.outputT2StarSelector.showChildNodeTypes = False
    self.outputT2StarSelector.setMRMLScene( slicer.mrmlScene )
    self.outputT2StarSelector.setToolTip( "Pick the T2Star output volume." )
    parametersFormLayout.addRow("T2Star Output Volume: ", self.outputT2StarSelector)

    #
    # outputR2Star volume selector
    #
    self.outputR2StarSelector = slicer.qMRMLNodeComboBox()
    self.outputR2StarSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputR2StarSelector.selectNodeUponCreation = True
    self.outputR2StarSelector.addEnabled = True
    self.outputR2StarSelector.removeEnabled = True
    self.outputR2StarSelector.noneEnabled = True
    self.outputR2StarSelector.renameEnabled = True
    self.outputR2StarSelector.showHidden = False
    self.outputR2StarSelector.showChildNodeTypes = False
    self.outputR2StarSelector.setMRMLScene( slicer.mrmlScene )
    self.outputR2StarSelector.setToolTip( "Pick the R2Star output volume." )
    parametersFormLayout.addRow("R2Star Output Volume: ", self.outputR2StarSelector)

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
    # Scaling Factor
    #
    self.ScaleSpinBox = qt.QDoubleSpinBox()
    self.ScaleSpinBox.objectName = 'ScaleSpinBox'
    self.ScaleSpinBox.setMaximum(10.000)
    self.ScaleSpinBox.setMinimum(0.000)
    self.ScaleSpinBox.setDecimals(8)
    self.ScaleSpinBox.setValue(1.000)
    self.ScaleSpinBox.setToolTip("Scaling factor to adjust magnitude of volume 2.")
    parametersFormLayout.addRow("Scaling Factor: ", self.ScaleSpinBox)

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
    # check box to use threshold
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
    parametersFormLayout.addRow("Upper OutputThreshold (s): ", self.upperOutputThresholdSpinBox)

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
    parametersFormLayout.addRow("Lower OutputThreshold (s): ", self.lowerOutputThresholdSpinBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputTE1Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputTE2Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputT2StarSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputR2StarSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.useOutputThresholdFlagCheckBox.connect('toggled(bool)', self.onUseOutputThreshold)
    self.useNoiseCorrectionFlagCheckBox.connect('toggled(bool)', self.onUseNoiseCorrection)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputTE1Selector.currentNode() and self.inputTE1Selector.currentNode() and (self.outputT2StarSelector.currentNode() or self.outputR2StarSelector.currentNode())

  def onUseOutputThreshold(self):
    if self.useOutputThresholdFlagCheckBox.checked == True:
      self.lowerOutputThresholdSpinBox.enabled = True;      
      self.upperOutputThresholdSpinBox.enabled = True;      
    else:
      self.lowerOutputThresholdSpinBox.enabled = False;      
      self.upperOutputThresholdSpinBox.enabled = False;

  def onUseNoiseCorrection(self):
    if self.useNoiseCorrectionFlagCheckBox.checked == True:
      self.Echo1NoiseSpinBox.enabled = True;
      self.Echo2NoiseSpinBox.enabled = True;      
    else:
      self.Echo1NoiseSpinBox.enabled = False;
      self.Echo2NoiseSpinBox.enabled = False;      
    

  def onApplyButton(self):
    logic = ComputeT2StarLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #imageOutputThreshold = self.imageOutputThresholdSliderWidget.value
    t2name = ''
    r2name = ''
    if self.outputT2StarSelector.currentNode():
      t2name = self.outputT2StarSelector.currentNode().GetName()
    if self.outputR2StarSelector.currentNode():
      r2name = self.outputR2StarSelector.currentNode().GetName()
      
    inputThreshold = [self.Echo1InputThresholdSpinBox.value, self.Echo2InputThresholdSpinBox.value]
    
    minT2s = self.MinT2sSpinBox.value
    
    outputThreshold = None
    if self.useOutputThresholdFlagCheckBox.checked == True:
      outputThreshold = [self.upperOutputThresholdSpinBox.value, self.lowerOutputThresholdSpinBox.value]
      
    noiseLevel = None
    if self.useNoiseCorrectionFlagCheckBox.checked == True:
      noiseLevel = [self.Echo1NoiseSpinBox.value, self.Echo2NoiseSpinBox.value]
    
    logic.run(self.inputTE1Selector.currentNode(), self.inputTE2Selector.currentNode(),
              self.outputT2StarSelector.currentNode(), self.outputR2StarSelector.currentNode(),
              self.TE1SpinBox.value, self.TE2SpinBox.value, self.ScaleSpinBox.value,
              noiseLevel, outputThreshold, inputThreshold, minT2s)

    ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
    ### reset the selector.
    t2Node = slicer.util.getNode(t2name)
    r2Node = slicer.util.getNode(r2name)
    self.outputT2StarSelector.setCurrentNode(t2Node)
    self.outputR2StarSelector.setCurrentNode(r2Node)

  def onReload(self, moduleName="ComputeT2Star"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


#
# ComputeT2StarLogic
#

class ComputeT2StarLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
  
  def isValidInputOutputData(self, inputTE1VolumeNode, inputTE2VolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputTE1VolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for TE1 image defined')
      return False
    if not inputTE2VolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for TE2 image defined')
      return False
    return True

  def run(self, inputTE1VolumeNode, inputTE2VolumeNode, outputT2StarVolumeNode, outputR2StarVolumeNode, TE1, TE2, scaleFactor, noiseLevel, outputThreshold, inputThreshold, minT2s):
    """
    Run the actual algorithm
    """

    echo1NoiseLevel = 0.0
    echo2NoiseLevel = 0.0
    upperOutputThreshold = 0.0
    lowerOutputThreshold = 0.0

    if not self.isValidInputOutputData(inputTE1VolumeNode, inputTE2VolumeNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    imageTE1 = sitk.Cast(sitkUtils.PullFromSlicer(inputTE1VolumeNode.GetID()), sitk.sitkFloat64)
    imageTE2 = sitk.Cast(sitkUtils.PullFromSlicer(inputTE2VolumeNode.GetID()), sitk.sitkFloat64)

    # Noise correction
    # Echo 1
    if noiseLevel != None:
      echo1NoiseLevel = noiseLevel[0]
      echo2NoiseLevel = noiseLevel[1]

      squareImage1 = sitk.Pow(imageTE1, 2)
      subImage1 = sitk.Subtract(squareImage1, echo1NoiseLevel*echo1NoiseLevel)
      subImagePositive1 = sitk.OutputThreshold(subImage1,0.0, float('Inf'), 0.0)
      imageTE1 = sitk.Sqrt(subImagePositive1)

      squareImage2 = sitk.Pow(imageTE2, 2)
      subImage2 = sitk.Subtract(squareImage2, echo2NoiseLevel*echo2NoiseLevel)
      subImagePositive2 = sitk.OutputThreshold(subImage2,0.0, float('Inf'), 0.0)
      imageTE2 = sitk.Sqrt(subImagePositive2)
    else:
      # Simply remove negative values (not needed?)
      imageTE1 = sitk.Threshold(imageTE1,0.0, float('Inf'), 0.0)
      imageTE2 = sitk.Threshold(imageTE2,0.0, float('Inf'), 0.0)

    ## Apply scaling factor to the second echo
    imageTE2 = sitk.Multiply(imageTE2, scaleFactor)

    ## Create mask to exclude invalid pixels
    #  Criteria for validation
    #   1. First or second echo signal is less than the input threshold
    #   2. Second echo signal is greater than the first
    mask1 = sitk.BinaryThreshold(imageTE1, inputThreshold[0], float('Inf'), 1, 0) 
    mask2 = sitk.BinaryThreshold(imageTE2, inputThreshold[1], float('Inf'), 1, 0) 
    mask3 = sitk.Greater(imageTE2, imageTE1, 1, 0)
    mask = sitk.And(mask1, mask2)
    mask = sitk.And(mask, mask3)

    imask = sitk.Not(mask)
    imaskFloat = sitk.Cast(imask, sitk.sitkFloat64)
    imaskFillT2s = imaskFloat * minT2s
    imaskFillR2s = 0.0
    if minT2s > 0:
      imaskFillR2s = imaskFloat * (1/minT2s)

    if outputThreshold != None:
      upperOutputThreshold = outputThreshold[0]
      lowerOutputThreshold = outputThreshold[1]

    if outputT2StarVolumeNode:
      imageT2Star = sitk.Divide(TE1-TE2, sitk.Log(sitk.Divide(imageTE2, imageTE1)))
      imageT2Star = sitk.Mask(imageT2Star, mask)
      imageT2Star = sitk.Add(imageT2Star, imaskFillT2s)
      if outputThreshold != None:
        imageT2StarThreshold = sitk.Threshold(imageT2Star, lowerOutputThreshold, upperOutputThreshold, 0.0)
        sitkUtils.PushToSlicer(imageT2StarThreshold, outputT2StarVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageT2Star, outputT2StarVolumeNode.GetName(), 0, True)

    if outputR2StarVolumeNode:
      imageR2Star = sitk.Divide(sitk.Log(sitk.Divide(imageTE2, imageTE1)), TE1-TE2)
      imageR2Star = sitk.Mask(imageR2Star, mask)
      imageR2Star = sitk.Add(imageR2Star, imaskFillR2s)
      if outputThreshold != None:
        imageR2StarThreshold = sitk.Threshold(imageR2Star, lowerOutputThreshold, upperOutputThreshold, 0.0)
        sitkUtils.PushToSlicer(imageR2StarThreshold, outputR2StarVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageR2Star, outputR2StarVolumeNode.GetName(), 0, True)

    logging.info('Processing completed')

    return True


class ComputeT2StarTest(ScriptedLoadableModuleTest):
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
    self.test_ComputeT2Star1()

  def test_ComputeT2Star1(self):
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
    #logic = ComputeT2StarLogic()
    #self.assertTrue( logic.hasImageData(volumeNode) )
    #self.delayDisplay('Test passed!')
