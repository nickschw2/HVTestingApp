# Test mode for when we're not connected to the National Instruments hardware
DEBUG_MODE = False
ADMIN_MODE = True
SHOT_MODE = True

# Power supply constants
maxVoltagePowerSupply = 20e3 # V
maxCurrentPowerSupply = 15e-3 # A
maxVoltageInput = 10 # V
systemStatus_sample_rate = 100 # Hz, rate at which the NI hardware updates the voltage

# Oscilloscope parameters
scopeChannelDefaults = {'Load Voltage': '1', 'Load Current': '2', 'Interferometer': '3', 'Diamagnetic': '4'}
scopeChannelOptions = ['1', '2', '3', '4']

# Pulse Generator parameters
pulseGeneratorGPIBAddress = 2

# NI DAQ parameters
discharge_name = 'PXI1Slot3' # The name of the DAQ device as shown in MAX
systemStatus_name = 'PXI1Slot2' # The name of the DAQ device as shown in MAX
digitalOutName = 'port0'
charge_ao_defaults = {'Power Supply Output': 'ao0'} # analog outputs
systemStatus_defaults = {'Power Supply Voltage': 'ai0',
    'Power Supply Current': 'ai1',
    'Capacitor Voltage': 'ai2'} # analog inputs
do_defaults = {'Load Switch': 'line0',
    'Power Supply Switch': 'line1',
    'Voltage Divider Switch': 'line2'}
diagnostics_defaults = {'Current': 'ai0',
    'Intereferometer': 'ai5',
    'Diamagnetic Axial': 'ai2',
    'Diamagnetic Radial': 'ai3'}
charge_ao_options = ['ao0', 'ao1']
systemStatus_options = ['ai0', 'ai1', 'ai2', 'ai3']
do_options = ['line0', 'line1', 'line2', 'line3']
diagnostics_options = ['ai0', 'ai1', 'ai2', 'ai3']
maxDischargeFreq = int(250000 / len(diagnostics_defaults)) # Hz

# Results plot
dischargeLines = {'Current': []}
interferometerLines = {'Central': []}
diamagneticLines = {'Axial': [], 'Radial': []}

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

# Capacitor constants
maxVoltage = {'LBL': 5, 'BLU': 50, 'GRA': 10, '': 'N/A'}
capacitance = 72 # uF

# User input validation
maximumValidVoltage = max([maxVoltagePowerSupply / 1000, maxVoltage['BLU']]) # kV
maximumValidGasPuff = 100 # ms

# Discharge timing
duration = 0.5 # s
pulse_period = 0.1 # s
pulse_width = 0.01 # s