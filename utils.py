"""
    utils.py
    Created by Floris P.J. den Hartog, 2018

    Utility functions used in the FSR main file
"""

import time

# Get current timestamp in ms
millis = lambda: int(round(time.time() * 1000.0))

# Get the time running in a visible format
def timerunning(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    
    return "%d:%02d:%02d" % (h, m, s)

# Create an empty file
def touch(name):
    file = open(name, "w")
    file.close()

