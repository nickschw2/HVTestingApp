import re
import matplotlib.lines as mlines

# github website
githubSite = 'https://github.com/nickschw2/HVTestingApp'

# Saving results
saveFolderShotDefault = 'C:/Users/Control Room/programs/HVTestingApp/results'
saveFolderCapDefault = 'C:/Users/Control Room/programs/HVTestingApp/capacitor_results'
resultsMasterName = 'results_master.csv'

# Capacitor Specs doc
capacitorSpecificationsName = 'Capacitor_Specifications.csv'

# Special characters
loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
PSSuperscript = '\u1D56\u02E2'
CapacitorSuperscript = '\u1D9C\u1D43\u1D56'
Omega = '\u03A9'

# Colors
# Taken from https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data
color_palette = ["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5", "#8bd3c7"]
voltageColor = color_palette[0]
currentColor = color_palette[1]
fitColor = color_palette[2]

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
themename = 'darkly'
button_opts = {'font':('Helvetica', 12), 'state':'normal'}
text_opts = {'font':('Helvetica', 12)}
entry_opts = {'font':('Helvetica', 12)}
# frame_opts = {'font':('Helvetica', 12), 'borderwidth': 3, 'relief': 'raised', 'padding': 12}
frame_opts = {'borderwidth': 3, 'relief': 'flat', 'padding': 12}

# Serial number format
# 3 Character Capacitor origin 3 digit serial number, e.g. LBL001
format = re.compile('.{3}\d{3}')

# Lines for charging
voltageLine = mlines.Line2D([], [], color=voltageColor, linestyle='-', label='V$_{PS}$')
currentLine = mlines.Line2D([], [], color=currentColor, linestyle='-', label='I$_{PS}$')
capacitorLine = mlines.Line2D([], [], color=voltageColor, linestyle='--', label='V$_{cap}$')
fitLine = mlines.Line2D([], [], color=fitColor, linestyle='-', label='V$_{fit}$')
chargeHandles = [voltageLine, capacitorLine, currentLine]
dischargeHandles = [voltageLine, currentLine]

# Analysis of data
cutoff_freq = 10000 # Hz
m_p = 1.673e-27 # proton mass (kg)
A = 1 # Atomic mass number
m_i = m_p * A 

# Diamagnetic constants
N_turns = 16
B0 = 3.0 # background magnetic field (T)
d_r = 0.05 # distance of magnetic shift (m)
chamber_radius = 0.3513 # Inner radius of chamber (m)
plasma_radius_outer = 0.2363 # Plasma radius (m)\
plasma_radius_inner = 0.05 # Plasma radius (m)



# Physics constants
mu0 = 1.2566e-6 # Vaccum permeability (H/m)

single_columns = {'serialNumber': {'name': 'Serial Number', 'type': 'scalar'},
    'runNumber': {'name': 'Run Number', 'type': 'scalar'},
    'runDate': {'name': 'Run Date', 'type': 'scalar'},
    'runTime': {'name': 'Run Time', 'type': 'scalar'},
    'capacitance': {'name': 'Capacitance (uF)', 'type': 'scalar'},
    'ballastResistance': {'name': 'Ballast Resistance (Ohms)', 'type': 'scalar'},
    'dumpResistance': {'name': 'Dump Resistance (Ohms)', 'type': 'scalar'},
    'gasPuffTime': {'name': 'Gas Puff Time (ms)', 'type': 'scalar'},
    'dumpDelay': {'name': 'Dump Delay (ms)', 'type': 'scalar'},
    'pumpBasePressure': {'name': 'Pump Base Pressure (torr)', 'type': 'scalar'},
    'chamberBasePressure': {'name': 'Chamber Base Pressure (torr)', 'type': 'scalar'},
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
    'dischargeVoltage': {'name': 'Discharge Voltage (V)', 'type': 'array'},
    'dischargeCurrent': {'name': 'Discharge Current (A)', 'type': 'array'},
    'dumpCurrent': {'name': 'Dump Current (A)', 'type': 'array'},
    'groundCurrent': {'name': 'Ground Current (A)', 'type': 'array'},
    'INT01': {'name': 'INT01 (V)', 'type': 'array'},
    'INT02': {'name': 'INT01 (V)', 'type': 'array'},
    'DIA01': {'name': 'DIA01 (V)', 'type': 'array'},
    'DIA02': {'name': 'DIA02 (V)', 'type': 'array'},
    'DIA03': {'name': 'DIA03 (V)', 'type': 'array'},
    'DIA04': {'name': 'DIA04 (V)', 'type': 'array'},
    'BR01': {'name': 'BR01 (V)', 'type': 'array'},
    'BR02': {'name': 'BR02 (V)', 'type': 'array'},
    'BR03': {'name': 'BR03 (V)', 'type': 'array'},
    'BR04': {'name': 'BR04 (V)', 'type': 'array'},
    'Trigger': {'name': 'Trigger (V)', 'type': 'array'},
    'preShotNotes': {'name': 'Pre-Shot Notes', 'type': 'scalar'},
    'postShotNotes': {'name': 'Post-Shot Notes', 'type': 'scalar'}}

# Columns to save to master lookup files
master_columns = {}
for variable, description in single_columns.items():
    if description['type'] == 'scalar':
        master_columns[variable] = description['name']