from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Force user to take pre- and post- shot notes
Clear notes on reset press
Reset y axis on reset press
Weird scaling on x axis for charging plot
Fix oscilloscope loading bar
When reset, the results plot shows up immediately
After resetting a second time, it does charge? Or at least nothing shows up on the plot
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
