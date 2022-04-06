import tkinter as tk
from tkinter import ttk
from constants import *

# Class for generating popup windows
class MessageWindow(tk.Toplevel):
    def __init__(self, master, name, text):
        super().__init__(master)
        # Bring pop up to the center and top
        master.eval(f'tk::PlaceWindow {str(self)} center')
        self.attributes('-topmost', True)
        self.title(name)

        self.maxWidth = 2000
        self.maxHeight = 2000
        self.maxsize(self.maxWidth, self.maxHeight)

        # Initialize okay button to False
        self.OKPress = False

        # Create two frames, one for the text, and the other for buttons on the bottom
        self.topFrame = ttk.Frame(self)
        self.bottomFrame = ttk.Frame(self)

        self.topFrame.pack(side='top', padx=framePadding, pady=(framePadding, 0))
        self.bottomFrame.pack(side='bottom', padx=framePadding, pady=framePadding)

        # Destroy window and set value of okay button to True
        def OKPress():
            self.OKPress = True
            self.destroy()

        # Create and place message and okay button
        self.message = ttk.Label(self.topFrame, wraplength=topLevelWrapLength, width=topLevelWidth, text=text, **text_opts)
        self.OKButton = ttk.Button(self.bottomFrame, text='Okay', command=OKPress, style='Accent.TButton')

        self.message.pack(fill='both')
        self.OKButton.pack(side='left')
