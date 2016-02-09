##########################################################################
##  GuiScannos provides an editor and log viewer for ppscannos output.
##  Copyright (C) 2016  Lisa Ann Hatfield
##
##  This file is part of GuiScannos.
##
##  GuiScannos is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  GuiScannos is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with GuiScannos.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################
    

import os, subprocess

from PyQt5.Qt import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QGridLayout, QHBoxLayout, 
                      QLabel, QLineEdit, QPushButton, QSettings)


def getRCFilesForDir(d):
    """Given directory d (as a string), return a list of the .rc files it contains."""
    
    #assert(d)
    rcList = []
    if not d:
        return rcList
    try:
        s = subprocess.check_output(['ls', d], universal_newlines=True)  # returns a string
        s.strip()
        lst = s.split('\n')
        #print(s)
        for f in lst:
            (base, ext) = os.path.splitext(f)
            if ext == '.rc':
                rcList.append(f)
    except subprocess.SubprocessError:
        pass
    #assert(len(rcList))
    return rcList


class ConfigDialog(QDialog):
    """Allow user to modify some persistent configuration settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineEditPPScannos = QLineEdit()
        self.lineEditPPScannos.setReadOnly(True)
        self.comboScannoFiles = QComboBox()
        
        labelPPScannosLoc = QLabel('PPScannos File')
        labelPPScannosLoc.setBuddy(self.lineEditPPScannos)
        labelScannoLoc = QLabel('Default Scanno File')
        labelScannoLoc.setBuddy(self.comboScannoFiles)

        self.buttonPPScannos = QPushButton('Change')
        self.buttonPPScannos.pressed.connect(self.openFileDlg)
        
        hbox = QHBoxLayout()
        hbox.addWidget(labelPPScannosLoc)
        hbox.addWidget(self.lineEditPPScannos)
        hbox.addWidget(self.buttonPPScannos)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        mainLayout = QGridLayout()
        mainLayout.addLayout(hbox, 0, 0, 2, 0)
        mainLayout.addWidget(labelScannoLoc, 1, 0)
        mainLayout.addWidget(self.comboScannoFiles, 1, 1)
        mainLayout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.setLayout(mainLayout)

        self.populate()
        
        self.lineEditPPScannos.textChanged.connect(self.ppscannosChanged)

        self.setWindowTitle("Configure Gui Scannos")
        self.resize(650, 400)
        
    def populate(self):
        """Fill the dialog."""
        
        settings = QSettings(self)
        ppscannos = settings.value('ppscannos', type=str)
        if not ppscannos:
            ppscannos = os.environ['HOME']
            ppscannos = ppscannos + '/ppscannos1/ppscannos1.py'
        self.lineEditPPScannos.setText(ppscannos)
        self.ppscannosChanged()
        
        defaultScanno = settings.value('defaultScannoFile', type=str)
        if defaultScanno:
            idx = self.comboScannoFiles.findText(defaultScanno)
            self.comboScannoFiles.setCurrentIndex(idx)
        #print('settings:', settings.allKeys())
        #print('\tdefault:', settings.value('defaultScannoFile'))
        
    def ppscannosChanged(self):
        self.comboScannoFiles.clear()
        ppscannos = self.lineEditPPScannos.text()
        if not ppscannos:
            return
        scannoFiles = getRCFilesForDir(os.path.dirname(ppscannos))
        if scannoFiles:
            for f in scannoFiles:
                (base, ext) = os.path.splitext(f)
                if ext == '.rc':
                    self.comboScannoFiles.addItem(f)
        idx = self.comboScannoFiles.findText('regex.rc')
        if idx != -1:
            self.comboScannoFiles.setCurrentIndex(idx)
                    
    def openFileDlg(self):
        """Open file picker for ppscannos.py file"""

        d = self.lineEditPPScannos.text()
        if d:
            d = os.path.dirname(d)

        dlg = QFileDialog(self, "Select PPScannos File...", None, "Python Files (*.py);;All Files (*)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        if dlg.exec():
            flist = dlg.selectedFiles()  # returns a list
            if len(flist):
                self.lineEditPPScannos.setText(flist[0])
