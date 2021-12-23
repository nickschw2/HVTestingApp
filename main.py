import tkinter as tk
import numpy as np
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import time
from constants import *

class MainApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('HV Capacitor Testing')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        # Column for buttons on the left
        self.grid_columnconfigure(0, w=1)
        self.buttons = ttk.Frame(self)
        self.buttons.grid(row=0, column=0, sticky='news')
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

        # Display voltage and current
        self.timePoint = 0.0

        voltageText = f'{self.getVoltage(self.timePoint)} kV' if type(self.getVoltage(self.timePoint)) == float else 'N/A'
        currentText = f'{self.getCurrent(self.timePoint)} A' if type(self.getCurrent(self.timePoint)) == float else 'N/A'

        self.voltageLabel = tk.Label(self.buttons, text='Voltage: '+ voltageText, **text_opts)
        self.currentLabel = tk.Label(self.buttons, text='Current: '+ currentText, **text_opts)

        self.voltageLabel.grid(row=7, column=0)
        self.voltageLabel.grid(row=8, column=0)

        # Refresh button
        self.collectDataButton = tk.Button(self.buttons, text='Begin Collection',
                                    command=self.resetPlot, bg=red, fg=white, **button_opts)
        self.collectDataButton.grid(row=6, column=0, sticky='ew')

        # Configure Graphs
        self.grid_rowconfigure(0, w=1)
        self.grid_columnconfigure(1, w=1)

        # Plot of results
        self.timeTrace = Can_Plot(self)
        self.voltageAxis = self.timeTrace.ax
        self.currentAxis = self.timeTrace.ax.twinx()

        self.voltageAxis.tick_params(axis='y', labelcolor=voltageColor)
        self.currentAxis.tick_params(axis='y', labelcolor=currentColor)

        self.timeTrace.ax.set_xlabel('Time (s)')
        self.voltageAxis.set_ylabel('Voltage (kV)', color=voltageColor)
        self.currentAxis.set_ylabel('Current (A)', color=currentColor)

        self.timeTrace.grid(row=0, column=1, sticky='news')

        try:
            # On startup, disable buttons until login is correct
            self.disableButtons()
            self.loggedIn = False
            self.validateLogin()
        except Exception as e:
            print(e)

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

        checklist_steps = ['Ensure that power supply is off',
            'Ensure that the charging switch is open',
            'Check system is grounded',
            'Turn on power supply',
            'Exit room and ensure nobody else is present',
            'Turn on HV Testing Light',
            'Close charging switch',
            'Increase voltage on power supply',
            'Open charging switch',
            'Trigger ignitron',
            'Save scope and video data',
            'Enter room, turn off power supply, and "idiot stick" all HV lines',
            'Turn off HV testing light'
            ]

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

    def discharge(self):
        print('Discharge')

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

    def startDischargeTimer(self, timeDesiredVoltage):
        elapsedHoldChargeTime = time.time() - timeDesiredVoltage
        if  elapsedHoldChargeTime < holdChargeTime * 1000:
            dischargeTimerName = 'Discharge Timer'
            dischargeTimerText = f'{holdChargeTime - elapsedHoldChargeTime}'
            # countdown clock https://www.pythontutorial.net/tkinter/tkinter-after/
        else:
            self.dischargeCapacitor()


    def getVoltage(self, timePoint):
        if self.timePoint == 0.0:
            return float('nan')
        RCTime = powerSupplyResistance * capacitorCapacitance
        return powerSupplyVoltage * ( 1 -  np.exp( -timePoint / RCTime ) )

    def getCurrent(self, timePoint):
        if self.timePoint == 0.0:
            return float('nan')
        period = 10 #seconds
        return np.cos(timePoint * 2 * np.pi / period)

    def updatePlot(self):
        self.timePoint = time.time() - self.beginDataCollectionTime
        voltagePoint = self.getVoltage(self.timePoint)
        currentPoint = self.getCurrent(self.timePoint)

        self.timeArray = np.append(self.timeArray, self.timePoint)
        self.voltageArray = np.append(self.voltageArray, voltagePoint)
        self.currentArray = np.append(self.currentArray, currentPoint)

        self.voltageAxis.plot(self.timeArray, self.voltageArray / 1000, color=voltageColor)
        self.currentAxis.plot(self.timeArray, self.currentArray, color=currentColor)
        self.timeTrace.update()

        if voltagePoint >= dummyMaxVoltage:
            self.startDischargeTimer(time.time())

        self.after(100, self.updatePlot)

    def resetPlot(self):
        # Set time and voltage to empty array
        self.timeArray = np.array([])
        self.voltageArray = np.array([])
        self.currentArray = np.array([])

        self.beginDataCollectionTime = time.time()
        self.updatePlot()

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
