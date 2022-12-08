import re
import matplotlib.lines as mlines
import datetime

# github website
githubSite = 'https://github.com/nickschw2/HVTestingApp'

# Capacitor Specs doc
capacitorSpecificationsName = 'Capacitor_Specifications.csv'

# Date
today = datetime.date.today()

loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
PSSuperscript = '\u1D56\u02E2'
CapacitorSuperscript = '\u1D9C\u1D43\u1D56'

# Colors
orange = '#ffa300'
blue = '#0bb4ff'
red = '#e60049'

# Widget display constants
userInputWidth = 8
userInputPadding = 50 #pixels
loginPadding = 20 #pixels
setPinsPaddingX = 15 #pixels
setPinsPaddingY = 3 #pixels
labelPadding = 10 #pixels
buttonPadding = 50 #pixels
framePadding = 20 #pixels
plotPadding = 30 #pixels
displaySetTextTime = 1000 # ms
topLevelWidth = 30
topLevelWrapLength = 275
systemStatusFrameWidth = 250
progressBarLength = 300
plotTimeLimit = 20 # s
voltageYLim = 1.2 # kV
currentYLim = 15 # mA

# Styles
button_opts = {'font':('Helvetica', 12), 'state':'normal'}
text_opts = {'font':('Helvetica', 12)}
entry_opts = {'font':('Helvetica', 12)}
# frame_opts = {'font':('Helvetica', 12), 'borderwidth': 3, 'relief': 'raised', 'padding': 12}
frame_opts = {'borderwidth': 3, 'relief': 'flat', 'padding': 12}

# Serial number format
# 3 Character Capacitor origin 3 digit serial number, e.g. LBL001
format = re.compile('.{3}\d{3}')

# Plotting constants
voltageColor = blue
currentColor = red
fitColor = orange

voltageLine = mlines.Line2D([], [], color=voltageColor, linestyle='-', label='V$_{PS}$')
currentLine = mlines.Line2D([], [], color=currentColor, linestyle='-', label='I$_{PS}$')
capacitorLine = mlines.Line2D([], [], color=voltageColor, linestyle='--', label='V$_{cap}$')
fitLine = mlines.Line2D([], [], color=fitColor, linestyle='-', label='V$_{fit}$')
chargeHandles = [voltageLine, capacitorLine, currentLine]
dischargeHandles = [voltageLine, currentLine]

columns = {'serialNumber': {'name': 'Serial Number', 'type': 'scalar'},
    'capacitance': {'name': 'Capacitance (uF)', 'type': 'scalar'},
    'equivalentSeriesResistance': {'name': 'ESR (Ohms)', 'type': 'scalar'},
    'dielectricAbsorptionRatio': {'name': 'DAR', 'type': 'scalar'},
    'polarizationIndex': {'name': 'PI', 'type': 'scalar'},
    'internalResistance': {'name': 'Internal Resistance (Ohms)', 'type': 'scalar'},
    'waterResistance': {'name': 'Water Resistance (Ohms)', 'type': 'scalar'},
    'chargeVoltage': {'name': 'Charged Voltage (kV)', 'type': 'scalar'},
    'holdChargeTime': {'name': 'Hold Charge Time (s)', 'type': 'scalar'},
    'chargeTime': {'name': 'Charge Time (s)', 'type': 'array'},
    'chargeVoltagePS': {'name': 'Charge Voltage PS (V)', 'type': 'array'},
    'chargeCurrentPS': {'name': 'Charge Current PS (A)', 'type': 'array'},
    'capacitorVoltage': {'name': 'Capacitor Voltage (V)', 'type': 'array'},
    'dischargeTime': {'name': 'Discharge Time', 'type': 'array'},
    'dischargeTimeUnit': {'name': 'Discharge Time Unit', 'type': 'scalar'},
    'dischargeVoltageLoad': {'name': 'Discharge Voltage (V)', 'type': 'array'},
    'dischargeCurrentLoad': {'name': 'Discharge Current (A)', 'type': 'array'},
    'interferometer': {'name': 'Interferometer (V)', 'type': 'array'},
    'diamagnetic': {'name': 'Diamagnetic (V)', 'type': 'array'},
    'preShotNotes': {'name': 'Pre-Shot Notes', 'type': 'scalar'},
    'postShotNotes': {'name': 'Post-Shot Notes', 'type': 'scalar'}}