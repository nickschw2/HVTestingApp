import tkinter as tk
import numpy as np
import pandas as pd
from tkinter import ttk, filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import time
import os
import nidaqmx
from constants import *

class MainApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('HV Capacitor Testing')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        # Row for user inputs on the top
        self.userInputs = tk.Frame(self)
        self.userInputs.grid(row=0, columnspan=3, sticky='ns')

        # Charge voltage and desired hold charge time
        self.serialNumberLabel = tk.Label(self.userInputs, text='Cap Serial #:', **text_opts)
        self.chargeVoltageLabel = tk.Label(self.userInputs, text='Charge (kV):', **text_opts)
        self.holdChargeTimeLabel = tk.Label(self.userInputs, text='Hold Charge (s):', **text_opts)

        self.serialNumberEntry = tk.Entry(self.userInputs, width=userInputWidth, **text_opts)
        self.chargeVoltageEntry = tk.Entry(self.userInputs, width=userInputWidth, **text_opts)
        self.holdChargeTimeEntry = tk.Entry(self.userInputs, width=userInputWidth, **text_opts)

        self.userInputOkayButton = tk.Button(self.userInputs, text='Okay', command=self.setUserInputs, **button_opts)
        self.userInputSetText = tk.StringVar()
        self.userInputSetText.set('      ')
        self.userInputSetLabel = tk.Label(self.userInputs, textvariable=self.userInputSetText, **text_opts)

        self.serialNumberLabel.pack(side='left')
        self.serialNumberEntry.pack(side='left', padx=(0, userInputPadding))
        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.holdChargeTimeLabel.pack(side='left')
        self.holdChargeTimeEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')
        self.userInputSetLabel.pack(side='left')

        # Column for labels on the left
        self.grid_columnconfigure(0, w=1)
        self.labels = tk.Frame(self)
        self.labels.grid(row=1, column=0)

        # Voltage and current are read from both the power supply and the load
        self.voltageLoadText = tk.StringVar()
        self.voltagePSText = tk.StringVar()
        self.currentLoadText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.chargeStateText = tk.StringVar()
        self.countdownText = tk.StringVar()

        self.voltageLoadLabel = tk.Label(self.labels, textvariable=self.voltageLoadText, **text_opts)
        self.voltagePSLabel = tk.Label(self.labels, textvariable=self.voltagePSText, **text_opts)
        self.currentLoadLabel = tk.Label(self.labels, textvariable=self.currentLoadText, **text_opts)
        self.currentPSLabel = tk.Label(self.labels, textvariable=self.currentPSText, **text_opts)
        self.chargeStateLabel = tk.Label(self.labels, textvariable=self.chargeStateText, **text_opts)
        self.countdownLabel = tk.Label(self.labels, textvariable=self.countdownText, **text_opts)

        self.voltageLoadLabel.pack()
        self.voltagePSLabel.pack()
        self.currentLoadLabel.pack()
        self.currentPSLabel.pack()
        self.chargeStateLabel.pack()
        self.countdownLabel.pack()

        # Row for buttons on the bottom
        self.grid_rowconfigure(2, w=1)
        self.buttons = tk.Frame(self)
        self.buttons.grid(row=2, columnspan=3, sticky='ns')

        # Button definitions and placement
        self.saveLocationButton = tk.Button(self.buttons, text='Save Location',
                                    command=self.setSaveLocation, bg=green, fg=white, **button_opts)
        self.checklistButton = tk.Button(self.buttons, text='Begin Checklist',
                                    command=self.checklist, bg=green, fg=white, **button_opts)
        self.chargeButton = tk.Button(self.buttons, text='Charge',
                                    command=self.charge, bg=yellow, fg=white, **button_opts)
        self.dischargeButton = tk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bg=orange, fg=white, **button_opts)
        self.emergency_offButton = tk.Button(self.buttons, text='Emergency Off',
                                    command=self.emergency_off, bg=red, fg=white, **button_opts)
        self.resetButton = tk.Button(self.buttons, text='Reset',
                                    command=self.reset, bg=red, fg=white, **button_opts)

        self.saveLocationButton.pack(side='left', padx=buttonPadding)
        self.checklistButton.pack(side='left', padx=buttonPadding)
        self.chargeButton.pack(side='left', padx=buttonPadding)
        self.dischargeButton.pack(side='left', padx=buttonPadding)
        self.emergency_offButton.pack(side='left', padx=buttonPadding)
        self.resetButton.pack(side='left', padx=buttonPadding)

        # Configure Graphs
        self.grid_rowconfigure(1, w=1)
        self.grid_columnconfigure(1, w=1)
        self.grid_columnconfigure(2, w=1)

        # Plot of charge and discharge
        self.chargePlot = Can_Plot(self)
        self.dischargePlot = Can_Plot(self)

        self.chargeVoltageAxis = self.chargePlot.ax
        self.chargeCurrentAxis = self.chargePlot.ax.twinx()
        self.dischargeVoltageAxis = self.dischargePlot.ax
        self.dischargeCurrentAxis = self.dischargePlot.ax.twinx()

        self.chargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.chargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)
        self.dischargeVoltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.dischargeCurrentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.chargePlot.ax.set_xlabel('Time (s)')
        self.dischargePlot.ax.set_xlabel('Time (s)')

        self.chargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.chargeCurrentAxis.set_ylabel('Current (A)', color=currentColor)
        self.dischargeVoltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.dischargeCurrentAxis.set_ylabel('Current (A)', color=currentColor)

        self.chargePlot.ax.set_title('Charge Plot')
        self.dischargePlot.ax.set_title('Discharge Plot')

        self.chargePlot.ax.legend(handles=chargeHandles, loc='lower left')
        self.dischargePlot.ax.legend(handles=dischargeHandles, loc='lower left')

        self.chargePlot.grid(row=1, column=1, sticky='ew')
        self.dischargePlot.grid(row=1, column=2, sticky='ew')


        try:
            # On startup, disable buttons until login is correct
            self.disableButtons()
            self.loggedIn = False
            self.validateLogin()

            self.safetyLights()

            self.reset()

        except Exception as e:
            print(e)

    def setSaveLocation(self):
        self.saveFolder = filedialog.askdirectory(initialdir=os.path.dirname(os.path.realpath(__file__)), title='Select directory for saving results.')

        if self.userInputsSet:
            self.checklistButton.configure(state='normal')

    def saveResults(self):
        date = today.strftime('%Y%m%d')
        run = 1
        filename = f'{today}_{self.serialNumber}_{run}.csv'
        while filename in os.listdir(self.saveFolder):
            run += 1
            filename = f'{today}_{self.serialNumber}_{run}.csv'

        results = [self.serialNumber, self.chargeVoltage, self.holdChargeTime,
            self.chargeTime, self.chargeVoltagePS, self.chargeCurrentPS, self.dischargeTime,
            self.dischargeVoltageLoad, self.dischargeCurrentLoad]

        results_df = pd.DataFrame([pd.Series(val) for val in results]).T
        results_df.columns = columns
        results_df.to_csv(f'{self.saveFolder}/{filename}', index=False)

    def setUserInputs(self):
        try:
            self.serialNumber = str(self.serialNumberEntry.get())
            self.chargeVoltage = float(self.chargeVoltageEntry.get())
            self.holdChargeTime = float(self.holdChargeTimeEntry.get())

            if format.match(self.serialNumber) is None:
                raise ValueError

            self.userInputsSet = True
            self.checklistComplete()

            if hasattr(self, 'saveFolder'):
                self.checklistButton.configure(state='normal')

            self.userInputSetText.set('Set!')
            def resetSetText():
                self.userInputSetText.set('      ')
            self.after(displaySetTextTime, resetSetText)

        except ValueError:
            incorrectUserInputName = 'Invalid Input'
            incorrectUserInputText = 'Please reenter a valid string for serial number and numerical value for both the Charge Voltage and Hold Charge Time.'
            incorrectUserInputWindow = MessageWindow(self, incorrectUserInputName, incorrectUserInputText)

            incorrectUserInputWindow.wait_window()

            self.serialNumberEntry.delete(0, 'end')
            self.chargeVoltageEntry.delete(0, 'end')
            self.holdChargeTimeEntry.delete(0, 'end')

    def disableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, tk.Button):
                w.configure(state='disabled')

    def enableButtons(self):
        for w in self.buttons.winfo_children():
            if isinstance(w, tk.Button):
                w.configure(state='normal')

    def checklistComplete(self):
        complete = False
        complete = all([cb.get() for keys, cb in self.checklist_Checkbuttons.items()])

        if complete and self.userInputsSet and len(self.checklist_Checkbuttons) !=0:
            self.enableButtons()

    def checklist(self):
        self.disableButtons()
        self.checklistButton.configure(state='normal')
        self.checklist_win = tk.Toplevel()

        for i, step in enumerate(checklist_steps):
            self.checklist_Checkbuttons[f'c{i + 1}'] = tk.BooleanVar()
            button = tk.Checkbutton(self.checklist_win, variable=self.checklist_Checkbuttons[f'c{i + 1}'], text=f'Step {i + 1}: ' + step, command=self.checklistComplete)
            button.grid(row=i, column=0, sticky='w')

        self.OKButton = tk.Button(self.checklist_win, text='Okay', command=self.checklist_win.destroy, **button_opts)
        self.OKButton.grid(row=i + 1, column=0)

        self.checklist_win.wait_window()

    def charge(self):
        chargeConfirmName = 'Begin charging'
        chargeConfirmText = 'Are you sure you want to begin charging?'
        chargeConfirmWindow = MessageWindow(self, chargeConfirmName, chargeConfirmText)

        cancelButton = tk.Button(chargeConfirmWindow.bottomFrame, text='Cancel', command=chargeConfirmWindow.destroy, **button_opts)
        cancelButton.pack(side='left')

        chargeConfirmWindow.wait_window()

        if chargeConfirmWindow.OKPress:
            self.beginChargeTime = time.time()
            self.charging = True
            self.resetChargePlot()
            self.updateChargePlot()
            self.chargePress = True

    def discharge(self):
        # Differentiate a discharge that comes automatically from charging the capacitor
        # and a discharge that comes from the discharge button press
        if self.chargePress:
            self.discharged = True
            self.charging = False
            pins = [voltageLoadPin, currentLoadPin]
            self.dischargeTime, self.dischargeVoltageLoad, self.dischargeCurrentLoad = self.readOscilloscope(pins)

            self.replotDischarge()

            self.saveResults()

        else:
            dischargeConfirmName = 'Discharge'
            dischargeConfirmText = 'Are you sure you want to discharge?'
            dischargeConfirmWindow = MessageWindow(self, dischargeConfirmName, dischargeConfirmText)

            cancelButton = tk.Button(dischargeConfirmWindow.bottomFrame, text='Cancel', command=dischargeConfirmWindow.destroy, **button_opts)
            cancelButton.pack(side='left')

            dischargeConfirmWindow.wait_window()

            if dischargeConfirmWindow.OKPress:
                print('Discharge')

    def safetyLights(self):
        print('Turn on safety lights')

    def emergency_off(self):
        print('Emergency Off')

    def validateLogin(self):
        # If someone is not logged in then the buttons remain deactivated
        def checkLogin():
            self.username = self.usernameEntry.get()
            self.password = self.passwordEntry.get()
            self.loggedIn = self.username in acceptableUsernames and self.password in acceptablePasswords

            if self.loggedIn:
                self.loginWindow.destroy()
                self.saveLocationButton.configure(state='normal')
            else:
                incorrectLoginName = 'Incorrect Login'
                incorrectLoginText = 'You have entered either a wrong name or password. Please reenter your credentials or contact nickschw@umd.edu for help'
                incorrectLoginWindow = MessageWindow(self, incorrectLoginName, incorrectLoginText)

                incorrectLoginWindow.wait_window()

                self.usernameEntry.delete(0, 'end')
                self.passwordEntry.delete(0, 'end')

        self.loginWindow = tk.Toplevel(padx=loginPadding, pady=loginPadding)
        self.loginWindow.title('Login Window')

        login_text = 'Please enter UMD username.'
        password_text = 'Please enter password.'
        button_text = 'Login'

        self.usernameLabel = tk.Label(self.loginWindow, text=login_text, **text_opts)
        self.usernameEntry = tk.Entry(self.loginWindow, **text_opts)
        self.passwordLabel = tk.Label(self.loginWindow, text=password_text, **text_opts)
        self.passwordEntry = tk.Entry(self.loginWindow, show='*', **text_opts)
        self.loginButton = tk.Button(self.loginWindow, text=button_text, command=checkLogin, **button_opts)

        self.usernameLabel.pack()
        self.usernameEntry.pack()
        self.passwordLabel.pack()
        self.passwordEntry.pack()
        self.loginButton.pack()

    def on_closing(self):
        plt.close('all')
        self.quit()
        self.destroy()

    def readSensor(self, pin):
        # sensorName = 'Dev1'
        # try:
        #     with nidaqmx.Task() as task:
        #         task.ai_channels.add_ai_voltage_chan(f'{sensorName}/{pin}')
        #         value = task.read()
        #
        # except nidaqmx._lib.DaqNotFoundError:
        #     # value = 'N/A'
        #     try:
        #         if pin == 'ai0':
        #             value = np.random.rand()
        #         elif pin == 'ai1':
        #             value = powerSupplyVoltage * ( 1 -  np.exp( -self.timePoint / RCTime ) )
        #         elif pin == 'ai2':
        #             value = np.random.rand()
        #         elif pin == 'ai3':
        #             period = 10 # seconds
        #             value = np.cos(self.timePoint * 2 * np.pi / period)
        #         else:
        #             value = 'N/A'
        #     except AttributeError:
        #         value = 'N/A'
        if pin == 'ai0':
            value = np.random.rand() * 1000
        elif pin == 'ai1':
            value = powerSupplyVoltage * ( 1 -  np.exp( -self.timePoint / RCTime ) )
        elif pin == 'ai2':
            value = np.random.rand() / 10
        elif pin == 'ai3':
            period = 10 # seconds
            value = np.abs(np.cos(self.timePoint * 2 * np.pi / period))
        else:
            value = 'N/A'

        return value

    def readOscilloscope(self, pins):
        time = np.linspace(0, 1)
        voltageLoad = 1 - np.exp(-time)
        currentLoad = np.exp(-time)
        return time, voltageLoad, currentLoad

    def updateLabels(self):
        loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
        PSSuperscript = '\u1D56\u02E2'
        self.voltageLoadText.set(f'V{loadSuperscript}: {self.readSensor(voltageLoadPin) / 1000:.2f} kV')
        self.voltagePSText.set(f'V{PSSuperscript}: {self.readSensor(voltagePSPin) / 1000:.2f} kV')
        self.currentLoadText.set(f'I{loadSuperscript}: {self.readSensor(currentLoadPin):.2f} A')
        self.currentPSText.set(f'I{PSSuperscript}: {self.readSensor(currentPSPin):.2f} A')

        if self.discharged:
            self.chargeStateText.set('Discharged!')
            self.countdownText.set(f'Coundown: {self.countdownTime:.2f} s')
        elif self.charged:
            self.chargeStateText.set('Charged')
            self.countdownText.set(f'Coundown: {self.countdownTime:.2f} s')
        else:
            self.chargeStateText.set('Not Charged')
            self.countdownText.set('Countdown: N/A')

    def clearAxisLines(self, axis):
        if len(axis.lines) != 0:
            for i in range(len(axis.lines)):
                axis.lines[0].remove()

    def replotCharge(self):
        self.clearAxisLines(self.chargeVoltageAxis)
        self.clearAxisLines(self.chargeCurrentAxis)

        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltageLoad / 1000, color=voltageColor)
        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltagePS / 1000, color=voltageColor, linestyle='--')
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentLoad, color=currentColor)
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentPS, color=currentColor, linestyle='--')
        self.chargePlot.update()

    def replotDischarge(self):
        self.clearAxisLines(self.dischargeVoltageAxis)
        self.clearAxisLines(self.dischargeCurrentAxis)

        self.dischargeVoltageAxis.plot(self.dischargeTime, self.dischargeVoltageLoad / 1000, color=voltageColor, label='V$_{load}$')
        self.dischargeCurrentAxis.plot(self.dischargeTime, self.dischargeCurrentLoad, color=currentColor, label='I$_{load}$')
        self.dischargePlot.update()

    def updateChargePlot(self):
        self.timePoint = time.time() - self.beginChargeTime
        voltageLoadPoint = self.readSensor(voltageLoadPin)
        voltagePSPoint = self.readSensor(voltagePSPin)
        currentLoadPoint = self.readSensor(currentLoadPin)
        currentPSPoint = self.readSensor(currentPSPin)

        # Voltage reaches a certain value of chargeVoltage to begin countown clock
        if voltagePSPoint >= chargeVoltageFraction * self.chargeVoltage * 1000 and not self.discharged:
            if not self.countdownStarted:
                self.countdownTimeStart = time.time()
                self.charged = True
                self.countdownStarted = True

            self.countdownTime = self.holdChargeTime - (time.time() - self.countdownTimeStart)

            if self.countdownTime <= 0.0:
                self.countdownTime = 0.0
                self.discharge()

        self.updateLabels()

        self.chargeTime = np.append(self.chargeTime, self.timePoint)
        self.chargeVoltageLoad = np.append(self.chargeVoltageLoad, voltageLoadPoint)
        self.chargeVoltagePS = np.append(self.chargeVoltagePS, voltagePSPoint)
        self.chargeCurrentLoad = np.append(self.chargeCurrentLoad, currentLoadPoint)
        self.chargeCurrentPS = np.append(self.chargeCurrentPS, currentPSPoint)

        self.replotCharge()

        if self.charging == True:
            self.after(int(1000 / refreshRate), self.updateChargePlot)

    def resetChargePlot(self):
        # Set time and voltage to empty array
        self.chargeTime = np.array([])
        self.chargeVoltageLoad = np.array([])
        self.chargeVoltagePS = np.array([])
        self.chargeCurrentLoad = np.array([])
        self.chargeCurrentPS = np.array([])

        self.replotCharge()

    def resetDischargePlot(self):
        # Set time and voltage to empty array
        self.dischargeTime = np.array([])
        self.dischargeVoltageLoad = np.array([])
        self.dischargeCurrentLoad = np.array([])

        self.replotDischarge()

    def reset(self):
        self.serialNumberEntry.delete(0, 'end')
        self.chargeVoltageEntry.delete(0, 'end')
        self.holdChargeTimeEntry.delete(0, 'end')

        self.charged = False
        self.chargePress = False
        self.discharged = False
        self.userInputsSet = False
        self.timePoint = 0
        self.countdownStarted = False
        self.checklist_Checkbuttons = {}
        self.updateLabels()

        self.resetChargePlot()
        self.resetDischargePlot()

        self.disableButtons()
        if self.loggedIn:
            self.saveLocationButton.configure(state='normal')

class Can_Plot(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.fig, self.ax = plt.subplots(constrained_layout=True)
        self.line, = self.ax.plot([],[]) #Create line object on plot
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=1, fill=tk.BOTH)

    def update(self):
        #update graph
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

class MessageWindow(tk.Toplevel):
    def __init__(self, master, name, text):
        super().__init__(master)
        self.name = name
        self.text = text
        self.title(self.name)

        self.maxWidth = 2000
        self.maxHeight = 2000
        self.maxsize(self.maxWidth, self.maxHeight)

        OKButtonText = 'Okay'
        self.OKPress = False

        self.topFrame = tk.Frame(self)
        self.bottomFrame = tk.Frame(self)

        self.topFrame.pack(side='top')
        self.bottomFrame.pack(side='bottom')

        def OKPress():
            self.OKPress = True
            self.destroy()

        self.message = tk.Message(self.topFrame, width=topLevelWidth, text=self.text, **text_opts)
        self.OKButton = tk.Button(self.bottomFrame, text=OKButtonText, command=OKPress, **button_opts)

        self.message.pack(fill='both')
        self.OKButton.pack(side='left')

if __name__ == "__main__":
    app = MainApp()
    app.loginWindow.lift(aboveThis=app)
    app.mainloop()
