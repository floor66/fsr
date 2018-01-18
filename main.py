import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial
import time
import tkinter as Tk

# Get current timestamp in ms
millis = lambda: int(round(time.time() * 1000.0))

class FSR:
    def __init__(self):
        self.__start__ = time.time()
        self.recordings = 1
        
####### User defined variables ##############################################################
        self.COM_PORT = "COM5" # Seen in the bottom-left of the Arduino IDE

        self.BAUD_RATE = 9600  # Needs to coincide with Arduino code "Serial.begin(...)"
        self.REFRESH_MS = 100  # Refresh the graph every (x) ms
        self.POP_CUTOFF = 100  # The amount of data points to show on screen
        self.INIT_TIMEOUT = 15 # The amount of seconds to wait for Arduino to initialize

        self.Vcc = 5.06 # Input voltage of Arduino

        # If both are -1, autofit is used
        self.Y_RANGE_LOW = -1
        self.Y_RANGE_HIGH = -1

        self.SHOW_PINS = [0, 1] # Only show from A0, A1, A..etc inputs
#############################################################################################
        
        # Misc. variable setup, don't touch
        self.SAVE_FILE = "sensordata/data_%i_%i.txt" % (self.__start__, self.recordings)
        self.LOG_FILE = "logs/log_%i.txt" % self.__start__
        self.cols = ["b-", "r-", "g-", "b-", "m-", "c-"]
        self.recording = False
        self.can_start = False # To wait for Arduino to give the go-ahead

        # Generate an empty data and log file
        self.touch(self.SAVE_FILE)
        self.touch(self.LOG_FILE)

        self.log("Starting... The GMT time is %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        self.reset_vars()
        self.init_gui()

    def log(self, msg):
        timerunning = time.time() - self.__start__
        m, s = divmod(timerunning, 60)
        h, m = divmod(m, 60)
        timerunning = "%d:%02d:%02d" % (h, m, s)
        
        print("%s - %s" % (timerunning, msg))
        
        file = open(self.LOG_FILE, "a")
        file.write("%s - " % timerunning)
        file.write(msg)
        file.write("\n")
        file.close()
    
    # Convert the 0...1024 value to lux
    def sensor_val_to_lux(self, val):
        res_volt = val * (self.Vcc / 1024) # Calc voltage over resistor (aprox. 5V supply, 10-bit reading, so 5/2^10 = 5/1024 V per value)
        return (500 / (10 * ((self.Vcc - res_volt) / res_volt)))

    # Update the GUI
    def update(self):
        self.root.update_idletasks()
        self.root.update()

    # Create an empty file
    def touch(self, name):
        file = open(name, "w")
        file.close()
    
    # Appending to data file
    def save_data(self, data):
        try:
            file = open(self.SAVE_FILE, "a")
            file.write(data)
            file.close()
        except Exception as e:
            self.log("Error saving data %s" % e)


    # Reset variables for plotting
    def reset_vars(self):
        self.times = []
        self.resistor_data = []
        for pin in self.SHOW_PINS:
            self.times.append([])
            self.resistor_data.append([])

    def rec_stop(self):
        self.recording = False
        self.log("Stopping recording")
        self.recordings += 1
        self.SAVE_FILE = "sensordata/data_%i_%i.txt" % (self.__start__, self.recordings)

        self.reset_vars()

        self.ser.close() # Close the serial connection
        self.rec_stop_btn.configure(state="disabled")
        self.rec_start_btn.configure(state="normal")

    def rec_start(self):
        self.recording = True
        self.rec_start_btn.configure(state="disabled")
        self.rec_stop_btn.configure(state="normal")

        # Check if we can initiate the serial communication
        if self.init_serial():
            self.record()
        else:
            self.recording = False
            self.rec_start_btn.configure(state="normal")
            self.rec_stop_btn.configure(state="disabled")

    def quit_gui(self):
        self.root.quit()
        self.root.destroy()

        self.log("GUI destroyed")

    def init_gui(self):
        # Initialize Tk, create layout elements
        self.root = Tk.Tk()
        self.root.wm_title("Sensor Data")

        self.menu_left = Tk.Frame(master=self.root)
        self.panel_right = Tk.Frame(master=self.root)
        self.canvas_container = Tk.Frame(master=self.root)

        # Left menu
        self.rec_start_btn = Tk.Button(master=self.menu_left, text="Start Recording", command=self.rec_start)
        self.rec_stop_btn = Tk.Button(master=self.menu_left, text="Stop Recording", command=self.rec_stop)

        self.rec_stop_btn.configure(state="disabled")

        self.rec_start_btn.grid(row=0, column=0, sticky="n")
        self.rec_stop_btn.grid(row=1, column=0, sticky="n")
        
        self.menu_left.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        self.quit_btn = Tk.Button(master=self.root, text="Quit", command=self.quit_gui)
        self.quit_btn.grid(row=0, column=0, sticky="s", pady=5)

        # Init matplotlib graph
        self.init_mpl()

        # Right panel
        # TODO: add labels/entries

    def init_mpl(self):
        # Initialize matplotlib
        self.lines = []
        self.fig, self.ax1 = plt.subplots()
        self.ax1.set_autoscale_on(True)
        self.ax1.set_title("Photoresistor Sensor Data\n")
        self.ax1.set_ylabel("Sensor Value (lx)")
        self.ax1.set_xlabel("Time (ms)")

        # Instantiate a line in the graph for every pin we're reading
        for pin in self.SHOW_PINS:
            tmp, = self.ax1.plot([], [], self.cols[pin])
            self.lines.append(tmp)

        canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_container)
        canvas.show()
        canvas.get_tk_widget().pack()

        self.canvas_container.grid(row=0, column=1, sticky="ne")

        # Instantiate Tk window for the first time
        self.update()

    def init_serial(self):
        # Wait for serial connection
        timer = millis()
        while True:
            self.update()
            
            try:
                self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE)
                break
            except serial.serialutil.SerialException as e:
                if (millis() - timer) >= 1000: # Give an error every second
                    self.log("Connect Arduino to USB!")
                    timer = millis()

        # Wait for the go-ahead from Arduino
        timer = millis()
        while True:
            self.update()
            data_in = self.ser.readline()

            if len(data_in) > 0:
                data_in = data_in.decode().rstrip()

                if data_in == "INIT_COMPLETE":
                    self.can_start = True
                    self.log("Arduino initialized, starting recording")
                    self.log("Using pin%s A%s" % ("s" if len(self.SHOW_PINS) > 1 else "", ", A".join(str(pin) for pin in self.SHOW_PINS)))

                    return True

            if (millis() - timer) >= (self.INIT_TIMEOUT * 1000):
                self.log("Arduino failed to initialize after %i sec" % self.INIT_TIMEOUT)
                return False

    # Main loop
    def record(self):
        if not self.can_start:
            return False
        
        self.timer = millis()
        while self.recording:
            self.update()

            try:
                data_in = self.ser.readline()
            except serial.serialutil.SerialException as e:
                self.log("Reading from the serial port failed: %s" % e)
            finally:
                if not self.recording:
                    return

            # Check the received data
            if len(data_in) > 1:
                data_in = data_in.decode()
                unpack = data_in.rstrip().split(",")
                
                if len(unpack) == 3: # We expect 3 variables. No more, no less
                    try:
                        timestamp = int(unpack[0])
                        pin = int(unpack[1])
                        res_val = int(unpack[2])
                    except ValueError:
                        self.log("Faulty serial communication: %s" % ",".join(unpack))
                        continue

                    if not pin in self.SHOW_PINS: # Skip the pins we don't want/need to read
                        continue
                    else:
                        self.save_data(data_in)
                    
                    # Appending to the proper array
                    i = self.SHOW_PINS.index(pin)
                    
                    self.times[i].append(timestamp)
                    self.resistor_data[i].append(self.sensor_val_to_lux(res_val))
                    #resistor_data[i].append(res_val * ((Vcc) / 1024)) # Displays voltage in V on y-axis
                    
                    if len(self.times[i]) > self.POP_CUTOFF:
                        self.times[i].pop(0)
                        self.resistor_data[i].pop(0)

                    self.lines[i].set_data(self.times[i], self.resistor_data[i])

            self.draw()

    def draw(self):
        # Draw when it's time to draw!
        if (millis() - self.timer) >= self.REFRESH_MS:
            self.timer = millis()
            
            # Required to properly scale axes
            self.ax1.relim()
            self.ax1.autoscale_view(True, True, True)

            # Adjust scale of axes according to data
            if (self.Y_RANGE_LOW > -1) and (self.Y_RANGE_HIGH > -1):
                self.ax1.set_ylim(self.Y_RANGE_LOW, self.Y_RANGE_HIGH)
            else:
                if len(min(self.resistor_data)) > 0:
                    self.ax1.set_ylim(min([(min(i) - round(min(i) * 0.05)) for i in self.resistor_data]), \
                                      max([(max(i) + round(max(i) * 0.05)) for i in self.resistor_data])) # 5% margin above/below extreme values of lines

            if len(min(self.resistor_data)) > 0:
                tmp = "Photoresistor Sensor Data\n%s" % (", ".join(("A%i: %0.2f lx" % (pin, self.resistor_data[i][-1])) for i, pin in enumerate(self.SHOW_PINS)))
                self.ax1.set_title(tmp)
            
            # Speeds up drawing tremendously
            self.ax1.draw_artist(self.ax1.patch)

            for line in self.lines:
                self.ax1.draw_artist(line)
                
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()

try:
    fsr = FSR()
except (KeyboardInterrupt, SystemExit):
    raise
except Exception as e:
    fsr.log(e)
