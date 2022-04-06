# Test mode for when we're not connected to the National Instruments hardware
TEST_MODE = False

# Power supply constants
maxVoltagePowerSupply = 20 # kV
maxCurrentPowerSupply = 15 # mA
maxVoltageInput = 10 # V
sample_rate = 100 # Hz, rate at which the NI hardware updates the voltage
seconds_per_kV = 2 # Time to charge per kV

# Oscilloscope parameters
TCPIPAddress = '169.254.168.66'
scopeChannelDefaults = {'Load Voltage': '1', 'Load Current': '2'}
scopeChannelOptions = ['1', '2', '3', '4']

# NI DAQ parameters
dev_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
NIAODefaults = {'Power Supply Output': 'ao0'} # analog outputs
NIAIDefaults = {'Power Supply Voltage': 'ai0', 'Power Supply Current': 'ai1'} # analog inputs
NIDODefaults = {'Load Switch': 'line0', 'Power Supply Switch': 'line1'}
NIAOOptions = ['ao0', 'ao1']
NIAIOptions = ['ai0', 'ai1', 'ai2', 'ai3']
NIDOOptions = ['line0', 'line1', 'line2', 'line3']

# Diagnostic hardware
voltageDivider = 1000 # voltage ratio in:out
pearsonCoil = 0.01 # V/A


RCTime = 4 # seconds
period = 4 # seconds

# Charging constants
# chargeTime = 60 # seconds
# maxVoltagePowerSupply = 20 # kV
# voltageReferencePowerSupply = 10 # V
chargeTimeLimit = 10 # seconds
epsilonDesiredChargeVoltage = 0.05 # Unitless, fraction of desired charge that will trigger a discharge if the capacitor is not charging
chargeVoltageLimit = 0.99

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 100.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.5

# Charging constants
maxVoltage = {'LBL': 5, 'BLU': 10, 'GRA': 50, '': 'N/A'}
