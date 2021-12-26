import tkinter as tk
import numpy as np
from tkinter import ttk
import matplotlib
import matplotlib.lines as mlines
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
        self.userInputs.grid(row=0, columnspan=2, sticky='ns')

        # Charge voltage and desired hold charge time
        self.chargeVoltageLabel = tk.Label(self.userInputs, text='Charge (kV):', **text_opts)
        self.holdChargeTimeLabel = tk.Label(self.userInputs, text='Hold Charge (s):', **text_opts)

        userInputWidth = 6
        self.chargeVoltageEntry = tk.Entry(self.userInputs, width=userInputWidth, **text_opts)
        self.holdChargeTimeEntry = tk.Entry(self.userInputs, width=userInputWidth, **text_opts)

        self.userInputOkayButton = tk.Button(self.userInputs, text='Okay', command=self.setUserInputs, **button_opts)
        self.userInputSetText = tk.StringVar()
        self.userInputSetText.set('      ')
        self.userInputSetLabel = tk.Label(self.userInputs, textvariable=self.userInputSetText, **text_opts)

        userInputPadding = 100
        self.chargeVoltageLabel.pack(side='left')
        self.chargeVoltageEntry.pack(side='left', padx=(0, userInputPadding))
        self.holdChargeTimeLabel.pack(side='left')
        self.holdChargeTimeEntry.pack(side='left', padx=(0, userInputPadding))
        self.userInputOkayButton.pack(side='left')
        self.userInputSetLabel.pack(side='left')

        # Column for buttons and labels on the left
        self.grid_columnconfigure(0, w=1)
        self.buttons = ttk.Frame(self)
        self.buttons.grid(row=1, column=0, sticky='news')
        self.buttons.grid_columnconfigure(0, w=1)

        # Begin checklist button
        self.checklistButton = tk.Button(self.buttons, text='Begin Charging\nChecklist',
                                    command=self.checklist, bg=green, fg=white, **button_opts)
        self.checklistButton.grid(row=2, column=0, sticky='ew')

        # Begin charging button
        self.chargeButton = tk.Button(self.buttons, text='Begin Charging',
                                    command=self.charge, bg=yellow, fg=white, **button_opts)
        self.chargeButton.grid(row=3, column=0, sticky='ew')

        # Discharge button
        self.dischargeButton = tk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bg=orange, fg=white, **button_opts)
        self.dischargeButton.grid(row=4, column=0, sticky='ew')

        # Emergency Off button
        self.emergency_offButton = tk.Button(self.buttons, text='Emergency Off',
                                    command=self.emergency_off, bg=red, fg=white, **button_opts)
        self.emergency_offButton.grid(row=5, column=0, sticky='ew')

        # Reset plots button
        self.resetPlotsButton = tk.Button(self.buttons, text='Reset Plots',
                                    command=self.resetPlot, bg=red, fg=white, **button_opts)
        self.resetPlotsButton.grid(row=6, column=0, sticky='ew')

        # Voltage and current are read from both the power supply and the load
        self.voltageLoadPin = 'ai0'
        self.voltagePSPin = 'ai1'
        self.currentLoadPin = 'ai2'
        self.currentPSPin = 'ai3'

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

        self.voltageLoadLabel.grid(row=7, column=0, sticky='w')
        self.voltagePSLabel.grid(row=8, column=0, sticky='w')
        self.currentLoadLabel.grid(row=9, column=0, sticky='w')
        self.currentPSLabel.grid(row=10, column=0, sticky='w')
        self.chargeStateLabel.grid(row=11, column=0, sticky='w')
        self.countdownLabel.grid(row=12, column=0, sticky='w')

        # Configure Graphs
        self.grid_rowconfigure(1, w=1)
        self.grid_columnconfigure(1, w=1)

        # Plot of results
        self.chargeTrace = Can_Plot(self)
        self.voltageAxis = self.chargeTrace.ax
        self.currentAxis = self.chargeTrace.ax.twinx()

        self.voltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.currentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.chargeTrace.ax.set_xlabel('Time (s)')
        self.voltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.currentAxis.set_ylabel('Current (A)', color=currentColor)

        voltageLine = mlines.Line2D([], [], color=voltageColor, linestyle='-', label='V$_{load}$')
        voltageDash = mlines.Line2D([], [], color=voltageColor, linestyle='--', label='V$_{PS}$')
        currentLine = mlines.Line2D([], [], color=currentColor, linestyle='-', label='I$_{load}$')
        currentDash = mlines.Line2D([], [], color=currentColor, linestyle='--', label='I$_{PS}$')
        self.chargeTrace.ax.legend(handles=[voltageLine, voltageDash, currentLine, currentLine], loc='lower left')

        self.chargeTrace.grid(row=1, column=1, sticky='news')

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
            self.chargeVoltage = float(self.chargeVoltageEntry.get())
            self.holdChargeTime = float(self.holdChargeTimeEntry.get())

            self.userInputSetText.set('Set!')
            displaySetTextTime = 1000 # ms
            def resetSetText():
                self.userInputSetText.set('      ')
            self.after(displaySetTextTime, resetSetText)

        except ValueError:
            incorrectUserInputName = 'Invalid Input'
            incorrectUserInputText = 'Please reenter a numerical value for both the Charge Voltage and Holt Charge Time.'
            incorrectUserInputWindow = MessageWindow(self, incorrectUserInputName, incorrectUserInputText)

            incorrectUserInputWindow.wait_window()

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

        self.loginWindow = tk.Toplevel(padx=pad_val, pady=pad_val)
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

    def updateLabels(self):
        loadSuperscript = '\u02E1\u1D52\u1D43\u1D48'
        PSSuperscript = '\u1D56\u02E2'
        self.voltageLoadText.set(f'V{loadSuperscript}: {self.readSensor(self.voltageLoadPin) / 1000:.2f} kV')
        self.voltagePSText.set(f'V{PSSuperscript}: {self.readSensor(self.voltagePSPin) / 1000:.2f} kV')
        self.currentLoadText.set(f'I{loadSuperscript}: {self.readSensor(self.currentLoadPin):.2f} A')
        self.currentPSText.set(f'I{PSSuperscript}: {self.readSensor(self.currentPSPin):.2f} A')

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
        voltageLoadPoint = self.readSensor(self.voltageLoadPin)
        voltagePSPoint = self.readSensor(self.voltagePSPin)
        currentLoadPoint = self.readSensor(self.currentLoadPin)
        currentPSPoint = self.readSensor(self.currentPSPin)

        # Voltage reaches a certain value of chargeVoltage to begin countown clock
        chargeVoltageFraction = 0.9
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

        self.timeArray = np.append(self.timeArray, self.timePoint)
        self.voltageLoadArray = np.append(self.voltageLoadArray, voltageLoadPoint)
        self.voltagePSArray = np.append(self.voltagePSArray, voltagePSPoint)
        self.currentLoadArray = np.append(self.currentLoadArray, currentLoadPoint)
        self.currentPSArray = np.append(self.currentPSArray, currentPSPoint)

        self.voltageAxis.plot(self.timeArray, self.voltageLoadArray / 1000, color=voltageColor, label='V$_{load}$')
        self.voltageAxis.plot(self.timeArray, self.voltagePSArray / 1000, color=voltageColor, label='V$_{PS}$', linestyle='--')
        self.currentAxis.plot(self.timeArray, self.currentLoadArray, color=currentColor, label='I$_{load}$')
        self.currentAxis.plot(self.timeArray, self.currentPSArray, color=currentColor, label='I$_{PS}$', linestyle='--')
        self.chargeTrace.update()

        frequency = 10 #Hz
        self.after(int(1000 / frequency), self.updateChargePlot)

    def resetPlot(self):
        # Set time and voltage to empty array
        self.timeArray = np.array([])
        self.voltageLoadArray = np.array([])
        self.voltagePSArray = np.array([])
        self.currentLoadArray = np.array([])
        self.currentPSArray = np.array([])

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
