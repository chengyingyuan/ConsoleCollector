ConsoleCollector

As a unix* guy, I like to get my job done with lots of terminal commands. 
Unfortunatelly, it makes my workmates a bit sick. To cheer them up, 
I wrote this tiny tool assembling non-gui commands into a gui program. I 
hope it cheer you up too. 


To use it, configure a ini file(pls refer demo.ini for details), then start it 
with

python src\main.py <path-to-your-ini-file>


This project depends on pywin32 and pyqt5. I tested it with python3.5 bit64 for 
windows 10.

pywin32:

http://docs.activestate.com/activepython/2.4/pywin32/win32process__CreateProcess_meth.html
http://timgolden.me.uk/pywin32-docs/contents.html
http://zetcode.com/gui/pyqt5/firstprograms/

pyqt5:
https://riverbankcomputing.com/software/pyqt/download5/

