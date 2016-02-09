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
        if logName and (-1 == self.comboLogFile.findText(logName)):
            self.comboLogFile.addItem(logName)

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
        self.logPane.cursorPositionChanged.connect(self.logCursorPosChanged)

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
        settings = QSettings(self)
        ppscannos = settings.value('ppscannos', type=str)
        scannoFiles = getRCFilesForDir(os.path.dirname(ppscannos))       
        if scannoFiles:
            for f in scannoFiles:
                self.comboScannoFile.addItem(f)
        defaultScanno = settings.value('defaultScannoFile', type=str)
        if defaultScanno:
            idx = self.comboScannoFile.findText(defaultScanno)
            self.comboScannoFile.setCurrentIndex(idx)
        
        self.comboLogFile= QComboBox(tb)
        self.comboLogFile.setObjectName("comboLogFile")
        self.comboLogFile.setEditable(True)
        tb.addWidget(self.comboLogFile)
        
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
        else:
            log = 'No log file loaded.'
            self.logPane.clear()
            self.logPane.setEnabled(False)
        self.logBox.setTitle(log)
        return True
        
    def maybeSave(self):
        if not self.textPane.document().isModified():
            return True

        ret = QMessageBox.warning(self, "Application",
                "The document has been modified.\n"
                "Do you want to save your changes?",
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

        self.setWindowTitle(self.tr("{}[*] - {}".format(shownName, "GUI Scannos")))
        self.setWindowModified(False)

    def fileNew(self):
        if self.maybeSave():
            self.textPane.clear()
            self.loadLog(None)  # clears logPane, logBox title, etc
            self.setCurrentFileName()

    def fileOpen(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open File...", None, "Text Files (*.txt);;All Files (*)")
        if fn:
            self.loadSrc(fn)
            self.loadLog(None)  # clears logPane, logBox title, etc

    def fileSave(self):
        if not self.fileName:
            return self.fileSaveAs()

        writer = QTextDocumentWriter(self.fileName)
        success = writer.write(self.textPane.document())
        if success:
            self.textPane.document().setModified(False)

        return success

    def fileSaveAs(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", None,
                "text files (*.txt);;All Files (*)")

        if not fn:
            return False

        lfn = fn.lower()
        if not lfn.endswith(('.txt')):
            # The default.
            fn += '.txt'

        self.setCurrentFileName(fn)
        return self.fileSave()

    # TODO implementation should be in TextPane and LogPane. MainWin should only handle the signal/slot connection.
    def logCursorPosChanged(self):
        cursor = self.logPane.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        logline = cursor.selectedText()
        match = self.logPane.pattern.search(logline)
        if not match:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.StartOfLine)
            self.logPane.setTextCursor(cursor)
            #print('no match')
            return
        #print('matched:', match.group(0))
        self.logPane.setTextCursor(cursor)
        numstr = match.group(1)
        linenum = int(numstr)
        colstr = match.group(2)
        col = int(colstr) - 1  # 1-based in ppscanno output
        s = match.group(3)  # scanno match
        cursor = self.textPane.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, linenum-1)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, col)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(s))  # create the selection
        self.textPane.setTextCursor(cursor)
    
    # FIXME shouldn't set document modified or add too undo stack
    def textFamily(self, family):
        """Set font family for text pane."""
        
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        cursor = self.textPane.textCursor()
        self.textPane.selectAll()
        self.textPane.setFontFamily(family)
        cursor2 = self.textPane.textCursor()
        cursor2.clearSelection()
        self.textPane.setTextCursor(cursor2)
        self.textPane.setTextCursor(cursor)

    def textSize(self, pointSize):
        """Set font size for text pane."""
        
        pointSize = float(pointSize)
        if pointSize > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(pointSize)
            cursor = self.textPane.textCursor()
            self.textPane.selectAll()
            self.textPane.setFontPointSize(pointSize)
            cursor2 = self.textPane.textCursor()
            cursor2.clearSelection()
            self.textPane.setTextCursor(cursor2)
            self.textPane.setTextCursor(cursor)

    def clipboardDataChanged(self):
        self.actionPaste.setEnabled(len(QApplication.clipboard().text()) != 0)

    def about(self):
        QMessageBox.about(self, "About", "GUI for ppscannos.")

    def fontChanged(self, font):
        self.comboFont.setCurrentIndex(self.comboFont.findText(QFontInfo(font).family()))
        self.comboSize.setCurrentIndex(self.comboSize.findText('{}'.format(font.pointSize())))
        
    def scannoCheck(self):
        """Run ppscannos."""
        
        settings = QSettings(self)
        ppscannos = settings.value('ppscannos')
        assert(ppscannos)
        scannodir = os.path.dirname(ppscannos)
        cmd = '/usr/bin/python3'
        scannoFile = self.comboScannoFile.currentText()
        scannoFile = scannodir + '/' + scannoFile
        #print('scannoFile:', scannoFile)
        src = self.fileName
        log = self.comboLogFile.currentText()
        if not log:
            log = './plog.txt'
        subprocess.call([cmd, ppscannos, '-s' + scannoFile, '-o' + log, '-i' + src])
        self.loadLog(log)
        self.logPane.setEnabled(True)
        
    def configure(self):
        """Configure application settings."""
        
        dlg = ConfigDialog()
        if dlg.exec():
            settings = QSettings(QApplication.organizationName(), QApplication.applicationName())
            settings.setValue('ppscannos', dlg.lineEditPPScannos.text())
            settings.setValue('defaultScannoFile', dlg.comboScannoFiles.currentText())
