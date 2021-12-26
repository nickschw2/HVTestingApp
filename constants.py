import re
import matplotlib.lines as mlines

# Oscilloscope pins
voltageLoadPin = 'ai0'
voltagePSPin = 'ai1'
currentLoadPin = 'ai2'
currentPSPin = 'ai3'

# Colors
green = '#2ecc71'
yellow = '#f1c40f'
orange = '#e67e22'
red = '#e74c3c'
blue = '#3498db'
white = '#ecf0f1'

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero']
acceptablePasswords = ['plasma']

# Constant Button Options
button_opts = {'font':('Calibri', 24), 'state':'normal'}
text_opts = {'font':('Calibri', 24)}

# Widget display constants
userInputWidth = 6
userInputPadding = 100 #pixels
loginPadding = 20 #pixels
buttonPadding = 50 #pixels
displaySetTextTime = 1000 # ms
topLevelWidth = 300 #pixels

# Serial number format
# 3 Character Capacitor origin 3 digit serial number, e.g. LBL001
format = re.compile('.{3}\d{3}')

# Plotting constants
refreshRate = 10.0 # Hz
voltageColor = 'blue'
currentColor = 'red'

voltageLine = mlines.Line2D([], [], color=voltageColor, linestyle='-', label='V$_{load}$')
voltageDash = mlines.Line2D([], [], color=voltageColor, linestyle='--', label='V$_{PS}$')
currentLine = mlines.Line2D([], [], color=currentColor, linestyle='-', label='I$_{load}$')
currentDash = mlines.Line2D([], [], color=currentColor, linestyle='--', label='I$_{PS}$')
chargeHandles = [voltageLine, voltageDash, currentLine, currentLine]
dischargeHandles = [voltageLine, currentLine]

# Charging constants
powerSupplyVoltage = 20e3 # V
powerSupplyResistance = 1E4 # Ohm
capacitorCapacitance = 200e-6 # Farads
RCTime = powerSupplyResistance * capacitorCapacitance
chargeVoltageFraction = 0.95
