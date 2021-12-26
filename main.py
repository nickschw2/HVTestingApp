import tkinter as tk
import numpy as np
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import time
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

        # Column for buttons and labels on the left
        self.grid_columnconfigure(0, w=1)
        self.buttons = tk.Frame(self)
        self.buttons.grid(row=1, column=0)

        # Button definitions and placement
        self.checklistButton = tk.Button(self.buttons, text='Begin Charging\nChecklist',
                                    command=self.checklist, bg=green, fg=white, **button_opts)
        self.chargeButton = tk.Button(self.buttons, text='Begin Charging',
                                    command=self.charge, bg=yellow, fg=white, **button_opts)
        self.dischargeButton = tk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bg=orange, fg=white, **button_opts)
        self.emergency_offButton = tk.Button(self.buttons, text='Emergency Off',
                                    command=self.emergency_off, bg=red, fg=white, **button_opts)
        self.resetPlotsButton = tk.Button(self.buttons, text='Reset Plots',
                                    command=self.resetPlot, bg=red, fg=white, **button_opts)

        # Voltage and current are read from both the power supply and the load
        self.voltageLoadText = tk.StringVar()
        self.voltagePSText = tk.StringVar()
        self.currentLoadText = tk.StringVar()
        self.currentPSText = tk.StringVar()
        self.chargeStateText = tk.StringVar()
        self.countdownText = tk.StringVar()

        self.voltageLoadLabel = tk.Label(self.buttons, textvariable=self.voltageLoadText, **text_opts)
        self.voltagePSLabel = tk.Label(self.buttons, textvariable=self.voltagePSText, **text_opts)
        self.currentLoadLabel = tk.Label(self.buttons, textvariable=self.currentLoadText, **text_opts)
        self.currentPSLabel = tk.Label(self.buttons, textvariable=self.currentPSText, **text_opts)
        self.chargeStateLabel = tk.Label(self.buttons, textvariable=self.chargeStateText, **text_opts)
        self.countdownLabel = tk.Label(self.buttons, textvariable=self.countdownText, **text_opts)

        self.charged = False
        self.discharged = False
        self.timePoint = 0
        self.countdownStarted = False
        self.updateLabels()

        self.checklistButton.pack()
        self.chargeButton.pack()
        self.dischargeButton.pack()
        self.emergency_offButton.pack()
        self.resetPlotsButton.pack()
        self.voltageLoadLabel.pack()
        self.voltagePSLabel.pack()
        self.currentLoadLabel.pack()
        self.currentPSLabel.pack()
        self.chargeStateLabel.pack()
        self.countdownLabel.pack()

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
        except Exception as e:
            print(e)

    def setUserInputs(self):
        try:
            self.serialNumber = str(self.serialNumberEntry.get())
            self.chargeVoltage = float(self.chargeVoltageEntry.get())
            self.holdChargeTime = float(self.holdChargeTimeEntry.get())

            if format.match(self.serialNumber) is None:
                raise ValueError

            self.userInputSetText.set('Set!')
            def resetSetText():
                self.userInputSetText.set('      ')
            self.after(displaySetTextTime, resetSetText)

        except ValueError:
            incorrectUserInputName = 'Invalid Input'
            incorrectUserInputText = 'Please reenter a valid string for serial number and numerical value for both the Charge Voltage and Holt Charge Time.'
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

        if complete:
            self.enableButtons()

    def checklist(self):
        self.disableButtons()
        self.checklistButton.configure(state='normal')
        self.checklist_win = tk.Toplevel()

        checklist_steps = ['Ensure that power supply is off']
            # 'Ensure that the charging switch is open',
            # 'Check system is grounded',
            # 'Turn on power supply',
            # 'Exit room and ensure nobody else is present',
            # 'Turn on HV Testing Light',
            # 'Close charging switch',
            # 'Increase voltage on power supply',
            # 'Open charging switch',
            # 'Trigger ignitron',
            # 'Save scope and video data',
            # 'Enter room, turn off power supply, and "idiot stick" all HV lines',
            # 'Turn off HV testing light']

        self.checklist_Checkbuttons = {}
        for i, step in enumerate(checklist_steps):
            self.checklist_Checkbuttons[f'c{i + 1}'] = tk.BooleanVar()
            button = tk.Checkbutton(self.checklist_win, variable=self.checklist_Checkbuttons[f'c{i + 1}'], text=f'Step {i + 1}: ' + step, command=self.checklistComplete)
            button.grid(row=i, column=0, sticky='w')

        self.OKButton = tk.Button(self.checklist_win, text='Okay', command=self.checklist_win.destroy, **button_opts)
        self.OKButton.grid(row=i + 1, column=0)

        self.checklist_win.wait_window()

    def charge(self):
        print('Charge')
        self.resetPlot()
        self.updateChargePlot()

    def discharge(self):
        print('Discharge')
        self.discharged = True
        pins = [voltageLoadPin, currentLoadPin]
        self.dischargeTime, self.dischargeVoltageLoad, self.dischargeCurrentLoad = self.readOscilloscope(pins)

        self.dischargeVoltageAxis.plot(self.dischargeTime, self.dischargeVoltageLoad / 1000, color=voltageColor, label='V$_{load}$')
        self.dischargeCurrentAxis.plot(self.dischargeTime, self.dischargeCurrentLoad, color=currentColor, label='I$_{load}$')
        self.dischargePlot.update()

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
                self.checklistButton.configure(state='normal')
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

    def updateChargePlot(self):
        self.timePoint = time.time() - self.beginDataCollectionTime
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

        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltageLoad / 1000, color=voltageColor)
        self.chargeVoltageAxis.plot(self.chargeTime, self.chargeVoltagePS / 1000, color=voltageColor, linestyle='--')
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentLoad, color=currentColor)
        self.chargeCurrentAxis.plot(self.chargeTime, self.chargeCurrentPS, color=currentColor, linestyle='--')
        self.chargePlot.update()

        self.after(int(1000 / refreshRate), self.updateChargePlot)

    def resetPlot(self):
        # Set time and voltage to empty array
        self.chargeTime = np.array([])
        self.chargeVoltageLoad = np.array([])
        self.chargeVoltagePS = np.array([])
        self.chargeCurrentLoad = np.array([])
        self.chargeCurrentPS = np.array([])

        self.beginDataCollectionTime = time.time()

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

        self.message = tk.Message(self, text=self.text, **text_opts)
        self.OKButton = tk.Button(self, text=OKButtonText, command=self.destroy, **button_opts)

        self.message.pack()
        self.OKButton.pack()

    def update(self):
        self.message


if __name__ == "__main__":
    app = MainApp()
    app.loginWindow.lift(aboveThis=app)
    app.mainloop()
