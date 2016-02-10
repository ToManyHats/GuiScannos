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


import re

from PyQt5.Qt import pyqtSignal, Qt, QFile, QFrame, QTextCursor, QTextEdit


class TextPane(QTextEdit):
    """Text editor window."""
    
    def __init__(self, parent=None):
        super(TextPane, self).__init__(parent)

        self.setFrameStyle(QFrame.StyledPanel)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)
        
    def load(self, f):
        if not QFile.exists(f):
            return False
        data = open(f, 'r').read()
        self.setPlainText(data)
        return True
    
    def setSelection(self, row, col, count):
        """Select count characters, beginning at (row, col)."""
        
        cursor = self.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, row-1)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, col)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, count)  # create the selection
        self.setTextCursor(cursor)        

class LogPane(TextPane):
    """Log viewer window."""
    
    lineMatchChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(TextPane, self).__init__(parent)

        # pattern for finding line numbers in log file
        # match groups are linenum, col, and scanno
        self.pattern = re.compile(r"^\s\sLine\s#=(\d+)(?:-\d+)?\spos=(\d+)\smatch=(.+)\s*$")
        self.currentMatch = None
               
        self.cursorPositionChanged.connect(self.updateMatch)

    def keyPressEvent(self, e):
        """Up and down arrows move cursor to next row that has line and column info and highlights it."""
        
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Down:
            #print('down arrow pressed')
            cursor = self.textCursor()
            while not cursor.atEnd():
                cursor.select(QTextCursor.LineUnderCursor)
                match = self.pattern.search(cursor.selectedText())
                if match:
                    break
                cursor.clearSelection()
                cursor.movePosition(QTextCursor.Down)
                cursor.movePosition(QTextCursor.StartOfLine)
            self.setTextCursor(cursor)
        elif e.key() == Qt.Key_Up:
            #print('up arrow pressed')
            cursor = self.textCursor()
            while not cursor.atStart():
                cursor.select(QTextCursor.LineUnderCursor)
                match = self.pattern.search(cursor.selectedText())
                if match:
                    break
                cursor.clearSelection()
                cursor.movePosition(QTextCursor.Up)
                cursor.movePosition(QTextCursor.StartOfLine)
            self.setTextCursor(cursor)

    def updateMatch(self):
        """Update the current pattern match."""
        
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        logline = cursor.selectedText()
        self.currentMatch = self.pattern.search(logline)
        if not self.currentMatch:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.StartOfLine)
            self.setTextCursor(cursor)
            return
        self.setTextCursor(cursor)
        self.lineMatchChanged.emit()
        
    def srcLineNum(self):
        if not self.currentMatch:
            return -1
        return int(self.currentMatch.group(1))
        
    def srcColNum(self):
        if not self.currentMatch:
            return -1
        colstr = self.currentMatch.group(2)
        return int(colstr) - 1  # 1-based in ppscanno output
    
    def srcScanno(self):
        if not self.currentMatch:
            return None
        return self.currentMatch.group(3)  # scanno match
