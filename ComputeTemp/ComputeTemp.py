import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import ComputeT2Star

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
    # Parameter A (Temp = A * R2Star + B)
    #
    self.paramASpinBox = qt.QDoubleSpinBox()
    self.paramASpinBox.objectName = 'paramASpinBox'
    self.paramASpinBox.setMaximum(100.0)
    self.paramASpinBox.setMinimum(-100.0)
    self.paramASpinBox.setDecimals(8)
    self.paramASpinBox.setValue(0.15798)
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
    self.paramBSpinBox.setValue(-9.92)
    self.paramBSpinBox.setToolTip("TE for Input Volume 2")
    parametersFormLayout.addRow("Param B: ", self.paramBSpinBox)
   
    #
    # Limit value range? 
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
    self.upperThresholdSpinBox.setMaximum(1000000.0)
    self.upperThresholdSpinBox.setMinimum(-1000000.0)
    self.upperThresholdSpinBox.setDecimals(6)
    self.upperThresholdSpinBox.setValue(1000000.0)
    self.upperThresholdSpinBox.setToolTip("Upper threshold for the output")
    parametersFormLayout.addRow("Upper Threshold: ", self.upperThresholdSpinBox)

    #
    # Lower threshold - We set threshold value to limit the range of intensity 
    #
    self.lowerThresholdSpinBox = qt.QDoubleSpinBox()
    self.lowerThresholdSpinBox.objectName = 'lowerThresholdSpinBox'
    self.lowerThresholdSpinBox.setMaximum(1000000.0)
    self.lowerThresholdSpinBox.setMinimum(-1000000.0)
    self.lowerThresholdSpinBox.setDecimals(6)
    self.lowerThresholdSpinBox.setValue(-1000000.0)
    self.lowerThresholdSpinBox.setToolTip("Lower threshold for the output")
    parametersFormLayout.addRow("Lower Threshold: ", self.lowerThresholdSpinBox)

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
    self.tempMapSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.useThresholdFlagCheckBox.connect('toggled(bool)', self.onUseThreshold)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.echo1ImageSelector.currentNode() and self.echo1ImageSelector.currentNode() and self.tempMapSelector.currentNode()

  def onUseThreshold(self):
    if self.useThresholdFlagCheckBox.checked == True:
      self.lowerThresholdSpinBox.enabled = True;      
      self.upperThresholdSpinBox.enabled = True;      
    else:
      self.lowerThresholdSpinBox.enabled = False;      
      self.upperThresholdSpinBox.enabled = False;      

  def onApplyButton(self):
    logic = ComputeTempLogic()
    if self.useThresholdFlagCheckBox.checked == True:
      logic.run(self.echo1ImageSelector.currentNode(), self.echo2ImageSelector.currentNode(),
                self.tempMapSelector.currentNode(),
                self.TE1SpinBox.value, self.TE2SpinBox.value, self.scaleFactorSpinBox.value,
                self.paramASpinBox.value, self.paramBSpinBox.value,
                self.upperThresholdSpinBox.value, self.lowerThresholdSpinBox.value)
    else:
      logic.run(self.echo1ImageSelector.currentNode(), self.echo2ImageSelector.currentNode(),
                self.tempMapSelector.currentNode(),
                self.TE1SpinBox.value, self.TE2SpinBox.value, self.scaleFactorSpinBox.value,
                self.paramASpinBox.value, self.paramBSpinBox.value)


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

  def run(self, echo1ImageVolumeNode, echo2ImageVolumeNode, tempMapVolumeNode, te1, te2, scaleFactor, paramA, paramB, upperThreshold=None, lowerThreshold=None):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(echo1ImageVolumeNode, echo2ImageVolumeNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    t2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    slicer.mrmlScene.AddNode(t2StarVolumeNode)
    t2StarVolumeNode.SetName("T2Star-temp")

    r2StarVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    slicer.mrmlScene.AddNode(r2StarVolumeNode)
    r2StarVolumeNode.SetName("R2Star-temp")

    T2StarLogic = ComputeT2Star.ComputeT2StarLogic()
    T2StarLogic.run(echo1ImageVolumeNode, echo2ImageVolumeNode, t2StarVolumeNode, r2StarVolumeNode, te1, te2, scaleFactor)

    ### Since PushToSlicer() called in logic.run() will delete the original node, obtain the new node and
    ### reset the selector.
    t2StarVolumeNode = slicer.util.getNode("T2Star-temp")
    r2StarVolumeNode = slicer.util.getNode("R2Star-temp")

    # Get R2* image
    r2StarImage = sitk.Cast(sitkUtils.PullFromSlicer(r2StarVolumeNode.GetID()), sitk.sitkFloat64)
 

    if tempMapVolumeNode:
      imageTemp = paramA * (r2StarImage) + paramB
      if upperThreshold or lowerThreshold:
        imageTempThreshold = sitk.Threshold(imageTemp, lowerThreshold, upperThreshold, 0.0)
        sitkUtils.PushToSlicer(imageTempThreshold, tempMapVolumeNode.GetName(), 0, True)
      else:
        sitkUtils.PushToSlicer(imageTemp, tempMapVolumeNode.GetName(), 0, True)

    slicer.mrmlScene.RemoveNode(t2StarVolumeNode)
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
