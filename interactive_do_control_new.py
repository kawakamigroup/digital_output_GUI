# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 15:21:55 2022

@author: asc-kawakamigroup
"""


# Challenge: Create a GUI that controls when certain buttons can be
#            selected. For instance, if we are using port 0, all 8 lines can
#            be selected. However, if we are using port 1, only 4 lines can
#            be selected. We can likely use an array for this similar to
#            nidaq_voltage_control such that the buttons alter a preset array.

# Import tools

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5 import uic
from functools import partial

import nidaqmx
from nidaqmx.constants import(LineGrouping)
import pprint
import numpy as np

# Define variables

pp = pprint.PrettyPrinter() # pprint for printing data from DAQ into kernel
High = bool(1) # High = True = 5V Signal
Low = bool(0) # Low = False = 0V Signal

# Create main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(r'C:\Python\gui-files\do_control_1.ui', self)
        # don't use do_control; program was wiped from memory.
        # instead use do_control_1.
        
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan (
                "Dev1/port1/line0",  
                line_grouping=LineGrouping.CHAN_PER_LINE)
            global N
            N = task.number_of_channels
            # This ask is used twice, first instance is local to obtain a 
            # global variable 'N'
        
        # enable a button for the individual line functions (will set high/low)
        for i in range(0,N):
            name = str(i)
            btn1 = self.findChild(QPushButton, f"setline{name}") #
            btn1.clicked.connect(partial(self.linestatus_function, name))
        
        # btn2 => all high button, btn3 => all low button                         
        btn2 = self.findChild(QPushButton, f"all_high_button")
        btn2.clicked.connect(partial(self.AllHigh_function, name))
        btn3 = self.findChild(QPushButton, f"all_low_button")
        btn3.clicked.connect(partial(self.AllLow_function, name))
        
        # array that will be sent out to DAQ with start function
        global data
        data = []
        for i in range (0,N):
            data.append(Low) # data array initally set at low values
        
        self.start_button.clicked.connect(self.Start_function) #writes signal
        self.stop_button.clicked.connect(self.Stop_function) #ends signal

# Define all button functions that alter the array

    def linestatus_function(self, name, checked): # change between 0V/5V
        state = "0V Enabled" # if not clicked, set at 0V
        messageState = "Low"
        color = "lightsteelblue"
        data[int(name)] = Low # sets array at position to Low, or False
        if checked: 
            state = "5V Enabled" # if clicked, set at 5V
            messageState = "High" 
            color = "lightslategray"
            data[int(name)] = High # sets array at position to High, or True
        btn1 = self.findChild(QPushButton, f"setline{name}")
        btn1.setStyleSheet(f"background-color:{color};") #bg color
        m = btn1.text()
        print(f"{m}: {state}") #Line status written in kernel
        label = self.findChild(QLabel, f"line{name}stat")
        label.setText(state) # chnages button label
        self.statusbar.showMessage(f"Line {name} set to {messageState}")
        print(data,'\n') # print updated array in kernel
        label = self.findChild(QLabel, f"arrayval_label")
        label.setText(str(np.multiply(data, 1))) #binary array of data[]
        
    def AllHigh_function(self, name): # set all array elements to 5V
        print("All States set to High (5V)")
        messageState = "High"
        self.statusbar.showMessage(f"All Lines Set to {messageState}")
        for x in range (0,N): #loop sets all buttons to high, but does not click them.
                name = str(x) 
                data[int(name)] = High
                state = "5V Enabled"
                color = "lightslategray"
                btn1 = self.findChild(QPushButton, f"setline{name}")
                btn1.setStyleSheet(f"background-color:{color};")
                label = self.findChild(QLabel, f"line{name}stat")
                label.setText(state)
        print(data, '\n')
        label = self.findChild(QLabel, f"arrayval_label")
        label.setText(str(np.multiply(data, 1)))
       
    def AllLow_function(self, name): #set all buttons to low, but does not unclick them
        print("All States set to Low (0V)")
        messageState = "Low"
        self.statusbar.showMessage(f"All Lines Set to {messageState}")
        for x in range (0,N):
                name = str(x)
                data[int(name)] = Low
                state = "0V Enabled"
                color = "lightsteelblue"
                btn1 = self.findChild(QPushButton, f"setline{name}")
                btn1.setStyleSheet(f"background-color:{color};")
                label = self.findChild(QLabel, f"line{name}stat")
                label.setText(state)
        print(data, '\n')
        label = self.findChild(QLabel, f"arrayval_label")
        label.setText(str(np.multiply(data, 1)))            
        
# Writes the signal

    def Start_function(self): # writes constructed array
        with nidaqmx.Task() as task: # create a local task
            task.do_channels.add_do_chan (
                "Dev1/port1/line0",  
                line_grouping=LineGrouping.CHAN_PER_LINE)
            task.write(data, auto_start = True, timeout=10.0)
            task_report = task.read()
            pp.pprint(task_report) 
            # prints the data from the task, ensuring the correct array is
            # received.
        print("Digital Output written to DAQ.\n")
        label = self.findChild(QLabel, f"arrayval_label")
        label.setText(f"Signal {np.multiply(data, 1)} written.")
        
    
    def Stop_function(self):
        print("Attempted to close Digital Output.")
        print("Diagnostics:")
        totClose = 0 # integer of lines that read 
        for x in range (0,N): # similar code to all_low, resets lines to 0V
            name = str(x)
            data[int(name)] = Low
            state = "0V Enabled"
            color = "lightsteelblue"
            btn1 = self.findChild(QPushButton, f"setline{name}")
            btn1.setStyleSheet(f"background-color:{color};")
            label = self.findChild(QLabel, f"line{name}stat")
            label.setText(state)
            
            # the below test checks if each line is false.
            # if a line is not false, the error message displays,
            # affecting the totClose integer and causing a discrepancy
            if data[int(name)] == Low:
                print(f"Line {name} closed.")
                totClose = totClose + 1
            else:
                print(f"Error: Line {name} not closed")
                
        if totClose != len(data):
            print("All Lines Not Reset to False, Exit the Window and Restart")
        else:
            print("Digital Output closed.")
            
        label = self.findChild(QLabel, f"arrayval_label")
        label.setText("Signal closed.")
        
    

app = QtWidgets.QApplication(sys.argv)
Window = MainWindow()
Window.setWindowTitle('Digital Output Control Panel')
Window.show()
sys.exit(app.exec_())    