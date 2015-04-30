import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils

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
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.baselineR2StarSelector = slicer.qMRMLNodeComboBox()
    self.baselineR2StarSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.baselineR2StarSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.baselineR2StarSelector.selectNodeUponCreation = True
    self.baselineR2StarSelector.addEnabled = False
    self.baselineR2StarSelector.removeEnabled = False
    self.baselineR2StarSelector.noneEnabled = False
    self.baselineR2StarSelector.showHidden = False
    self.baselineR2StarSelector.showChildNodeTypes = False
    self.baselineR2StarSelector.setMRMLScene( slicer.mrmlScene )
    self.baselineR2StarSelector.setToolTip( "Pick the baseline R2* map" )
    parametersFormLayout.addRow("Baseline R2*: ", self.baselineR2StarSelector)

    #
    # input volume selector
    #
    self.referenceR2StarSelector = slicer.qMRMLNodeComboBox()
    self.referenceR2StarSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.referenceR2StarSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.referenceR2StarSelector.selectNodeUponCreation = True
    self.referenceR2StarSelector.addEnabled = False
    self.referenceR2StarSelector.removeEnabled = False
    self.referenceR2StarSelector.noneEnabled = False
    self.referenceR2StarSelector.showHidden = False
    self.referenceR2StarSelector.showChildNodeTypes = False
    self.referenceR2StarSelector.setMRMLScene( slicer.mrmlScene )
    self.referenceR2StarSelector.setToolTip( "Pick the reference R2* map" )
    parametersFormLayout.addRow("Reference R2*: ", self.referenceR2StarSelector)


    #
    # tempMap volume selector
    #
    self.tempMapSelector = slicer.qMRMLNodeComboBox()
    self.tempMapSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.tempMapSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.tempMapSelector.selectNodeUponCreation = True
    self.tempMapSelector.addEnabled = True
    self.tempMapSelector.removeEnabled = True
    self.tempMapSelector.noneEnabled = True
    self.tempMapSelector.renameEnabled = True
    self.tempMapSelector.showHidden = False
    self.tempMapSelector.showChildNodeTypes = False
    self.tempMapSelector.setMRMLScene( slicer.mrmlScene )
    self.tempMapSelector.setToolTip( "Pick the output temperature map." )
    parametersFormLayout.addRow("T2Star Output Volume: ", self.tempMapSelector)

    #
    # Parameter A (Temp = A * R2Star + B)
    #
    self.paramASpinBox = qt.QDoubleSpinBox()
    self.paramASpinBox.objectName = 'paramASpinBox'
    self.paramASpinBox.setMaximum(100.0)
    self.paramASpinBox.setMinimum(-100.0)
    self.paramASpinBox.setDecimals(8)
    self.paramASpinBox.setValue(0.0735)
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
    self.paramBSpinBox.setValue(-4.0588)
    self.paramBSpinBox.setToolTip("TE for Input Volume 2")
    parametersFormLayout.addRow("Param B: ", self.paramBSpinBox)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.useThresholdFlagCheckBox = qt.QCheckBox()
    self.useThresholdFlagCheckBox.checked = 1
    self.useThresholdFlagCheckBox.setToolTip("If checked, apply the threshold to limit the pixel value ranges.")
    parametersFormLayout.addRow("Use Threshold", self.useThresholdFlagCheckBox)
    
    #
    # Upper threshold - We set threshold value to limit the range of intensity 
    #
    self.upperThresholdSpinBox = qt.QDoubleSpinBox()
    self.upperThresholdSpinBox.objectName = 'upperThresholdSpinBox'
    self.upperThresholdSpinBox.setMaximum(10000.0)
    self.upperThresholdSpinBox.setMinimum(-10000.0)
    self.upperThresholdSpinBox.setDecimals(6)
    self.upperThresholdSpinBox.setValue(1000.0)
    self.upperThresholdSpinBox.setToolTip("Upper threshold for the output")
    parametersFormLayout.addRow("Upper Threshold (ms): ", self.upperThresholdSpinBox)

    #
    # Lower threshold - We set threshold value to limit the range of intensity 
    #
    self.lowerThresholdSpinBox = qt.QDoubleSpinBox()
    self.lowerThresholdSpinBox.objectName = 'lowerThresholdSpinBox'
    self.lowerThresholdSpinBox.setMaximum(10000.0)
    self.lowerThresholdSpinBox.setMinimum(-10000.0)
    self.lowerThresholdSpinBox.setDecimals(6)
    self.lowerThresholdSpinBox.setValue(-1000.0)
    self.lowerThresholdSpinBox.setToolTip("Lower threshold for the output")
    parametersFormLayout.addRow("Lower Threshold (ms): ", self.lowerThresholdSpinBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.baselineR2StarSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.referenceR2StarSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.tempMapSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.useThresholdFlagCheckBox.connect('toggled(bool)', self.onUseThreshold)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.baselineR2StarSelector.currentNode() and self.baselineR2StarSelector.currentNode() and self.tempMapSelector.currentNode()

  def onUseThreshold(self):
    if self.useThresholdFlagCheckBox.checked == True:
      self.lowerThresholdSpinBox.enabled = True;      
      self.upperThresholdSpinBox.enabled = True;      
    else:
      self.lowerThresholdSpinBox.enabled = False;      
      self.upperThresholdSpinBox.enabled = False;      

  def onApplyButton(self):
    logic = ComputeTempLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #imageThreshold = self.imageThresholdSliderWidget.value
    if self.useThresholdFlagCheckBox.checked == True:
      logic.run(self.baselineR2StarSelector.currentNode(), self.referenceR2StarSelector.currentNode(),
                self.tempMapSelector.currentNode(), self.paramASpinBox.value, self.paramBSpinBox.value,
                self.upperThresholdSpinBox.value, self.lowerThresholdSpinBox.value)
    else:
      logic.run(self.baselineR2StarSelector.currentNode(), self.referenceR2StarSelector.currentNode(),
                self.tempMapSelector.currentNode(), self.paramASpinBox.value, self.paramBSpinBox.value)
      

  def onReload(self, moduleName="ComputeTemp"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


#
# ComputeTempLogic
#

class ComputeTempLogic(ScriptedLoadableModuleLogic):

  def isValidInputOutputData(self, baselineR2StarVolumeNode, referenceR2StarVolumeNode):
    """Validates if the output is not the same as input
    """
    if not baselineR2StarVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for ParamA image defined')
      return False
    if not referenceR2StarVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for ParamB image defined')
      return False
    return True

  def run(self, baselineR2StarVolumeNode, referenceR2StarVolumeNode, tempMapVolumeNode, paramA, paramB, upperThreshold=None, lowerThreshold=None):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(baselineR2StarVolumeNode, referenceR2StarVolumeNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    imageBaseline  = sitk.Cast(sitkUtils.PullFromSlicer(baselineR2StarVolumeNode.GetID()), sitk.sitkFloat64)
    imageReference = sitk.Cast(sitkUtils.PullFromSlicer(referenceR2StarVolumeNode.GetID()), sitk.sitkFloat64)

    if tempMapVolumeNode:
      imageTemp = paramA * (imageReference - imageBaseline) + paramB
      if upperThreshold or lowerThreshold:
        imageTempThreshold = sitk.Threshold(imageTemp, lowerThreshold, upperThreshold, 0.0)
        sitkUtils.PushToSlicer(imageTempThreshold, tempMapVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageTemp, tempMapVolumeNode.GetName(), 0, True)

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
