import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

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
    self.reloadButton.name = "NeedleGuideTemlpate Reload"
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
    self.inputTE1Selector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputTE1Selector.selectNodeUponCreation = True
    self.inputTE1Selector.addEnabled = False
    self.inputTE1Selector.removeEnabled = False
    self.inputTE1Selector.noneEnabled = False
    self.inputTE1Selector.showHidden = False
    self.inputTE1Selector.showChildNodeTypes = False
    self.inputTE1Selector.setMRMLScene( slicer.mrmlScene )
    self.inputTE1Selector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputTE1Selector)

    #
    # input volume selector
    #
    self.inputTE2Selector = slicer.qMRMLNodeComboBox()
    self.inputTE2Selector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputTE2Selector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputTE2Selector.selectNodeUponCreation = True
    self.inputTE2Selector.addEnabled = False
    self.inputTE2Selector.removeEnabled = False
    self.inputTE2Selector.noneEnabled = False
    self.inputTE2Selector.showHidden = False
    self.inputTE2Selector.showChildNodeTypes = False
    self.inputTE2Selector.setMRMLScene( slicer.mrmlScene )
    self.inputTE2Selector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputTE2Selector)


    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    ##
    ## check box to trigger taking screen shots for later use in tutorials
    ##
    #self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    #self.enableScreenshotsFlagCheckBox.checked = 0
    #self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    #parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

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
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputTE1Selector.currentNode() and self.inputTE1Selector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = ComputeT2StarLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputTE1Selector.currentNode(), self.inputTE2Selector.currentNode(), self.outputSelector.currentNode())

  def onReload(self, moduleName="NeedleGuideTemplate"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


#
# ComputeT2StarLogic
#

class ComputeT2StarLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def isValidInputOutputData(self, inputTE1VolumeNode, inputTE2VolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputTE1VolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for TE1 image defined')
      return False
    if not inputTE2VolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node for TE2 image defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    return True

  def run(self, inputTE1Volume, inputTE2Volume, outputVolume):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputTE1Volume, inputTE2Volume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    logging.info('Processing completed')

    return True

o
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

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = ComputeT2StarLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
