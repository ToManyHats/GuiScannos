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


import io, re, subprocess, os

import sys

from PyQt5.Qt import (Qt, QAction, QApplication, QFontDatabase, QComboBox, QFileDialog, 
                      QFileInfo, QFontComboBox, QFontInfo, QGroupBox, QKeySequence, QLabel, 
                      QMainWindow, QMenu, QMessageBox, QSettings, QSplitter, QTextCharFormat, 
                      QTextCursor, QTextDocumentWriter, QToolBar, QVBoxLayout)

from configdialog import ConfigDialog, getRCFilesForDir
from textpane import LogPane, TextPane


class MainWin(QMainWindow):
    def __init__(self, fileName=None, logName=None, parent=None):
        super(MainWin, self).__init__(parent)

        #self.setWindowIcon(QIcon(':/images/logo.png'))
        self.setToolButtonStyle(Qt.ToolButtonFollowStyle)
        self.setupFileActions()
        self.setupEditActions()
        self.setupTextActions()
        self.setupRunActions()
        self.initializeSettings()
        self.populateRunSettings()  # FIXME put in initializeSettings()?
        
        settingsMenu = QMenu('Settings', self)
        self.menuBar().addMenu(settingsMenu)
        settingsMenu.addAction('Configure...', self.configure)

        helpMenu = QMenu("Help", self)
        self.menuBar().addMenu(helpMenu)
        helpMenu.addAction("About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)
 
        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Vertical)
        self.textPane = TextPane()
        self.logPane = LogPane()
        self.logBox = QGroupBox()
        self.logBox.setFlat(True)
        vbox = QVBoxLayout()
        vbox.addWidget(self.logPane)
        self.logBox.setLayout(vbox)
        self.splitter.addWidget(self.textPane)
        self.splitter.addWidget(QLabel()) # spacer
        self.splitter.addWidget(self.logBox)
        self.setCentralWidget(self.splitter)

        self.loadSrc(fileName)
        self.loadLog(logName)
        #if logName and (-1 == self.comboLogFile.findText(logName)):
            #self.comboLogFile.addItem(logName)

        self.logPane.setFocus()
        self.fontChanged(self.textPane.font())
        self.textPane.document().modificationChanged.connect(self.actionSave.setEnabled)
        self.textPane.document().modificationChanged.connect(self.setWindowModified)
        self.textPane.document().undoAvailable.connect(self.actionUndo.setEnabled)
        self.textPane.document().redoAvailable.connect( self.actionRedo.setEnabled)
        self.setWindowModified(self.textPane.document().isModified())
        self.actionSave.setEnabled(self.textPane.document().isModified())
        self.actionUndo.setEnabled(self.textPane.document().isUndoAvailable())
        self.actionRedo.setEnabled(self.textPane.document().isRedoAvailable())
        self.actionUndo.triggered.connect(self.textPane.undo)
        self.actionRedo.triggered.connect(self.textPane.redo)
        self.actionCut.setEnabled(False)
        self.actionCopy.setEnabled(False)
        self.actionCut.triggered.connect(self.textPane.cut)
        self.actionCopy.triggered.connect(self.textPane.copy)
        self.actionPaste.triggered.connect(self.textPane.paste)
        self.textPane.copyAvailable.connect(self.actionCut.setEnabled)
        self.textPane.copyAvailable.connect(self.actionCopy.setEnabled)
        QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)
        
        self.actionRun.triggered.connect(self.scannoCheck)       
        self.logPane.lineMatchChanged.connect(self.logLineMatchChanged)

    def closeEvent(self, e):
        if self.maybeSave():
            e.accept()
        else:
            e.ignore()

    def setupFileActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("File Actions")
        self.addToolBar(tb)

        menu = QMenu("&File", self)
        self.menuBar().addMenu(menu)

        self.actionNew = QAction("&New", self, priority=QAction.LowPriority,
                shortcut=QKeySequence.New, triggered=self.fileNew)
        tb.addAction(self.actionNew)
        menu.addAction(self.actionNew)

        self.actionOpen = QAction("&Open...", self, shortcut=QKeySequence.Open,
                triggered=self.fileOpen)
        tb.addAction(self.actionOpen)
        menu.addAction(self.actionOpen)
        menu.addSeparator()

        self.actionSave = QAction("&Save", self, shortcut=QKeySequence.Save,
                triggered=self.fileSave, enabled=False)
        tb.addAction(self.actionSave)
        menu.addAction(self.actionSave)

        self.actionSaveAs = QAction("Save &As...", self, priority=QAction.LowPriority,
                shortcut=Qt.CTRL + Qt.SHIFT + Qt.Key_S, triggered=self.fileSaveAs)
        menu.addAction(self.actionSaveAs)
        menu.addSeparator()
 
        self.actionQuit = QAction("&Quit", self, shortcut=QKeySequence.Quit, triggered=self.close)
        menu.addAction(self.actionQuit)

    def setupEditActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("Edit Actions")
        self.addToolBar(tb)

        menu = QMenu("&Edit", self)
        self.menuBar().addMenu(menu)

        self.actionUndo = QAction("&Undo", self, shortcut=QKeySequence.Undo)
        tb.addAction(self.actionUndo)
        menu.addAction(self.actionUndo)

        self.actionRedo = QAction("&Redo", self, priority=QAction.LowPriority, shortcut=QKeySequence.Redo)
        tb.addAction(self.actionRedo)
        menu.addAction(self.actionRedo)
        menu.addSeparator()

        self.actionCut = QAction("Cu&t", self, priority=QAction.LowPriority, shortcut=QKeySequence.Cut)
        tb.addAction(self.actionCut)
        menu.addAction(self.actionCut)

        self.actionCopy = QAction("&Copy", self, priority=QAction.LowPriority, shortcut=QKeySequence.Copy)
        tb.addAction(self.actionCopy)
        menu.addAction(self.actionCopy)

        self.actionPaste = QAction("&Paste", self, priority=QAction.LowPriority,
                shortcut=QKeySequence.Paste, enabled=(len(QApplication.clipboard().text()) != 0))
        tb.addAction(self.actionPaste)
        menu.addAction(self.actionPaste)

    def setupTextActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("Format Actions")
        self.addToolBar(tb)

        tb = QToolBar(self)
        tb.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        tb.setWindowTitle("Format Actions")
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.addToolBar(tb)

        self.comboFont = QFontComboBox(tb)
        tb.addWidget(self.comboFont)
        self.comboFont.activated[str].connect(self.textFamily)

        self.comboSize = QComboBox(tb)
        self.comboSize.setObjectName("comboSize")
        tb.addWidget(self.comboSize)
        self.comboSize.setEditable(True)

        db = QFontDatabase()
        for size in db.standardSizes():
            self.comboSize.addItem('{}'.format(size))

        self.comboSize.activated[str].connect(self.textSize)
        self.comboSize.setCurrentIndex(self.comboSize.findText('{}'.format(QApplication.font().pointSize())))
        
    def setupRunActions(self):
        tb = QToolBar(self)
        tb.setWindowTitle("Run Actions")
        self.addToolBar(tb)

        menu = QMenu("Run", self)
        self.menuBar().addMenu(menu)

        self.actionRun = QAction(
                "&Run", self, shortcut=Qt.CTRL + Qt.Key_R)
        tb.addAction(self.actionRun)
        menu.addAction(self.actionRun)

        self.comboScannoFile = QComboBox(tb)
        self.comboScannoFile.setObjectName("comboScannoFile")
        tb.addWidget(self.comboScannoFile)
        self.comboScannoFile.setEditable(True)
        
        self.comboLogFile= QComboBox(tb)
        self.comboLogFile.setObjectName("comboLogFile")
        self.comboLogFile.setEditable(True)
        tb.addWidget(self.comboLogFile)
    
    def populateRunSettings(self):
        for f in self.scannoFiles():
            self.comboScannoFile.addItem(f)
        if self.defaultScannoFile:
            idx = self.comboScannoFile.findText(self.defaultScannoFile)
            self.comboScannoFile.setCurrentIndex(idx)

        self.comboLogFile.addItem('plog.txt')

    def loadSrc(self, src):
        if src:
            if not self.textPane.load(src):
                return False
        self.setCurrentFileName(src)
        return True

    def loadLog(self, log):
        if log:
            if not self.logPane.load(log):
                return False
            self.comboLogFile.clear()
            self.comboLogFile.addItem(log)
        else:
            self.logPane.clear()
            self.logPane.setEnabled(False)
            self.logBox.setTitle(self.tr('No log file loaded.'))
        return True
        
    def maybeSave(self):
        if not self.textPane.document().isModified():
            return True

        ret = QMessageBox.warning(self, 'GuiScannos',
                'The document has been modified.\n'
                'Do you want to save your changes?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

        if ret == QMessageBox.Save:
            return self.fileSave()

        if ret == QMessageBox.Cancel:
            return False

        return True

    def setCurrentFileName(self, fileName=''):
        self.fileName = fileName
        self.textPane.document().setModified(False)

        if not fileName:
            shownName = 'untitled.txt'
            self.actionRun.setEnabled(False)
        else:
            shownName = QFileInfo(fileName).fileName()
            self.actionRun.setEnabled(True)

        self.setWindowTitle(self.tr('{}[*] - {}'.format(shownName, 'GUI Scannos')))
        self.setWindowModified(False)

    def fileNew(self):
        if self.maybeSave():
            self.textPane.clear()
            self.loadLog(None)  # clears logPane, logBox title, etc
            self.setCurrentFileName()

    def fileOpen(self):
        fn, _ = QFileDialog.getOpenFileName(self, 'Open File...', None, 'Text Files (*.txt);;All Files (*)')
        if fn:
            self.loadSrc(fn)
            self.loadLog(None)  # clears logPane, logBox title, etc

    def fileSave(self):
        if not self.fileName:
            return self.fileSaveAs()

        return self.textpane.save(self.fileName)

    def fileSaveAs(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", None, "text files (*.txt);;All Files (*)")

        if not fn:
            return False

        self.setCurrentFileName(fn)
        return self.fileSave()

    def logLineMatchChanged(self):
        linenum = self.logPane.srcLineNum()
        col = self.logPane.srcColNum()
        s = self.logPane.srcScanno()
        self.textPane.setSelection(linenum, col, len(s))
    
    def textFamily(self, family):
        """Set font family for text and log panes."""
        
        self.textPane.setFontFamily(family)
        self.logPane.setFontFamily(family)

    def textSize(self, pointSize):
        """Set font size for text and log panes."""
        
        self.textPane.setFontPointSize(pointSize)
        self.logPane.setFontPointSize(pointSize)

    def clipboardDataChanged(self):
        self.actionPaste.setEnabled(len(QApplication.clipboard().text()) != 0)

    def about(self):
        QMessageBox.about(self, 'About', 'GUI for ppscannos.')

    def fontChanged(self, font):
        self.comboFont.setCurrentIndex(self.comboFont.findText(QFontInfo(font).family()))
        self.comboSize.setCurrentIndex(self.comboSize.findText('{}'.format(font.pointSize())))
        
    def scannoCheck(self):
        """Run ppscannos."""
        
        scannodir = os.path.dirname(self.ppscannos)
        cmd = sys.executable
        assert(cmd)
        scannoFile = self.comboScannoFile.currentText()
        if not scannoFile:
            scannoFile = self.defaultScannoFile
        scannoFile = scannodir + '/' + scannoFile
        src = self.fileName
        log = self.comboLogFile.currentText()
        if not log:
            log = './plog.txt'
        subprocess.call([cmd, self.ppscannos, '-s' + scannoFile, '-o' + log, '-i' + src])
        self.loadLog(log)
        self.logPane.setEnabled(True)
        
    def configure(self):
        """Configure application settings by way of a dialog."""
        
        dlg = ConfigDialog()
        if dlg.exec():
            self.setPPScannos(dlg.lineEditPPScannos.text())
            self.setDefaultScannoFile(dlg.comboScannoFiles.currentText())
            settings = QSettings(QApplication.organizationName(), QApplication.applicationName())
            settings.setValue('ppscannos', self.ppscannos)
            settings.setValue('defaultScannoFile', self.defaultScannoFile)

    def setPPScannos(self, s):
        self.ppscannos = s
        self.actionRun.setEnabled(self.ppscannos and os.path.exists(self.ppscannos))
        
    def scannoFiles(self):
        """Return list of .rc filenames (without path) that are in ppscannos directory."""
        
        if not self.ppscannos:
            return []
        return getRCFilesForDir(os.path.dirname(self.ppscannos))
        
    def setDefaultScannoFile(self, s):
        self.defaultScannoFile = s
        valid = False
        if self.defaultScannoFile and self.ppscannos and os.path.exists(self.ppscannos):
            if os.path.exists(os.path.dirname(self.ppscannos) + '/' + self.defaultScannoFile):
                valid = True
        self.actionRun.setEnabled(valid)
        
    def initializeSettings(self):
        """Load persistent config settings."""
        
        settings = QSettings()
        s = settings.value('ppscannos', type=str)
        if not s:
            # try the default
            s = os.path.expanduser('~') + '/ppscannos1/ppscannos1.py'
            #s = os.environ['HOME'] + '/ppscannos1/ppscannos1.py'
        self.setPPScannos(s)
        
        s = settings.value('defaultScannoFile', type=str)
        if (not s) and self.ppscannos:
            # try the default
            lst = getRCFilesForDir(os.path.dirname(self.ppscannos))
            if len(lst):
                # prefer 'regex.rc'; otherwise use the first one
                s = lst[0]
                for f in lst:
                    if f == 'regex.rc':
                        s = f
                        break
        self.setDefaultScannoFile(s)