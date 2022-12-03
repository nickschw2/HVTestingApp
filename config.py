# Test mode for when we're not connected to the National Instruments hardware
DEBUG_MODE = False
ADMIN_MODE = True
SHOT_MODE = True

# Power supply constants
maxVoltagePowerSupply = 20e3 # V
maxCurrentPowerSupply = 15e-3 # A
maxVoltageInput = 10 # V
sample_rate = 1000 # Hz, rate at which the NI hardware updates the voltage

# Oscilloscope parameters
TCPIPAddress = '169.254.55.65'
scopeChannelDefaults = {'Load Voltage': '1', 'Load Current': '2', 'Interferometer': '3', 'Diamagnetic': '4'}
scopeChannelOptions = ['1', '2', '3', '4']

# Pulse Generator parameters
pulseGeneratorGPIBAddress = 2

# NI DAQ parameters
output_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
input_name = 'PXI1Slot2' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
ao_Defaults = {'Power Supply Output': 'ao0'} # analog outputs
ai_Defaults = {'Power Supply Voltage': 'ai0',
    'Power Supply Current': 'ai1',
    'Capacitor Voltage': 'ai2'} # analog inputs
do_Defaults = {'Load Switch': 'line0',
    'Power Supply Switch': 'line1',
    'Voltage Divider Switch': 'line2'}
ao_Options = ['ao0', 'ao1']
ai_Options = ['ai0', 'ai1', 'ai2', 'ai3']
do_Options = ['line0', 'line1', 'line2', 'line3']

# Diagnostic hardware
voltageDivider = 1000 # voltage ratio in:out
attenuator = 19.3 # attenuate voltage on end of capacitor input, this was calibrated for specific voltage divider
pearsonCoil = 0.01 # V/A
# Changing waterResistor temporarily to match plasma
waterResistor = 500 # Ohms
measureInterval = 5 # time between capacitor voltage measurements in seconds

# Testing constants
RCTime = 0.2 # seconds

# Charging constants
chargeTimeLimit = 10 # seconds
epsilonDesiredChargeVoltage = 0.05 # Unitless, fraction of desired charge that will trigger a discharge if the capacitor is not charging
chargeVoltageLimit = 0.95 # fraction above which the capacitor will be considered charged to the desired charge

# Usernames
acceptableUsernames = ['nickschw', 'koeth', 'beaudoin', 'romero', 'rschnei4']
acceptablePasswords = ['plasma']

# Plotting constants
refreshRate = 100.0 # Hz

# Time between switch operations in seconds
switchWaitTime = 0.2
hardCloseWaitTime = 4

# Is the ignitron used for switching?
# If so, it will stop conducting when the current becomes too low, meaning that there is a steep drop to zero voltage when the switch reopens
ignitronInstalled = True

# Charging constants
maxVoltage = {'LBL': 5, 'BLU': 50, 'GRA': 10, '': 'N/A'}
