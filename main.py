from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Force user to take pre- and post- shot notes
Fix oscilloscope loading bar
Need to allow for plotting of more than one line on twinx
The digital filter trigger enable is not working
Add gas puff delay to recorded data
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
