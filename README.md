# GuiScannos
A DP PP tool. Log viewer for ppscannos.


## System Requirements
python 3.4, Qt5, PyQt5


## Installation
Unpack the zip file somewhere.


## Usage
The main program file is guiscannos.py. If it has been made executable, you just
click on it or type it in on the command line. Otherwise, pass it to the python
interpreter:
$ python3 guiscannos.py
The -h option invokes the help message, which describes the command line
options. In particular,
$ python3 guiscannos.py -l plog.txt foo.txt
will start the program with foo.txt in the edit pane and plog.txt in the log
pane.

You can also run (or re-run) ppscannos from within guiscannos by means of the
Run button in the toolbar. To the right of it are two boxes. The first is to
select the scanno file to use for the run. The second is to select the name of
the log file to generate. The menu choice Settings | Configure will bring up a
dialog where you can edit the location of the ppscannos1.py file. It also allows
you to set the default scanno file to use. The program will store this in a
system-dependent way. I used "LHat" as the Organization and "Gui Scannos" as the
program name. On a Linux system, it will end up in the .config directory under
your home directory.

In the log pane, you can navigate by clicking with the mouse or with the up and
down arrows on the keyboard.


## Remember
This is alpha software. Don't use it under an account with admin priviledges.
Make an extra copy of your text file before using the editor. Expect it to do
something wrong at some point. A number of useful features are still missing.


## Known Issues
