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
from analysis import *
from indicator import *

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
        
        # Special code for styling big buttons
        style.configure('bigRed.TButton', font=(None, 24,), justify='center', background=self.colors.danger)
        style.configure('bigOrange.TButton', font=(None, 24,), justify='center', background=self.colors.warning)
        style.map('bigRed.TButton', background=[('active', '#e74c3c')])
        style.map('bigOrange.TButton', background=[('active', '#f39c12')])

        # Initialize pins to default values
        self.scopePins = scopeChannelDefaults
        self.charge_ao_Pins = charge_ao_defaults
        self.systemStatus_Pins = systemStatus_defaults
        self.do_Pins = do_defaults
        self.di_Pins = di_defaults
        self.diagnostics_Pins = diagnostics_defaults
        self.counters_Pins = counters_defaults

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
        self.NI_DAQ = NI_DAQ(systemStatus_sample_rate, systemStatus_channels=self.systemStatus_Pins,
                             charge_ao_channels=self.charge_ao_Pins, di_channels=self.di_Pins, diagnostics=self.diagnostics_Pins,
                             counters=self.counters_Pins, n_pulses=n_pulses)

        # Discharge the power supply on startup
        self.powerSupplyRamp(action='discharge')

        # Initialize the scope over ethernet
        if USING_SCOPE:
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
            runNumber = int(max(runNumbers)) + 1
            self.runNumber = f'{runNumber:05d}'

        # Save master results
        resultMaster = []
        for variable in master_columns:
            if hasattr(self, variable):
                resultMaster.append(getattr(self, variable))

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
            results_df = pd.read_csv(readFile, low_memory=False)

            # Reset program and allow user to reset
            self.resetButton.configure(state='normal')

            for variable, description in single_columns.items():
                if description['type'] == 'scalar':
                    if description['name'] in results_df:
                        scalar_data = results_df[description['name']].values[0]
                        setattr(self, variable, scalar_data)
                else:
                    if description['name'] in results_df:
                        array_data = results_df[description['name']].dropna().values
                        setattr(self, variable, array_data)

            # Place values for all user inputs and plots
            if SHOT_MODE:
                self.gasPuffEntry.delete(0, 'end')
                self.dumpDelayEntry.delete(0, 'end')
                self.gasPuffEntry.insert(0, self.gasPuffTime)
                self.dumpDelayEntry.insert(0, self.dumpDelay)
            else:
                self.serialNumberEntry.delete(0, 'end')
                self.holdChargeTimeEntry.delete(0, 'end')
                self.serialNumberEntry.insert(0, self.serialNumber)
                self.holdChargeTimeEntry.insert(0, self.holdChargeTime)

            self.chargeVoltageEntry.delete(0, 'end')
            self.chargeVoltageEntry.insert(0, self.chargeVoltage)

            # Load pre- and post-shot notes
            self.preShotNotesEntry.text.delete('1.0', 'end')
            self.postShotNotesEntry.text.delete('1.0', 'end')
            self.preShotNotesEntry.text.insert('1.0', self.preShotNotes)
            self.postShotNotesEntry.text.insert('1.0', self.postShotNotes)

            self.replotCharge()

            # Load the results plots
            self.setData(self.resultsPlotData)
            self.resultsPlotViewer.replot()

            # Load the analysis plots
            self.performAnalysis()
            self.analysisPlotViewer.replot()

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
        di_PinsOptions = selectPins(di_defaults, di_options)
        diagnostics_PinsOptions = selectPins(diagnostics_defaults, diagnostics_options)
        counter_PinsOptions = selectPins(counters_defaults, counters_options)

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

            for channel in di_PinsOptions:
                self.di_Pins[channel] = di_PinsOptions[channel].get()

            for channel in diagnostics_PinsOptions:
                self.diagnostics_Pins[channel] = diagnostics_PinsOptions[channel].get()

            for channel in counter_PinsOptions:
                self.counters_Pins[channel] = counter_PinsOptions[channel].get()

            print(self.scopePins)
            print(self.charge_ao_Pins)
            print(self.systemStatus_Pins)
            print(self.do_Pins)
            print(self.di_Pins)
            print(self.diagnostics_Pins)
            print(self.counters_Pins)
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

    def enableHV(self):
        # Popup window appears to confirm
        name = 'Enable HV?'
        text = 'Are you sure you want to enable HV?'
        enableHVWindow = MessageWindow(self, name, text)

        enableHVWindow.OKButton['text'] = 'Yes'
        cancelButton = ttk.Button(enableHVWindow.bottomFrame, text='Cancel', command=enableHVWindow.destroy, bootstyle='danger')
        cancelButton.pack(side='left')

        enableHVWindow.wait_window()

        if enableHVWindow.OKPress:
            self.operateSwitch('Enable HV', True)

    def operateSwitch(self, switchName, state):
        # If state is false, power supply switch opens and load switch closes
        # If state is true, power supply switch closes and load switch opens
        if not DEBUG_MODE:
            try:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(f'{self.do_Pins[switchName]}')
                    task.write(state)
                    print(f'{switchName} in {state} state')

            except Exception as e:
                print(e)
                print('Cannot operate switches')

    # Sends signal from NI analog output to charge or discharge the capacitor
    def powerSupplyRamp(self, action='discharge'):
        breakpoint()
        if action == 'charge':
            voltageValue = self.chargeVoltage / maxVoltagePowerSupply * maxAnalogInput * 1000
            currentValue = maxCurrentPowerSupply / maxCurrentPowerSupply * maxAnalogInput # Charge with maximum current
        else:
            voltageValue = 0
            currentValue = 0

        if not DEBUG_MODE:
            self.NI_DAQ.write_value(voltageValue, currentValue)

    def charge(self):
        # Determine whether there are any faults in the HV supply
        if any([not self.booleanIndicators['HV On'].state,
                not self.booleanIndicators['Interlock Closed'].state,
                self.booleanIndicators['Spark'].state,
                self.booleanIndicators['Over Temp Fault'].state,
                self.booleanIndicators['AC Fault'].state]):
            name = 'Power Supply Fault'
            text = 'Please evaluate power supply status. HV may not be enabled, interlock may be open, or there may be a fault.'

        else:
            name = 'Begin charging'
            text = 'Are you sure you want to begin charging?'

        # Popup window appears to confirm charging
        chargeConfirmWindow = MessageWindow(self, name, text)

        cancelButton = ttk.Button(chargeConfirmWindow.bottomFrame, text='Cancel', command=chargeConfirmWindow.destroy, bootstyle='danger')
        cancelButton.pack(side='left')

        chargeConfirmWindow.wait_window()

        # If the user presses the Okay button, charging begins
        if chargeConfirmWindow.OKPress:
            self.NI_DAQ.reset_systemStatus() # Only start gathering data when beginning to charge

            self.idleMode = False

            ### Operate switches ###
            # Open dump switch
            self.operateSwitch('Dump Switch', True)
            time.sleep(switchWaitTime)

            # Close power supply switch
            self.operateSwitch('Power Supply Switch', True)
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
        def discharge_switch():
            if not IGNITRON_MODE:
                self.operateSwitch('Load Switch', True)
                time.sleep(gasPuffWaitTime)	# Hold central conductor at high voltage for a while to avoid bouncing switch until gas puff starts

            # Start the pulse generator
            self.pulseGenerator.triggerStart()

            # Read from DAQ
            self.NI_DAQ.read_discharge()

            # Wait a while before closing the mechanical dump switch
            time.sleep(hardCloseWaitTime)	
            self.operateSwitch('Dump Switch', False)

            self.charging = False
            self.discharged = True

            # Save discharge on a separate thread
            self.saveDischarge_thread = Thread(target=self.saveDischarge)
            self.saveDischarge_thread.start()

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

                self.NI_DAQ.remove_tasks(self.NI_DAQ.dump_task_names + self.NI_DAQ.switch_task_names)

                # Operate switches
                self.operateSwitch('Power Supply Switch', False)
                time.sleep(switchWaitTime)

                discharge_switch()

        if not self.idleMode:
            if not self.charged:
                popup()
            else:
                discharge_switch()
        else:
            popup()

        # Disable all buttons except for reset, if logged in
        self.disableButtons()
        if self.loggedIn:
            self.resetButton.configure(state='normal')

    def replotCharge(self):
        self.chargeVoltageLine.set_data(self.chargeTime, np.abs(self.chargeVoltagePS) / 1000)
        self.chargeCurrentLine.set_data(self.chargeTime, self.chargeCurrentPS * 1000)

        # If the capacitor is only being read every so often, only plot non nan values
        try:
            nanIndices = np.isnan(self.capacitorVoltage)
            self.capacitorVoltageLine.set_data(self.chargeTime[~nanIndices], self.capacitorVoltage[~nanIndices] / 1000)
        except IndexError:
            print('Mismatch in shape')

        if self.timePoint + 0.2 * plotTimeLimit > plotTimeLimit:
            self.chargePlot.ax.set_xlim(self.timePoint - 0.8 * plotTimeLimit, self.timePoint + 0.2 * plotTimeLimit)
        else:
            self.chargePlot.ax.set_xlim(0, plotTimeLimit)

        if len(self.capacitorVoltage) != 0 and 1.2 * max(self.capacitorVoltage) / 1000 > voltageYLim:
            self.chargePlot.ax.set_ylim(0, 1.2 * max(self.capacitorVoltage) / 1000)

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

        # Close the switch tasks so we can close the switches with hardware instead of software
        if hasattr(self, 'NI_DAQ'):
            self.NI_DAQ.remove_tasks(self.NI_DAQ.dump_task_names + self.NI_DAQ.switch_task_names)

        # Operate switches
        self.operateSwitch('Enable HV', False)
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Dump Switch', False)
        self.operateSwitch('Load Switch', False)

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

        # Close the switch tasks so we can close the switches with hardware instead of software
        if hasattr(self, 'NI_DAQ'):
            self.NI_DAQ.remove_tasks(self.NI_DAQ.dump_task_names + self.NI_DAQ.switch_task_names)

        # Open power supply and Cap Switch and close load switch
        self.operateSwitch('Enable HV', False)
        self.operateSwitch('Power Supply Switch', False)
        time.sleep(switchWaitTime)
        self.operateSwitch('Dump Switch', False)
        self.operateSwitch('Load Switch', False)

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
        current = pearsonCoilDischarge * np.exp( - time / RCTime)
        return (voltage, current, time, tUnit)

    # Popup window for help
    def help(self):
        webbrowser.open(f'{githubSite}/blob/main/README.md')