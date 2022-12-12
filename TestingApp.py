import ttkbootstrap as ttk
from ttkbootstrap import validation, scrolled, window
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os
import webbrowser
import nidaqmx
import scipy.optimize, scipy.signal
from scipy.ndimage import uniform_filter1d
import datetime
from threading import Thread
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

class TestingApp(ttk.Window):
    def __init__(self):
        super().__init__(themename=themename)
        style = ttk.Style()
        self.colors = style.colors

        style.configure('TButton', **button_opts)
        style.configure('TFrame', **frame_opts)
        style.configure('TLabelframe.Label', **text_opts)
        style.configure('TEntry', **entry_opts)
        style.configure('TLabel', **text_opts)
        style.configure('TRadiobutton', **text_opts)
        style.configure('TNotebook.Tab', **text_opts)
        style.configure('TCheckbutton', **text_opts)
        self.option_add('*TCombobox*Listbox.font', text_opts)
        
        # Special code for styling big red button
        style.configure('big.TButton', font=(None, 24,), justify='center', background=self.colors.danger)
        style.map('big.TButton', background=[('active', '#bc0303')])

        # Initialize pins to default values
        self.scopePins = scopeChannelDefaults
        self.charge_ao_Pins = charge_ao_defaults
        self.systemStatus_Pins = systemStatus_defaults
        self.do_Pins = do_defaults
        self.diagnostics_Pins = diagnostics_defaults

    def center_app(self):
        self.update_idletasks()
        width = self.winfo_width()
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = width + 2 * frm_width
        height = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = self.winfo_screenwidth() // 2 - win_width // 2
        y = self.winfo_screenheight() // 2 - win_height // 2
        self.geometry(f'+{x}+{0}')
        self.deiconify()  
        
    # There are two pieces of hardware important for communication with the test cart
    # The NI panel extender provides an analog output and two analog inputs to read/write to the power supply during charging
    # The Oscilloscope is triggered when the capacitor discharges and reads waveform from the discharge
    def init_DAQ(self):
        # We need both an analog input and output
        self.NI_DAQ = NI_DAQ(systemStatus_name, discharge_name, systemStatus_sample_rate,
                             systemStatus_channels=self.systemStatus_Pins,
                             charge_ao_channels=self.charge_ao_Pins,
                             diagnostics=self.diagnostics_Pins)

        # Discharge the power supply on startup
        self.powerSupplyRamp(action='discharge')

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

        # Setup delays
        for trigger_values in pulseGeneratorOutputs.values():
            chan = trigger_values['chan']
            delay = trigger_values['delay']
            self.pulseGenerator.setDelay(chan, delay)

    def saveResults(self):
        '''MASTER FILE SAVE'''
        # Create master file if it does not already exist
        self.runNumber = f'{0:05d}'
        # Date
        now = datetime.datetime.now()
        self.runDate = now.date().strftime('%Y_%m_%d')
        self.runTime = now.time().strftime('%H:%M:%S')
        
        master_columnsNames = [master_columns[variable] for variable in master_columns if hasattr(self, variable)]

        if resultsMasterName not in os.listdir(self.saveFolder):
            resultsMaster_df = pd.DataFrame(columns=master_columnsNames)
            resultsMaster_df.to_csv(f'{self.saveFolder}/{resultsMasterName}', index=False)
        else:
            resultsMaster_df = pd.read_csv(f'{self.saveFolder}/{resultsMasterName}')
            runNumbers = resultsMaster_df[master_columns['runNumber']]
            runNumber = max(runNumbers.astype(int)) + 1
            self.runNumber = f'{runNumber:05d}'
            print(self.runNumber)

        # Save master results
        resultMaster = []
        for variable in master_columns:
            if hasattr(self, variable):
                resultMaster.append(getattr(self, variable))

        print(resultMaster)
        print(master_columnsNames)
        resultMaster_df = pd.DataFrame(columns=master_columnsNames)
        resultMaster_df.loc[0] = resultMaster
        resultsMaster_df = pd.concat([resultsMaster_df, resultMaster_df])
        resultsMaster_df.to_csv(f'{self.saveFolder}/{resultsMasterName}', index=False)

        '''RUN FILE SAVE'''
        # Create a folder for today's date if it doesn't already exist
        if self.runDate not in os.listdir(self.saveFolder):
            os.mkdir(f'{self.saveFolder}/{self.runDate}')

        if SHOT_MODE:
            self.filename = f'CMFX_{self.runNumber}.csv'
        else:
            self.filename = f'CMFX_{self.serialNumber}.csv'

        # These results are listed in accordance with the 'columns' variable in constants.py
        # If the user would like to add or remove fields please make those changes in constant.py
        results = [getattr(self, variable) for variable in single_columns if hasattr(self, variable)]

        # Creates a data frame which is easier to save to csv formats
        results_df = pd.DataFrame([pd.Series(val, dtype='object') for val in results]).T
        results_df.columns = [single_columns[variable]['name'] for variable in single_columns if hasattr(self, variable)]
        results_df.to_csv(f'{self.saveFolder}/{self.runDate}/{self.filename}', index=False)

    # Read in a csv file and plot those results
    def readResults(self):
        readFile = filedialog.askopenfilename(filetypes=[('Comma separated values', '.csv')])
        if readFile != '':
            results_df = pd.read_csv(readFile)

            # Reset program and allow user to reset
            self.reset()
            self.resetButton.configure(state='normal')

            for key, value in single_columns.items():
                if value['type'] == 'scalar':
                    if value['name'] in results_df:
                        self.__dict__.update({key: results_df[value['name']].values[0]})
                    else:
                        self.__dict__.update({key: np.nan})
                else:
                    if value['name'] in results_df:
                        self.__dict__.update({key: results_df[value['name']].dropna().values})
                    else:
                        self.__dict__.update({key: np.zeros(0)})

            # Place values for all user inputs and plots
            self.serialNumberEntry.insert(0, self.serialNumber)
            self.chargeVoltageEntry.insert(0, self.chargeVoltage)
            self.holdChargeTimeEntry.insert(0, self.holdChargeTime)

            self.replotCharge()
            self.replotDischarge()

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
        self.setPinWindow = window.Toplevel(padx=setPinsPaddingX, pady=setPinsPaddingY)
        self.setPinWindow.title('Set Pins')
        # Bring pop up to the center and top
        self.eval(f'tk::PlaceWindow {str(self.setPinWindow)} center')
        self.setPinWindow.attributes('-topmost', True)

        # This function places pin labels and dropdown menus in the popup window
        def selectPins(channelDefaults, options):
            pins = {}
            nCols, nRows = self.setPinWindow.grid_size()
            for i, channel in enumerate(channelDefaults):
                channelVariable = ttk.StringVar()
                channelVariable.set(channelDefaults[channel])
                label = ttk.Label(self.setPinWindow, text=channel, **text_opts)
                drop = ttk.OptionMenu(self.setPinWindow, channelVariable, channelDefaults[channel], *options)

                label.grid(row=nRows + i, column=0, sticky='w', padx=(0, setPinsPaddingX), pady=(0, setPinsPaddingY))
                drop.grid(row=nRows + i, column=1, sticky='w', padx=(setPinsPaddingX, 0), pady=(0, setPinsPaddingY))

                pins[channel] = channelVariable

            return pins

        scopePinsOptions = selectPins(scopeChannelDefaults, scopeChannelOptions)
        charge_ao_PinsOptions = selectPins(charge_ao_defaults, charge_ao_options)
        systemStatus_PinsOptions = selectPins(systemStatus_defaults, systemStatus_options)
        do_PinsOptions = selectPins(do_defaults, do_options)
        diagnostics_PinsOptions = selectPins(diagnostics_defaults, diagnostics_options)

        # Button on the bottom
        nCols, nRows = self.setPinWindow.grid_size()
        buttonFrame = ttk.Frame(self.setPinWindow)
        buttonFrame.grid(row=nRows + 1, columnspan=2)
        # Once the okay button is pressed, assign the pins
        def assignPins():
            for channel in scopePinsOptions:
                self.scopePins[channel] = scopePinsOptions[channel].get()

            for channel in charge_ao_PinsOptions:
                self.charge_ao_Pins[channel] = charge_ao_PinsOptions[channel].get()

            for channel in systemStatus_PinsOptions:
                self.systemStatus_Pins[channel] = systemStatus_PinsOptions[channel].get()
            for channel in do_PinsOptions:
                self.do_Pins[channel] = do_PinsOptions[channel].get()

            for channel in diagnostics_PinsOptions:
                self.diagnostics_Pins[channel] = diagnostics_PinsOptions[channel].get()

            print(self.scopePins)
            print(self.charge_ao_Pins)
            print(self.systemStatus_Pins)
            print(self.do_Pins)
            print(self.diagnostics_Pins)
            self.setPinWindow.destroy()

        okayButton = ttk.Button(buttonFrame, text='Set Pins', command=assignPins, bootstyle='success')
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
        cancelButton = ttk.Button(checklistWindow.bottomFrame, text='Cancel', command=checklistWindow.destroy, bootstyle='danger')
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
                    task.do_channels.add_do_chan(f'{discharge_name}/{digitalOutName}/{self.do_Pins[switchName]}')
                    task.write(state)
                    print(f'{switchName} in {state} state')

            except Exception as e:
                print(e)
                print('Cannot operate switches')

    # Sends signal from NI analog output to charge or discharge the capacitor
    def powerSupplyRamp(self, action='discharge'):
        if action == 'charge':
            value = self.chargeVoltage / maxVoltagePowerSupply * maxVoltageInput * 1000
        else:
            value = 0

        if not DEBUG_MODE:
            self.NI_DAQ.write_value(value)

    def charge(self):
        # Popup window appears to confirm charging
        chargeConfirmName = 'Begin charging'
        chargeConfirmText = 'Are you sure you want to begin charging?'
        chargeConfirmWindow = MessageWindow(self, chargeConfirmName, chargeConfirmText)

        cancelButton = ttk.Button(chargeConfirmWindow.bottomFrame, text='Cancel', command=chargeConfirmWindow.destroy, bootstyle='danger')
        cancelButton.pack(side='left')

        chargeConfirmWindow.wait_window()

        # If the user presses the Okay button, charging begins
        if chargeConfirmWindow.OKPress:
            self.NI_DAQ.reset_systemStatus() # Only start gathering data when beginning to charge

            self.idleMode = False

            # Operate switches
            self.operateSwitch('Load Switch', True)
            time.sleep(switchWaitTime)
            self.operateSwitch('Power Supply Switch', True)
            # LASER TEST	
            # self.operateSwitch('Voltage Divider Switch', True)	
            # self.voltageDividerClosed = True
            time.sleep(switchWaitTime)

            # Actually begin charging power supply
            self.powerSupplyRamp(action='charge')

            # Begin tracking time
            self.beginChargeTime = time.time()
            self.charging = True

            if SHOT_MODE:
                # Record base pressures when charging begins
                self.recordPressure()

    def discharge(self):
        def popup():
            # Popup window to confirm discharge
            dischargeConfirmName = 'Discharge'
            dischargeConfirmText = 'Are you sure you want to discharge?'
            dischargeConfirmWindow = MessageWindow(self, dischargeConfirmName, dischargeConfirmText)

            cancelButton = ttk.Button(dischargeConfirmWindow.bottomFrame, text='Cancel', command=dischargeConfirmWindow.destroy, bootstyle='danger')
            cancelButton.pack(side='left')

            dischargeConfirmWindow.wait_window()

            if dischargeConfirmWindow.OKPress:
                # Force power supply to discharge
                self.powerSupplyRamp(action='discharge')

                # Operate switches
                self.operateSwitch('Power Supply Switch', False)
                time.sleep(switchWaitTime)
                self.operateSwitch('Load Switch', False)

                self.charging = False
                self.discharged = True

                self.pulseGenerator.triggerStart()
                self.NI_DAQ.discharge_reader.read_many_sample(self.NI_DAQ.dischargeData)

        if not self.idleMode:
            if not self.charged:
                popup()

            else:
                self.operateSwitch('Voltage Divider Switch', True)	
                time.sleep(0.5)	# Hold central conductor at high voltage for a while to avoid bouncing switch until gas puff starts
                self.pulseGenerator.triggerStart()
                self.NI_DAQ.discharge_reader.read_many_sample(self.NI_DAQ.dischargeData)

                # Wait a while before closing the mechanical dump switch
                time.sleep(hardCloseWaitTime)	
                self.operateSwitch('Load Switch', False)

            # Save discharge on a separate thread	
            print('Saving discharge...')
            # self.saveDischarge()
            self.saveDischarge_thread = Thread(target=self.saveDischarge)
            self.saveDischarge_thread.start()
            print('Discharge saved')

        else:
            popup()

        # Disable all buttons except for reset, if logged in
        self.disableButtons()
        if self.loggedIn:
            self.resetButton.configure(state='normal')

    def replotCharge(self):
        self.chargeVoltageLine.set_data(self.chargeTime, self.chargeVoltagePS / 1000)
        self.chargeCurrentLine.set_data(self.chargeTime, self.chargeCurrentPS * 1000)

        # If the capacitor is only being read every so often, only plot non nan values
        try:
            nanIndices = np.isnan(self.capacitorVoltage)
            if hasattr(self, 'capacitorVoltageFiltered'):
                self.capacitorVoltageLine.set_data(self.chargeTime[~nanIndices], self.capacitorVoltageFiltered / 1000)
            else:
                self.capacitorVoltageLine.set_data(self.chargeTime[~nanIndices], self.capacitorVoltage[~nanIndices] / 1000)
        except IndexError:
            print('Mismatch in shape')

        if self.timePoint > plotTimeLimit:
            self.chargePlot.ax.set_xlim(self.timePoint - plotTimeLimit, self.timePoint)
        else:
            self.chargePlot.ax.set_xlim(0, plotTimeLimit)

        if len(self.capacitorVoltage) != 0 and 1.2 * max(self.chargeVoltagePS) / 1000 > voltageYLim:
            self.chargePlot.ax.set_ylim(0, 1.2 * max(self.chargeVoltagePS) / 1000)

        try:
            self.bm.update()
        except ValueError:
            print('Mismatch in shape')

    # Turn on safety lights inside the control room and outside the lab
    def safetyLights(self):
        print('Turn on safety lights')

    def emergency_off(self):
        print('Emergency Off')
        # Force power supply to discharge
        self.powerSupplyRamp(action='discharge')

        # Operate switches
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Load Switch', False)
        self.operateSwitch('Voltage Divider Switch', False)

        self.charging = False
        self.discharged = True
        self.idleMode = True

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
        self.loginWindow = window.Toplevel(padx=loginPadding, pady=loginPadding)
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
        self.loginButton = ttk.Button(self.loginWindow, text=button_text, command=lambda event='Okay Press': checkLogin(event), bootstyle='success')

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
        self.powerSupplyRamp(action='discharge')

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

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')