import tkinter as tk
from tkinter import ttk, filedialog
import sv_ttk
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
from console import *

# Change nidaqmx read/write to this format? https://github.com/AppliedAcousticsChalmers/nidaqmxAio

# Tkinter has quite a high learning curve. If attempting to edit this source code without experience, I highly
# recommend going through some tutorials. The documentation on tkinter is also quite poor, but
# this website has the best I can find (http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm). At times you may
# need to manually go into the tkinter source code to investigate the behavior/capabilities of some code.

class TestingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # set theme
        sv_ttk.set_theme('light')

        # Change style
        style = ttk.Style(self)
        style.configure('TButton', **button_opts)
        style.configure('TCheckbutton', **text_opts)
        style.configure('TLabelframe.Label', **text_opts)

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
            time.sleep(switchWaitTime)

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
            dataarray = self.scope.get_data(pin)
            if channel == 'Load Voltage':
                dataarray *= voltageDivider
            elif channel == 'Load Current':
                dataarray /= pearsonCoil
            else:
                print('Incorrect channel chosen')

        except:
            dataarray = np.nan
            print('Not connected to the scope')


        return dataarray

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

    # Removes all lines from a figure
    def clearFigLines(self, fig):
        axes = fig.axes
        for axis in axes:
            if len(axis.lines) != 0:
                for i in range(len(axis.lines)):
                    axis.lines[0].remove()

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')
