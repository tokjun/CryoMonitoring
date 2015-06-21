import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils

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
    parametersFormLayout.addRow("Upper Threshold (s): ", self.upperThresholdSpinBox)

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
    parametersFormLayout.addRow("Lower Threshold (s): ", self.lowerThresholdSpinBox)

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
    self.useThresholdFlagCheckBox.connect('toggled(bool)', self.onUseThreshold)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputTE1Selector.currentNode() and self.inputTE1Selector.currentNode() and (self.outputT2StarSelector.currentNode() or self.outputR2StarSelector.currentNode())

  def onUseThreshold(self):
    if self.useThresholdFlagCheckBox.checked == True:
      self.lowerThresholdSpinBox.enabled = True;      
      self.upperThresholdSpinBox.enabled = True;      
    else:
      self.lowerThresholdSpinBox.enabled = False;      
      self.upperThresholdSpinBox.enabled = False;      

  def onApplyButton(self):
    logic = ComputeT2StarLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #imageThreshold = self.imageThresholdSliderWidget.value
    if self.useThresholdFlagCheckBox.checked == True:
      logic.run(self.inputTE1Selector.currentNode(), self.inputTE2Selector.currentNode(),
                self.outputT2StarSelector.currentNode(), self.outputR2StarSelector.currentNode(),
                self.TE1SpinBox.value, self.TE2SpinBox.value,
                self.upperThresholdSpinBox.value, self.lowerThresholdSpinBox.value)
    else:
      logic.run(self.inputTE1Selector.currentNode(), self.inputTE2Selector.currentNode(),
                self.outputT2StarSelector.currentNode(), self.outputR2StarSelector.currentNode(),
                self.TE1SpinBox.value, self.TE2SpinBox.value)
      

  def onReload(self, moduleName="ComputeT2Star"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


#
# ComputeT2StarLogic
#

class ComputeT2StarLogic(ScriptedLoadableModuleLogic):

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

  def run(self, inputTE1VolumeNode, inputTE2VolumeNode, outputT2StarVolumeNode, outputR2StarVolumeNode, TE1, TE2, upperThreshold=None, lowerThreshold=None):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputTE1VolumeNode, inputTE2VolumeNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    imageTE1 = sitk.Cast(sitkUtils.PullFromSlicer(inputTE1VolumeNode.GetID()), sitk.sitkFloat64)
    imageTE2 = sitk.Cast(sitkUtils.PullFromSlicer(inputTE2VolumeNode.GetID()), sitk.sitkFloat64)

    if outputT2StarVolumeNode:
      imageT2Star = sitk.Divide(TE1-TE2, sitk.Log(sitk.Divide(imageTE2, imageTE1)))
      if upperThreshold or lowerThreshold:
        imageT2StarThreshold = sitk.Threshold(imageT2Star, lowerThreshold, upperThreshold, 0.0)
        sitkUtils.PushToSlicer(imageT2StarThreshold, outputT2StarVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageT2Star, outputT2StarVolumeNode.GetName(), 0, True)

    if outputR2StarVolumeNode:
      imageR2Star = sitk.Divide(sitk.Log(sitk.Divide(imageTE2, imageTE1)), TE1-TE2)
      if upperThreshold or lowerThreshold:
        imageR2StarThreshold = sitk.Threshold(imageR2Star, lowerThreshold, upperThreshold, 0.0)
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
