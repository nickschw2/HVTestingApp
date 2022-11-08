import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os
import webbrowser
import nidaqmx
import scipy.optimize, scipy.signal
from constants import *
from plots import *
from messages import *
from config import *
from scope import *
from ni_daq import *
from timer import *
from gpib import *

# Change nidaqmx read/write to this format? https://github.com/AppliedAcousticsChalmers/nidaqmxAio

# Tkinter has quite a high learning curve. If attempting to edit this source code without experience, I highly
# recommend going through some tutorials. The documentation on tkinter is also quite poor, but
# this website has the best I can find (http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm). At times you may
# need to manually go into the tkinter source code to investigate the behavior/capabilities of some code.

class TestingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # set theme
        self.tk.call('source', 'Sun-Valley-ttk-theme/sun-valley.tcl')
        self.tk.call('set_theme', 'light')

        # Change style
        style = ttk.Style(self)
        style.configure('TButton', **button_opts)
        style.configure('TCheckbutton', **text_opts)
        style.configure('TLabelframe.Label', **text_opts)

        self.configure_ui()
        self.init_ui()
        if not DEBUG_MODE:
            self.init_DAQ()
            self.init_PulseGenerator()

    # There are two pieces of hardware important for communication with the test cart
    # The NI panel extender provides an analog output and two analog inputs to read/write to the power supply during charging
    # The Oscilloscope is triggered when the capacitor discharges and reads waveform from the discharge
    def init_DAQ(self):
        # We need both an analog input and output
        self.NI_DAQ = NI_DAQ(input_name, output_name, sample_rate, ai_channels=self.ai_Pins, ao_channels=self.ao_Pins)

        # Initialize the scope over ethernet
        try:
            self.scope = Oscilloscope()
        except visa.errors.VisaIOError:
            scopeErrorName = 'Oscilloscope Connection'
            scopeErrorText = 'Cannot connect to oscilloscope because IP address is either incorrect or not present. Please make sure instrument is on and has IP address. The IP can be found on the instrument or NI MAX.'
            scopeErrorWindow = MessageWindow(self, scopeErrorName, scopeErrorText)

            scopeErrorWindow.wait_window()

            # If the user presses the Okay button, charging begins
            if scopeErrorWindow.OKPress:
                self.on_closing()

    def init_PulseGenerator(self):
        self.pulseGenerator = PulseGenerator()

    def openSite(self):
        webbrowser.open(githubSite)

    def setSaveLocation(self):
        # Creates folder dialog for user to choose save directory
        self.saveFolder = filedialog.askdirectory(initialdir=os.path.dirname(os.path.realpath(__file__)), title='Select directory for saving results.')
        if self.saveFolder != '':
            self.saveFolderSet = True

        # If the user inputs have already been set, enable the checklist button
        if self.userInputsSet:
            self.checklistButton.configure(state='normal')

    def pinSelector(self):
        # Create popup window with fields for username and password
        self.setPinWindow = tk.Toplevel(padx=setPinsPadding, pady=setPinsPadding)
        self.setPinWindow.title('Set Pins')
        # Bring pop up to the center and top
        self.eval(f'tk::PlaceWindow {str(self.setPinWindow)} center')
        self.setPinWindow.attributes('-topmost', True)

        # This function places pin labels and dropdown menus in the popup window
        def selectPins(channelDefaults, options):
            pins = {}
            nCols, nRows = self.setPinWindow.grid_size()
            for i, channel in enumerate(channelDefaults):
                channelVariable = tk.StringVar()
                channelVariable.set(channelDefaults[channel])
                label = ttk.Label(self.setPinWindow, text=channel, **text_opts)
                drop = ttk.OptionMenu(self.setPinWindow, channelVariable, channelDefaults[channel], *options)

                label.grid(row=nRows + i, column=0, sticky='w', padx=(0, setPinsPadding))
                drop.grid(row=nRows + i, column=1, sticky='w', padx=(setPinsPadding, 0))

                pins[channel] = channelVariable

            return pins

        scopePinsOptions = selectPins(scopeChannelDefaults, scopeChannelOptions)
        ao_PinsOptions = selectPins(ao_Defaults, ao_Options)
        ai_PinsOptions = selectPins(ai_Defaults, ai_Options)
        do_PinsOptions = selectPins(do_Defaults, do_Options)

        # Button on the bottom
        nCols, nRows = self.setPinWindow.grid_size()
        buttonFrame = ttk.Frame(self.setPinWindow)
        buttonFrame.grid(row=nRows + 1, columnspan=2)

        # Once the okay button is pressed, assign the pins
        def assignPins():
            for channel in scopePinsOptions:
                self.scopePins[channel] = scopePinsOptions[channel].get()

            for channel in ao_PinsOptions:
                self.ao_Pins[channel] = ao_PinsOptions[channel].get()

            for channel in ai_PinsOptions:
                self.ai_Pins[channel] = ai_PinsOptions[channel].get()

            for channel in do_PinsOptions:
                self.do_Pins[channel] = do_PinsOptions[channel].get()

            print(self.scopePins)
            print(self.ao_Pins)
            print(self.ai_Pins)
            print(self.do_Pins)
            self.setPinWindow.destroy()

        okayButton = ttk.Button(buttonFrame, text='Set Pins', command=assignPins, style='Accent.TButton')
        okayButton.pack()

        self.setPinWindow.wait_window()

    def getCapacitorData(self, serialNumber):
        capacitorSpecifications = pd.read_csv(capacitorSpecificationsName)
        index = capacitorSpecifications['Serial Number'] == serialNumber
        # If serial number is not in the list, raise ValueError
        if not index.any():
            raise ValueError

        return capacitorSpecifications[capacitorSpecifications['Serial Number'] == serialNumber]

    # Disable all buttons in the button frame
    def disableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, ttk.Button):
                w.configure(state='disabled')

    # Enable normal operation of all buttons in the button frame
    def enableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, ttk.Button):
                w.configure(state='normal')

    def checklist(self):
        # Any time the checklist is opened, all buttons are disabled except for the save, help, and checklist
        self.disableButtons()
        self.checklistButton.configure(state='normal')

        # Popup window appears to confirm charging
        checklistName = 'Checklist Complete?'
        checklistText = 'Has the checklist been completed?'
        checklistWindow = MessageWindow(self, checklistName, checklistText)

        checklistWindow.OKButton['text'] = 'Yes'
        cancelButton = ttk.Button(checklistWindow.bottomFrame, text='Cancel', command=checklistWindow.destroy, style='Accent.TButton')
        cancelButton.pack(side='left')

        checklistWindow.wait_window()

        if checklistWindow.OKPress and self.userInputsSet:
            self.enableButtons()

    def operateSwitch(self, switchName, state):
        # If state is false, power supply switch opens and load switch closes
        # If state is true, power supply switch closes and load switch opens
        if not DEBUG_MODE:
            try:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(f'{output_name}/{digitalOutName}/{self.do_Pins[switchName]}')
                    value = task.write(state)
                    print(f'{switchName} in {state} state')

            except Exception as e:
                print(e)
                print('Cannot operate switches')

    # Sends signal from NI analog output to charge or discharge the capacitor
    def powerSupplyRamp(self, action='discharge'):
        mapVoltage = self.chargeVoltage / maxVoltagePowerSupply * maxVoltageInput * 1000

        if action == 'charge':
            value = mapVoltage
        else:
            value = 0

        if not DEBUG_MODE:
            self.NI_DAQ.write_value(value)

    def charge(self):
        # Popup window appears to confirm charging
        chargeConfirmName = 'Begin charging'
        chargeConfirmText = 'Are you sure you want to begin charging?'
        chargeConfirmWindow = MessageWindow(self, chargeConfirmName, chargeConfirmText)

        cancelButton = ttk.Button(chargeConfirmWindow.bottomFrame, text='Cancel', command=chargeConfirmWindow.destroy, style='Accent.TButton')
        cancelButton.pack(side='left')

        chargeConfirmWindow.wait_window()

        # If the user presses the Okay button, charging begins
        if chargeConfirmWindow.OKPress:
            self.idleMode = False

            # Operate switches
            self.operateSwitch('Load Switch', True)
            time.sleep(switchWaitTime)
            self.operateSwitch('Power Supply Switch', True)
            self.operateSwitch('Voltage Divider Switch', True)
            self.voltageDividerClosed = True
            time.sleep(switchWaitTime)s

            # Actually begin charging power supply
            self.powerSupplyRamp(action='charge')

            # Begin tracking time
            self.beginChargeTime = time.time()
            self.charging = True

            # Reset the charge plot and begin continuously plotting
            self.resetChargePlot()
            # self.updateCharge()
            self.updateChargeValues()
            self.chargePress = True

    def discharge(self):
        def popup():
            # Popup window to confirm discharge
            dischargeConfirmName = 'Discharge'
            dischargeConfirmText = 'Are you sure you want to discharge?'
            dischargeConfirmWindow = MessageWindow(self, dischargeConfirmName, dischargeConfirmText)

            cancelButton = ttk.Button(dischargeConfirmWindow.bottomFrame, text='Cancel', command=dischargeConfirmWindow.destroy, style='Accent.TButton')
            cancelButton.pack(side='left')

            dischargeConfirmWindow.wait_window()

            if dischargeConfirmWindow.OKPress:
                # Operate switches
                self.operateSwitch('Power Supply Switch', False)
                time.sleep(switchWaitTime)
                self.operateSwitch('Load Switch', False)

                # Force discharge to occur
                self.powerSupplyRamp(action='discharge')

        def saveDischarge():
            # Close voltage divider and stop repeating timer
            self.operateSwitch('Voltage Divider Switch', True)
            self.voltageDividerClosed = True
            if hasattr(self, 'switchTimer'):
                self.switchTimer.stop()

            # Read from the load
            if not DEBUG_MODE:
                try:
                    self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                    self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                    self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
                    self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()
                except visa.errors.VisaIOError:
                    self.scope.connectInstrument()
                    self.dischargeVoltageLoad = self.scope.get_data(self.scopePins['Load Voltage']) * voltageDivider
                    self.dischargeCurrentLoad = self.scope.get_data(self.scopePins['Load Current']) / pearsonCoil
                    self.interferometer = self.scope.get_data(self.scopePins['Interferometer'])
                    self.dischargeTime, self.dischargeTimeUnit  = self.scope.get_time()

            else:
                self.dischargeVoltageLoad, self.dischargeCurrentLoad, self.dischargeTime, self.dischargeTimeUnit = self.getDischargeTestValues()

            if len(self.dischargeTime) != 0:
                # get resistance of water resistor
                try:
                    self.internalResistance, chargeFitTime, chargeFitVoltage = self.getResistance(self.chargeTime, self.capacitorVoltage)
                    self.waterResistance, self.dischargeFitTime, self.dischargeFitVoltage = self.getResistance(self.dischargeTime, self.dischargeVoltageLoad)
                except:
                    self.internalResistance, chargeFitTime, chargeFitVoltage = (0, 0, 0)
                    self.waterResistance, self.dischargeFitTime, self.dischargeFitVoltage = (0, 0, 0)
                self.fitVoltageLine.set_data(chargeFitTime, chargeFitVoltage / 1000)
                self.waterResistance /= 1000

                # Plot results on the discharge graph and save them
                # The only time results are saved is when there is a discharge that is preceded by charge
                self.replotCharge()
                self.replotDischarge()

                self.internalResistanceText.set(f'R{CapacitorSuperscript}: {self.internalResistance / 1e6:.2f} M\u03A9')

                self.saveResults()

            else:
                print('Oscilloscope was not triggered successfully')

        if self.charging:
            if not hasattr(self, 'countdownTime') or self.countdownTime > 0.0:
                popup()
                saveDischarge()
            else:
                self.pulseGenerator.triggerIgnitron()
                time.sleep(hardCloseWaitTime)
                self.operateSwitch('Load Switch', False)
                saveDischarge()
        else:
            popup()

        # Disable all buttons except for save and help, if logged in
        self.disableButtons()
        if self.loggedIn:
            self.resetButton.configure(state='normal')

        self.discharged = True
        self.charging = False

    def getResistance(self, time, voltage):
        # Exponential decay function that decays to 0
        def expDecay(time, m, tau, b):
            return m * np.exp(-time / tau) + b

        # Find the point at which the capacitor is isolated
        try:
            peaks, _ = scipy.signal.find_peaks(voltage, width=10)
            startIndex = peaks[-1]
        except:
            startIndex = np.where(voltage == max(voltage))[0][0]
        expVoltage = voltage[startIndex:]
        if ignitronInstalled:
            endIndex = (expVoltage < 0).argmax()
        else:
            endIndex = len(time) - 1

        expVoltage = voltage[startIndex:endIndex]
        expTime = time[startIndex:endIndex]
        nanIndices = np.isnan(expVoltage)
        zeroIndices = expVoltage == 0
        expVoltage = expVoltage[~np.logical_or(nanIndices, zeroIndices)]
        expTime = expTime[~np.logical_or(nanIndices, zeroIndices)]

        # get estimate of tau
        tauGuess = (expTime[-1] - expTime[0]) / np.log(expVoltage[0] / expVoltage[-1])

        p0 = (max(voltage) * voltageDivider, tauGuess, expVoltage[-1]) # start with values near those we expect
        try:
            params, cv = scipy.optimize.curve_fit(expDecay, expTime, expVoltage, p0) # zero the time so that initial guess can be closer
            m, tau, b = params
            fitVoltage = expDecay(expTime, m, tau, b)
        except:
            tau = 0
            fitVoltage = np.zeros(len(expTime))

        return tau / self.capacitance, expTime, fitVoltage

    # Turn on safety lights inside the control room and outside the lab
    def safetyLights(self):
        print('Turn on safety lights')

    def emergency_off(self):
        print('Emergency Off')

    def validateLogin(self):
        # If someone is not logged in then the buttons remain deactivated
        def checkLogin(event):
            # Obtain login status. To change valid usernames and password please see constants.py
            self.username = self.usernameEntry.get()
            self.password = self.passwordEntry.get()
            self.loggedIn = self.username in acceptableUsernames and self.password in acceptablePasswords

            # Once logged in, enable the save location and help buttons
            if self.loggedIn:
                self.loginWindow.destroy()

            # If incorrect username or password, create popup notifying the user
            else:
                incorrectLoginName = 'Incorrect Login'
                incorrectLoginText = 'You have entered either a wrong name or password. Please reenter your credentials or contact nickschw@umd.edu for help'
                incorrectLoginWindow = MessageWindow(self, incorrectLoginName, incorrectLoginText)

                # Clear username and password entries
                self.usernameEntry.delete(0, 'end')
                self.passwordEntry.delete(0, 'end')

        # Create popup window with fields for username and password
        self.loginWindow = tk.Toplevel(padx=loginPadding, pady=loginPadding)
        self.loginWindow.title('Login Window')

        # Center and bring popup to the top
        self.loginWindow.attributes('-topmost', True)
        self.eval(f'tk::PlaceWindow {str(self.loginWindow)} center')

        login_text = 'Please enter UMD username.'
        password_text = 'Please enter password.'
        button_text = 'Login'

        self.usernameLabel = ttk.Label(self.loginWindow, text=login_text, **text_opts)
        self.usernameEntry = ttk.Entry(self.loginWindow, **entry_opts)
        self.passwordLabel = ttk.Label(self.loginWindow, text=password_text, **text_opts)
        self.passwordEntry = ttk.Entry(self.loginWindow, show='*', **entry_opts)
        self.loginButton = ttk.Button(self.loginWindow, text=button_text, command=lambda event='Okay Press': checkLogin(event), style='Accent.TButton')

        # User can press 'Return' key to login instead of loginButton
        self.loginWindow.bind('<Return>', checkLogin)

        self.usernameLabel.pack()
        self.usernameEntry.pack()
        self.passwordLabel.pack()
        self.passwordEntry.pack()
        self.loginButton.pack()

        self.loginWindow.wait_window()

    # Special function for closing the window and program
    def on_closing(self):
        # Open power supply and voltage divider switch and close load switch
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Load Switch', False)
        self.operateSwitch('Voltage Divider Switch', False)

        if not DEBUG_MODE:
            # Stop NI communication
            self.NI_DAQ.close()

            # Close visa communication with scope
            if hasattr(self, 'scope'):
                try:
                    self.scope.inst.close()
                except visa.errors.VisaIOError:
                    pass

        # Close plots
        plt.close('all')

        # Cancel all scheduled callbacks
        for after_id in self.tk.eval('after info').split():
            self.after_cancel(after_id)

        self.quit()
        self.destroy()

    def readScope(self, channel):
        try:
            pin = self.scopePins[channel]
            value = self.scope.get_data(pin)
            if channel == 'Load Voltage':
                value *= voltageDivider
            elif channel == 'Load Current':
                value /= pearsonCoil
            else:
                print('Incorrect channel chosen')

        except:
            value = np.nan
            print('Not connected to the scope')


        return value

    def readNI(self, channel):
        try:
            values = self.NI_DAQ.read()
            value = values[channel]
            if channel == 'Power Supply Voltage':
                value *= maxVoltagePowerSupply / maxVoltageInput
            elif channel == 'Power Supply Current':
                value *= maxCurrentPowerSupply / maxVoltageInput
            else:
                print('Incorrect channel chosen')

        except Exception as e:
            value = np.nan
            print('Not connected to the NI DAQ')
            print(e)

        return value

    def getChargingTestVoltages(self):
        if hasattr(self, 'waveform') and not self.discharged and len(self.waveform) != 0:
            powerSupplyVoltage = np.abs(self.waveform[0] + (np.random.rand() - 0.5) * 0.01)
            capacitorVoltage = np.abs(self.waveform[0] + (np.random.rand() - 0.5) * 0.01)
            powerSupplyCurrent = np.random.rand() * 0.01
            values = [powerSupplyVoltage, powerSupplyCurrent, capacitorVoltage]

            # remove the first element so that the next element is acquired on the next iteration
            self.waveform = self.waveform[1:]
        else:
            powerSupplyVoltage = np.random.rand() * 0.01
            powerSupplyCurrent = np.random.rand() * 0.01
            capacitorVoltage = np.random.rand() * 0.01
            values = [powerSupplyVoltage, powerSupplyCurrent, capacitorVoltage]

        return values

    def getDischargeTestValues(self):
        time = np.linspace(0, 1, 100)
        tUnit = 's'
        voltage = self.chargeVoltage * voltageDivider * np.exp( - time / RCTime)
        current = pearsonCoil * np.exp( - time / RCTime)
        return (voltage, current, time, tUnit)

    def intermittentVoltageDivider(self):
        self.operateSwitch('Voltage Divider Switch', True)
        time.sleep(switchWaitTime)
        self.voltageDividerClosed = True

    def updateChargeValues(self):
        voltagePSPoint = np.nan
        currentPSPoint = np.nan
        self.capacitorVoltagePoint = np.nan

        # not applicable on startup
        if hasattr(self, 'NI_DAQ'):
            if not DEBUG_MODE:
                voltages = self.NI_DAQ.h_task_ai.read()
                # Retrieve charging data
                # voltages = self.NI_DAQ.data
            else:
                voltages = self.getChargingTestVoltages()
            voltagePSPoint = voltages[0] * maxVoltagePowerSupply / maxVoltageInput
            currentPSPoint = (voltages[1] + 10) * maxCurrentPowerSupply / maxVoltageInput # +10 because theres an offset for whatever reason
            # voltagePSPoint = voltages[]

            # Only record the voltage when the switch is closed
            # This occurs during all of charging and intermittently when the capacitor is isolated
            if self.voltageDividerClosed:
                self.capacitorVoltagePoint = voltages[2] * voltageDivider * attenuator
                self.capacitorVoltageText.set(f'V{CapacitorSuperscript}: {np.abs(self.capacitorVoltagePoint) / 1000:.2f} kV')

        self.voltagePSText.set(f'V{PSSuperscript}: {np.abs(voltagePSPoint) / 1000:.2f} kV')
        self.currentPSText.set(f'I{PSSuperscript}: {np.abs(currentPSPoint) * 1000:.2f} mA')

        # Once the DAQ has made a measurement, open up the switch again
        if self.voltageDividerClosed and self.countdownStarted:
            self.operateSwitch('Voltage Divider Switch', False)
            self.voltageDividerClosed = False

        if not self.idleMode and self.voltageDividerClosed:
            self.progress['value'] = 100 * self.capacitorVoltagePoint / 1000 / self.chargeVoltage

        # Logic heirarchy for charge state and countdown text
        if self.discharged:
            self.chargeStateText.set('Discharged!')
            self.countdownText.set(f'Coundown: 0.0 s')
        elif self.charged:
            self.chargeStateText.set('Charged')
            self.countdownText.set(f'Coundown: {self.countdownTime:.2f} s')
        else:
            self.chargeStateText.set('Not Charged')
            self.countdownText.set('Countdown: N/A')

        if self.charging:
            self.timePoint = time.time() - self.beginChargeTime

            self.chargeTime = np.append(self.chargeTime, self.timePoint)
            self.chargeVoltagePS = np.append(self.chargeVoltagePS, voltagePSPoint)
            self.chargeCurrentPS = np.append(self.chargeCurrentPS, currentPSPoint)
            self.capacitorVoltage = np.append(self.capacitorVoltage, self.capacitorVoltagePoint)

            # Plot the new data
            self.replotCharge()

            # Voltage reaches a certain value of chargeVoltage to begin countown clock
            if self.capacitorVoltagePoint >= chargeVoltageLimit * self.chargeVoltage * 1000 or self.countdownStarted:
                # Start countdown only once
                if not self.countdownStarted:
                    self.countdownTimeStart = time.time()
                    self.charged = True
                    self.countdownStarted = True

                    # Open power supply switch
                    self.operateSwitch('Power Supply Switch', False)

                    # Actually begin discharging power supply
                    time.sleep(0.5) # allow some time for power supply switch to open
                    self.powerSupplyRamp(action='discharge')

                    if not DEBUG_MODE:
                        # Start repeated timer to measure capacitor at regular intervals
                        self.switchTimer = RepeatedTimer(measureInterval, self.intermittentVoltageDivider)

                # Time left before discharge
                self.countdownTime = self.holdChargeTime - (time.time() - self.countdownTimeStart)

                # Set countdown time to 0 seconds once discharged
                if self.countdownTime <= 0.0:
                    self.countdownTime = 0.0
                    self.countdownStarted = False
                    self.discharge()

            # # Discharge if the voltage is not increasing
            # # This is determined if the charge does not exceed a small percentage of the desired charge voltage within a given period of time
            # notCharging = voltagePSPoint <= epsilonDesiredChargeVoltage * self.chargeVoltage and self.timePoint > chargeTimeLimit
            # if notCharging:
            #     self.discharge()
            #     print('Not charging')
            #
            # # Also discharge if charging but not reaching the desired voltage
            # # This is determined by checking for steady state
            # # In the future it would be better to implement a more rigorous statistical test, like the student t
            # steadyState = False
            # window = 20 # number of points at the end of the data set from which to calculate slope
            # nWindows = 10 # number of windows to implement sliding window
            # lengthArray = len(self.chargeTime)
            # slopes, _ = np.array([np.polyfit(self.chargeTime[lengthArray - window - i:lengthArray - i], self.chargeVoltagePS[lengthArray - window - i:lengthArray - i], 1) for i in range(nWindows)]).T # first order linear regression
            # steadyState = np.std(slopes) / np.mean(slopes) < 0.05
            # if steadyState:
            #     self.discharge()
            #     print('Steady state reached without charging to desired voltage')

        self.after(int(1000 / refreshRate), self.updateChargeValues)

    # Removes all lines from a figure
    def clearFigLines(self, fig):
        axes = fig.axes
        for axis in axes:
            if len(axis.lines) != 0:
                for i in range(len(axis.lines)):
                    axis.lines[0].remove()

    def replotCharge(self):
        self.chargeVoltageLine.set_data(self.chargeTime, self.chargeVoltagePS / 1000)
        self.chargeCurrentLine.set_data(self.chargeTime, self.chargeCurrentPS * 1000)

        nanIndices = np.isnan(self.capacitorVoltage)
        self.capacitorVoltageLine.set_data(self.chargeTime[~nanIndices], self.capacitorVoltage[~nanIndices] / 1000)

        if self.timePoint > plotTimeLimit:
            self.chargePlot.ax.set_xlim(self.timePoint - plotTimeLimit, self.timePoint)
        else:
            self.chargePlot.ax.set_xlim(0, plotTimeLimit)

        if len(self.capacitorVoltage) != 0 and 1.2 * max(self.chargeVoltagePS) / 1000 > voltageYLim:
            self.chargePlot.ax.set_ylim(0, 1.2 * max(self.chargeVoltagePS) / 1000)

        self.bm.update()

    def replotDischarge(self):
        # Remove lines every time the figure is plotted
        self.clearFigLines(self.dischargePlot.fig)
        self.dischargeVoltageAxis.set_xlabel(f'Time ({self.dischargeTimeUnit})')

        # Add plots
        self.dischargeVoltageAxis.plot(self.dischargeTime, self.dischargeVoltageLoad / 1000, color=voltageColor, label='V$_{load}$')
        self.dischargeCurrentAxis.plot(self.dischargeTime, self.dischargeCurrentLoad, color=currentColor, label='I$_{load}$')
        self.dischargeVoltageAxis.plot(self.dischargeFitTime, self.dischargeFitVoltage / 1000, color=fitColor, label='V$_{fit}$')
        self.dischargePlot.updatePlot()

    def resetChargePlot(self):
        # Set time and voltage to empty array
        self.chargeTime = np.array([])
        self.chargeVoltagePS = np.array([])
        self.chargeCurrentPS = np.array([])
        self.capacitorVoltage = np.array([])
        self.chargeFitTime = np.array([])
        self.chargeFitVoltage = np.array([])

        self.fitVoltageLine.set_data(self.chargeFitTime, self.chargeFitVoltage / 1000)

        # Also need to reset the twinx axis
        # self.chargeCurrentAxis.relim()
        # self.chargeCurrentAxis.autoscale_view()

        self.timePoint = 0
        self.capacitorVoltagePoint = 0
        self.replotCharge()

    def resetDischargePlot(self):
        # Set time and voltage to empty array
        self.dischargeTime = np.array([])
        self.dischargeFitTime = np.array([])
        self.dischargeVoltageLoad = np.array([])
        self.dischargeCurrentLoad = np.array([])
        self.dischargeFitVoltage = np.array([])

        # Also need to reset the twinx axis
        self.dischargeCurrentAxis.relim()
        self.dischargeCurrentAxis.autoscale_view()

        self.replotDischarge()

    def reset(self):
        # Clear all user inputs
        self.serialNumberEntry.delete(0, 'end')
        self.chargeVoltageEntry.delete(0, 'end')
        self.holdChargeTimeEntry.delete(0, 'end')

        # Reset all boolean variables, time, and checklist
        self.charged = False
        self.charging = False
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.countdownStarted = False
        self.idleMode = True
        self.checklist_Checkbuttons = {}

        # Close voltage divider
        self.operateSwitch('Voltage Divider Switch', True)
        self.voltageDividerClosed = True

        # Reset plots
        self.resetChargePlot()
        self.resetDischargePlot()

        # Disable all buttons if logged in
        self.disableButtons()

        if hasattr(self, 'scope'):
            self.scope.reset() # Reset the scope

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')
