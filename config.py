# NI DAQ pins
sensorName = 'PXI1Slot2'
digitalOutName = 'port0'
inputPinDefaults = {'Load Voltage': 'ai0',
'Power Supply Voltage': 'ai1',
'Load Current': 'ai2',
'Power Supply Current': 'ai3'}
outputPinDefaults = {'Power Supply Switch': 'line0',
outputPinDefaults = {'Charge Control': 'ao0',
'Power Supply Switch': 'line0',
'Load Switch': 'line1'}
inputPinOptions = ['ai0', 'ai1', 'ai2', 'ai3']
outputPinOptions = ['line0', 'line1']

# Charging constants
chargeTime = 60 # seconds
maxVoltagePowerSupply = 20 # kV
voltageReferencePowerSupply = 10 # V

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 10.0 # Hz

# Charging constants
maxVoltage = {'LBL': 5, 'BLU': 10, 'GRA': 50, '': 'N/A'}
