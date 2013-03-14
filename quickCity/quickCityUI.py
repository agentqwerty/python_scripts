# Standard Imports
import sys, os, re

# Qt Imports
from PyQt4 import QtCore, QtGui, uic
from PyQt.QtCore import pyqtSlot

# Non-standard Imports
import quickCity

# Globals
FILE_PATH = os.path.dirname(__file__)

# Classes
class QuickCityWindow(object):
    """
    The main window.
    """
    def __init__(self):
        super(QuickCityWindow, self).__init__()
        self.ui = uic.loadUi(os.path.join(FILE_PATH, 'quickCity.ui'))

        # Connect UI to controller functions.
        self.connectSignalsToSlots()

    def connectSignalsToSlots(self):
        """
        Connects UI elements to their slot functions.
        """
        pass

    @pyqtSlot()
    def submitClicked(self):
        """
        Called if the submit button is clicked.
        """
        pass


# Functions
WINDOW = None
def runMaya():
    """
    Launch the window in Maya.
    """
    import maya.cmds as cmds

    global WINDOW
    if not WINDOW:
        WINDOW = QuickCityWindow()
    WINDOW.ui.show()


