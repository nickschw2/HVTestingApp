from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Force user to take pre- and post- shot notes
Fix oscilloscope loading bar
When reset, the results plot shows up immediately
After resetting a second time, it does charge? Or at least nothing shows up on the plot
Need to allow for plotting of more than one line on twinx
Need to figure out weird zoom effect on single plots
The digital filter trigger enable is not working
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
