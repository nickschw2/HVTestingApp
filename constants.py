import re
import matplotlib.lines as mlines
import datetime
from tkinter import ttk

# github website
githubSite = 'https://github.com/nickschw2/HVCapTestingApp'

# Date
today = datetime.date.today()

loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
PSSuperscript = '\u1D56\u02E2'
CapacitorSuperscript = '\u1D9C\u1D43\u1D56'

# Colors
green = '#2ecc71'
yellow = '#f1c40f'
orange = '#e67e22'
red = '#e74c3c'
blue = '#3498db'
white = '#ecf0f1'
black = '#000000'
grey = '#636262'
lightGrey = '#a9a1a1'
defaultbg = '#f0f0f0'
UMDRed = '#e03a3d'

# Widget display constants
userInputWidth = 8
userInputPadding = 50 #pixels
loginPadding = 20 #pixels
setPinsPadding = 15 #pixels
labelPadding = 10 #pixels
buttonPadding = 50 #pixels
framePadding = 20 #pixels
plotPadding = 30 #pixels
displaySetTextTime = 1000 # ms
topLevelWidth = 30
topLevelWrapLength = 275
progressBarLength = 300

# Styles
button_opts = {'font':('Helvetica', 12), 'state':'normal'}
text_opts = {'font':('Helvetica', 12)}
entry_opts = {'font':('Helvetica', 12), 'background': lightGrey}
frame_opts = {'borderwidth': 3, 'relief': 'raised', 'padding': 12}

# Serial number format
# 3 Character Capacitor origin 3 digit serial number, e.g. LBL001
format = re.compile('.{3}\d{3}')

# Plotting constants
voltageColor = 'blue'
currentColor = UMDRed

voltageLine = mlines.Line2D([], [], color=voltageColor, linestyle='-', label='V$_{PS}$')
currentLine = mlines.Line2D([], [], color=currentColor, linestyle='-', label='I$_{PS}$')
capacitorLine = mlines.Line2D([], [], color=voltageColor, linestyle='--', label='V$_{cap}$')
chargeHandles = [voltageLine, currentLine, capacitorLine]
dischargeHandles = [voltageLine, currentLine]

checklist_steps = ['Ensure that power supply is off',
     'Ensure that the charging switch is open']
    # 'Check system is grounded',
    # 'Turn on power supply',
    # 'Enter serial number, charge voltage, and hold charge time',
    # 'Exit room and ensure nobody else is present',
    # 'Turn on HV Testing Light',
    # 'Close charging switch',
    # 'Increase voltage on power supply',
    # 'Open charging switch',
    # 'Trigger ignitron',
    # 'Save scope and video data',
    # 'Enter room, turn off power supply, and "idiot stick" all HV lines',
    # 'Turn off HV testing light']

# Saving results
columns = ['Serial Number', 'Capacitance (uF)', 'Internal Resistance (Ohms)', 'Charged Voltage (kV)', 'Hold Charge Time (s)',
    'Charge Time (s)', 'Charge Voltage PS (V)', 'Charge Current PS (A)', 'Capacitor Voltage (V)', 'Discharge Time',
    'Discharge Time Unit', 'Discharge Voltage (V)', 'Discharge Current (A)']
