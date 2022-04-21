# Test mode for when we're not connected to the National Instruments hardware
DEBUG_MODE = True

# Power supply constants
maxVoltagePowerSupply = 20e3 # V
maxCurrentPowerSupply = 15e-3 # A
maxVoltageInput = 10 # V
sample_rate = 100 # Hz, rate at which the NI hardware updates the voltage
seconds_per_kV = 10 # Time to charge per kV

# Oscilloscope parameters
TCPIPAddress = '169.254.183.132'
scopeChannelDefaults = {'Load Voltage': '1', 'Load Current': '2'}
scopeChannelOptions = ['1', '2', '3', '4']

# NI DAQ parameters
dev_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
NIAODefaults = {'Power Supply Output': 'ao0'} # analog outputs
NIAIDefaults = {'Power Supply Voltage': 'ai0',
    'Power Supply Current': 'ai1',
    'Capacitor Voltage': 'ai2'} # analog inputs
NIDODefaults = {'Load Switch': 'line0', 'Power Supply Switch': 'line1'}
NIAOOptions = ['ao0', 'ao1']
NIAIOptions = ['ai0', 'ai1', 'ai2', 'ai3']
NIDOOptions = ['line0', 'line1', 'line2', 'line3']

# Diagnostic hardware
voltageDivider = 1000 # voltage ratio in:out
pearsonCoil = 0.01 # V/A

# Testing constants
RCTime = 0.4 # seconds

# Charging constants
chargeTimeLimit = 10 # seconds
epsilonDesiredChargeVoltage = 0.05 # Unitless, fraction of desired charge that will trigger a discharge if the capacitor is not charging
chargeVoltageLimit = 0.3 # fraction above which the capacitor will be considered charged to the desired charge

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 200.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.5

# Charging constants
maxVoltage = {'LBL': 5, 'BLU': 10, 'GRA': 50, '': 'N/A'}
