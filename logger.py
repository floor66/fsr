"""
    logger.py
    Created by Floris P.J. den Hartog, 2018

    Main file for the logging functions used by main.py
"""

import time
from utils import timerunning, touch

class logger:
    def __init__(self, file, time_started):
        self.file = file
        self.time_started = time_started
        
        touch(self.file) # Generate an empty log file
    
    # Log to console and to a log file
    def log(self, msg):
        timerunning_ = timerunning(time.time() - self.time_started)
        
        print("%s - %s" % (timerunning_, msg))
        
        file = open(self.file, "a")
        file.write("%s - " % timerunning_)
        file.write(str(msg))
        file.write("\n")
        file.close()
    
