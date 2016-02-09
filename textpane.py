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

from PyQt5.Qt import Qt, QFile, QFrame, QTextCursor, QTextEdit


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


class LogPane(TextPane):
    """Log viewer window."""
    
    def __init__(self, parent=None):
        super(TextPane, self).__init__(parent)

        # pattern for finding line numbers in log file
        # match groups are linenum, col, and scanno
        self.pattern = re.compile(r"^\s\sLine\s#=(\d+)(?:-\d+)?\spos=(\d+)\smatch=(.+)\s*$")

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
