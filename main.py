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
        self.checklist_button = tk.Button(self.buttons, text='Begin Charging\nChecklist',
                                    command=self.checklist, bg=green, fg=white, **widget_opts)
        self.checklist_button.grid(row=2, column=0, sticky='ew')

        # Begin charging button
        self.charge_button = tk.Button(self.buttons, text='Begin Charging',
                                    command=self.charge, bg=yellow, fg=white, **widget_opts)
        self.charge_button.grid(row=3, column=0, sticky='ew')

        # Discharge button
        self.discharge_button = tk.Button(self.buttons, text='Discharge',
                                    command=self.discharge, bg=orange, fg=white, **widget_opts)
        self.discharge_button.grid(row=4, column=0, sticky='ew')

        # Emergency Off button
        self.emergency_off_button = tk.Button(self.buttons, text='Emergency Off',
                                    command=self.emergency_off, bg=red, fg=white, **widget_opts)
        self.emergency_off_button.grid(row=5, column=0, sticky='ew')

        # Display current voltage
        voltage_text = f'{self.get_voltage()} kV' if type(self.get_voltage())==float else 'N/A'
        self.voltage_label = tk.Label(self.buttons, text='Voltage: '+voltage_text, **widget_opts)
        self.voltage_label.grid(row=6, column=0)

        # Refresh button
        self.collectDataButton = tk.Button(self.buttons, text='Begin Collection',
                                    command=self.resetPlot, bg=red, fg=white, **widget_opts)
        self.collectDataButton.grid(row=6, column=0, sticky='ew')

        # Configure Graphs
        self.grid_rowconfigure(0, w=1)
        self.grid_columnconfigure(1, w=1)

        # Plot of results
        self.timeTrace = Can_Plot(self)
        self.voltageAxis = self.timeTrace.ax
        self.currentAxis = self.timeTrace.ax.twinx()

        self.timeTrace.ax.set_xlabel('Time (s)')
        self.voltageAxis.set_ylabel('Voltage (kV)')
        self.currentAxis.set_ylabel('Current (A)')

        self.timeTrace.grid(row=0, column=1, sticky='news')

        try:
            # On startup, ask for username
            self.loggedIn = False
            self.validateLogin()
        except Exception as e:
            print(e)

    def checklist(self):
        self.checklist_win = tk.Toplevel()

        checklist_steps = ['Turn on ignitron heat lamp for 10 minutes',
            'Ensure that power supply is off',
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
            self.checklist_Checkbuttons[f'c{i}'] = tk.Checkbutton(self.checklist_win, text=f'Step {i}: ' + step)
            self.checklist_Checkbuttons[f'c{i}'].grid(row=i, column=0, sticky='w')

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

        self.username_label = tk.Label(self.loginWindow, text=login_text, **widget_opts)
        self.usernameEntry = tk.Entry(self.loginWindow, **widget_opts)
        self.password_label = tk.Label(self.loginWindow, text=password_text, **widget_opts)
        self.passwordEntry = tk.Entry(self.loginWindow, show='*', **widget_opts)
        self.login_button = tk.Button(self.loginWindow, text=button_text, command=checkLogin, **widget_opts)

        self.username_label.pack()
        self.usernameEntry.pack()
        self.password_label.pack()
        self.passwordEntry.pack()
        self.login_button.pack()

    def on_closing(self):
        plt.close('all')
        self.quit()
        self.destroy()

    def get_voltage(self):
        return 'N/A'

    def generate_data(self):
        timePoint = time.time() - self.beginDataCollectionTime
        period = 10 #seconds
        voltagePoint = np.sin(timePoint * 2 * np.pi / period)
        return timePoint, voltagePoint

    def updatePlot(self):
        timePoint, voltagePoint = self.generate_data()
        self.timeArray = np.append(self.timeArray, timePoint)
        self.voltageArray = np.append(self.voltageArray, voltagePoint)
        self.timeTrace.ax.plot(self.timeArray, self.voltageArray, color=voltageColor)
        self.timeTrace.update()

        self.after(100, self.updatePlot)

    def resetPlot(self):
        # Set time and voltage to empty array
        self.timeArray = np.array([])
        self.voltageArray = np.array([])

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

        self.message = tk.Message(self, text=self.text, **widget_opts)
        self.OKButon = tk.Button(self, text=OKButtonText, command=self.destroy, **widget_opts)

        self.message.pack()
        self.OKButon.pack()


if __name__ == "__main__":
    app = MainApp()
    app.loginWindow.lift(aboveThis=app)
    app.mainloop()
