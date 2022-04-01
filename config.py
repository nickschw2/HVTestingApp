# Test mode for when we're not connected to the National Instruments hardware
TEST_MODE = False
maxVoltagePowerSupply = 20 # kV
maxInputVoltage = 10 # V
RCTime = 4 # seconds
period = 4 # seconds

# NI DAQ pins
sensorName = 'PXI1Slot3'
digitalOutName = 'port0'
inputPinDefaults = {'Load Voltage': '1',
'Power Supply Voltage': '2',
'Load Current': '3',
'Power Supply Current': '4'}
outputPinDefaults = {'Power Supply Voltage': 'ao0',
'Load Switch': 'line0',
'Power Supply Switch': 'line1'}
inputPinOptions = ['1', '2', '3', '4']
outputPinOptions = ['ao0', 'line0', 'line1']

# Charging constants
# chargeTime = 60 # seconds
# maxVoltagePowerSupply = 20 # kV
# voltageReferencePowerSupply = 10 # V
chargeTimeLimit = 10 # seconds
epsilonDesiredChargeVoltage = 0.05 # Unitless, fraction of desired charge that will trigger a discharge if the capacitor is not charging

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 10.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.5

# Charging constants
maxVoltage = {'LBL': 5, 'BLU': 10, 'GRA': 50, '': 'N/A'}