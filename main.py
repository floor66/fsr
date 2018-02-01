"""
    main.py
    Created by Floris P.J. den Hartog, 2018

    Main file for the GUI / processing of Force Sensitive Resistor data
    Used in conjunction with Arduino for analog-digital conversion
"""

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
        self.recordings = 0
        self.curr_rec_count = 0
        
####### User defined variables ##############################################################
        self.COM_PORT = "COM5" # Seen in the bottom-right of the Arduino IDE

        self.BAUD_RATE = 500000 # Needs to coincide with Arduino code "Serial.begin(...)" (!)
        self.INIT_TIMEOUT = 5 # The amount of seconds to wait for Arduino to initialize

        self.Vcc = 5.06 # Input voltage of Arduino in V

        # If both are None, autofit is used
        #self.Y_RANGE_LOW = -10
        #self.Y_RANGE_HIGH = 1023

        self.NUM_ANALOG = 6 # 6 max possible analog pins
        
        self.pulldown = 10000 # 10 kOhm pulldown resistance
#############################################################################################
        
        # Misc. variable setup, don't touch
        self.LOG_FILE = "logs/log_%i.txt" % self.__start__
        self.recording = False

        self.OPT_RAW = 0
        self.OPT_VOLTAGE = 1
        self.OPT_RESISTANCE = 2
        self.OPT_CONDUCTANCE = 3
        self.OPT_VOLTAGE_AVG = 4
        self.OPT_RESISTANCE_AVG = 5
        self.OPT_CONDUCTANCE_AVG = 6

        self.SHOW_PINS = [] # Linked to checkbuttons
        self.REC_PINS = [] #TEMPORARY! MAKE CHECKBOXES FOR
        self.touch(self.LOG_FILE) # Generate an empty log file

        self.log("Logging started @ %s (GMT)" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        self.init_gui()
        self.reset_vars()

    def timerunning(self, sec):
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        
        return "%d:%02d:%02d" % (h, m, s)

    # Log to console and to a log file
    def log(self, msg):
        timerunning = self.timerunning(time.time() - self.__start__)
        
        print("%s - %s" % (timerunning, msg))
        
        file = open(self.LOG_FILE, "a")
        file.write("%s - " % timerunning)
        file.write(str(msg))
        file.write("\n")
        file.close()
    
    # At-a-glance status label
    def status(self, txt):
        self.status_lbl.configure(text="%s" % txt)

    def val_to_volt(self, val):
        return val * (self.Vcc / (2**10 - 1)) if val > 0 else 0

    """
    FSR spec sheet says:
      VOUT = (V+) / [1 + RFSR/RM]
      
    Where:
      VOUT is measured by Arduino on the analog pin
        the pin gives a value of 0-1023, corresponding to (Vcc / 2^10) different "steps" of voltage
      V+ = Vcc (power source to Arduino)
      RFSR = the "unknown" we want to know (!)
      RM = pulldown resistance

    So, in our words and some algebra:
      res_volt = Vcc / (1 + (Rfsr / Rp))
      
      (1 + (Rfsr / Rp)) * res_volt = Vcc   | Div both sides by (1 + (Rfsr / Rp))
      (1 + (Rfsr / Rp)) = (Vcc / res_volt) | Div both sides by res_volt
      (Rfsr / Rp) = ((Vcc / res_volt) - 1) | Subtract both by 1
      Rfsr = Rp * ((Vcc / res_volt) - 1)   | Multiply both by Rp
    """
    def volt_to_Rfsr(self, volt):
        # return ((self.Vcc * self.pulldown) / volt) - self.pulldown (old formula, works the same but less evidence)
        return self.pulldown * ((self.Vcc / volt) - 1) if volt > 0 else 0

    def val_to_N(self, val):
        if(val > 0):
            res_volt = self.val_to_volt(val)
            Rfsr = self.volt_to_Rfsr(res_volt)

            if Rfsr > 0:
                cond = 1 / Rfsr # Conductance = 1 / Resistance and vice-versa
            else:
                return 0
            
            # y = 96892x-1,292
            force = 96892 * (Rfsr**-1.292)
            # Not really correct, reference website rounded too much

            return force

            """
            #print("Vfsr = %.10f V" % res_volt)
            #print("Rfsr = %.10f Ohm" % Rfsr)
            #print("Cfsr = %.10f S" % cond)
            """
        else:
            return 0

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
        self.resistor_data_raw = []
        self.resistor_data = []
        
        for i in range(0, self.NUM_ANALOG):
            self.times.append([])
            self.resistor_data_raw.append([]) # Raw sensor readouts, these are used for calculations
            self.resistor_data.append([]) # Processed sensor readouts (voltage, resistance, etc.), these are drawn
            
            self.lines[i].set_data([], [])

    def check_rec_pins(self):
        if self.recording:
            if len(self.REC_PINS) > 0:
                self.log("Recording from pin%s A%s" % ("s" if len(self.REC_PINS) > 1 else "", ", A".join(str(pin) for pin in self.REC_PINS)))
                self.status("Recording #%i active...\nSaving: A%s" % (self.recordings, ", A".join(str(pin) for pin in self.REC_PINS)))
            else:
                self.log("Warning: no data is being saved! Please check 'Save data' for the pin(s) you wish to record.")
                self.status("Recording #%i active...\nWarning: no data is being saved!" % self.recordings)

    def rec_stop(self):
        self.recording = False
        self.log("Stopping recording, saved %i measurements" % self.curr_rec_count)

        self.reset_vars()

        try:
            self.ser.close() # Close the serial connection
        except AttributeError:
            pass # Occurs when the serial connection was never established
        except Exception as e:
            self.log(e)
            
        self.rec_stop_btn.configure(state="disabled")
        self.rec_start_btn.configure(state="normal")
        self.status("Recording stopped")

    def rec_start(self):
        self.recording = True
        self.status("Initiating connection")

        self.rec_start_btn.configure(state="disabled")
        self.rec_stop_btn.configure(state="normal")

        # Check if we can initiate the serial communication
        if self.init_serial():
            self.status("Connection initiated (COM port: %s)" % self.COM_PORT)
            self.recordings += 1
            self.SAVE_FILE = "sensordata/data_%i_%i.txt" % (self.__start__, self.recordings)
            self.touch(self.SAVE_FILE) # Generate a new, empty data file

            self.log("Arduino initialized, starting recording #%i of this session" % self.recordings)
            self.log("Currently recording to file: %s" % self.SAVE_FILE)
            self.save_data("; Recording @ 50 Hz\n")
            self.save_data("; Vcc = %.02f V, pulldown = %i Ohm\n" % (self.Vcc, self.pulldown))
            self.save_data("; Key: time (ms), pin (A0-5), readout (0-1023)\n")

            self.check_rec_pins()
            self.__rec_start__ = time.time()
            self.record()
        else:
            self.recording = False
            
            self.rec_start_btn.configure(state="normal")
            self.rec_stop_btn.configure(state="disabled")

            self.status("Connection failed")
            self.log("Connection failed")

    def quit_gui(self):
        if Tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()
            self.root.destroy()

            self.log("GUI exit")

    def toggle_sensor_display(self):
        for i in range(0, self.NUM_ANALOG):
            changed = False
            state = self.sensor_display_vars[i].get()

            if state == 1:
                if not i in self.SHOW_PINS:
                    self.SHOW_PINS.append(i)
                    changed = True
            elif state == 0:
                if i in self.SHOW_PINS:
                    self.SHOW_PINS.pop(self.SHOW_PINS.index(i))
                    changed = True

            if changed:
                self.log("Reset display data for Pin A%i" % i)
                self.times[i] = []
                self.resistor_data_raw[i] = []
                self.resistor_data[i] = []
                self.lines[i].set_data([], [])

    def toggle_sensor_record(self):
        for i in range(0, self.NUM_ANALOG):
            changed = False
            state = self.sensor_record_vars[i].get()

            if state == 1:
                if not i in self.REC_PINS:
                    self.REC_PINS.append(i)
                    changed = True
            elif state == 0:
                if i in self.REC_PINS:
                    self.REC_PINS.pop(self.REC_PINS.index(i))
                    changed = True

            if changed:
                self.check_rec_pins()

    def y_unit_change(self, val):
        try:
            i = self.y_unit_opts.index(val)
        except ValueError:
            val = self.y_unit_opts[0]

        self.ax1.set_ylabel(val)
        self.reset_vars()
                
    def init_gui(self):
        # Initialize Tk, create layout elements
        self.root = Tk.Tk()
        self.root.wm_title("Sensor Data (%i)" % self.__start__)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_gui)

        # Required to make the plot resize with the window, row0 col1 (= the plot) gets the "weight"
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # So that we lose Entry focus on clicking anywhere
        self.root.bind_all("<1>", lambda event:event.widget.focus_set())

        self.panel_left = Tk.Frame(master=self.root)
        self.panel_right = Tk.Frame(master=self.root)
        self.canvas_container = Tk.Frame(master=self.root)

        # Left panel

        # Status label+frame
        self.status_frame = Tk.LabelFrame(master=self.panel_left, text="Status")
        self.status_lbl = Tk.Label(master=self.status_frame)
        self.status_lbl.pack()
        self.status("Disconnected")
        
        # Start/stop buttons+frame
        self.controls_frame = Tk.LabelFrame(master=self.panel_left, text="Controls", pady=10)
        self.rec_start_btn = Tk.Button(master=self.controls_frame, text="Start Recording", command=self.rec_start)
        self.rec_stop_btn = Tk.Button(master=self.controls_frame, text="Stop Recording", command=self.rec_stop)
        self.rec_stop_btn.configure(state="disabled")

        # Graph refresh scale
        self.REFRESH_MS = Tk.IntVar()
        self.REFRESH_MS.set(250)
            
        self.refresh_entry = Tk.Scale(master=self.controls_frame, length=150, from_=1, to=1000, resolution=25, label="Graph refreshrate (ms)", orient=Tk.HORIZONTAL, variable=self.REFRESH_MS)

        # The amount of data points to show on screen
        self.POP_CUTOFF = Tk.IntVar()
        self.POP_CUTOFF.set(1000)

        self.cutoff_entry = Tk.Scale(master=self.controls_frame, length=150, from_=100, to=2500, resolution=100, label="Datapoints to show", orient=Tk.HORIZONTAL, variable=self.POP_CUTOFF)

        # Y-axis unit selection
        self.y_unit = Tk.StringVar()
        self.y_unit_opts = ["Raw value (0-1023)", "Voltage (mV)", "Resistance (Ohm)", "Conductance (uS)", \
                            "Avg. voltage (mV)", "Avg. resistance (Ohm)", "Avg. conductance (uS)"]
        self.y_unit.set(self.y_unit_opts[self.OPT_RAW])
        
        self.unit_select_label = Tk.Label(master=self.controls_frame, text="Y-axis unit:")
        self.unit_select_opts = Tk.OptionMenu(self.controls_frame, self.y_unit, *self.y_unit_opts, command=self.y_unit_change)
        
        # Y-axis scaling
        self.Y_RANGE_LOW = Tk.IntVar()
        self.Y_RANGE_HIGH = Tk.IntVar()
        self.Y_RANGE_LOW.set("")
        self.Y_RANGE_HIGH.set("")

        self.scaling_label = Tk.Label(master=self.controls_frame, text="Y-axis scale:")
        self.y_low_label = Tk.Label(master=self.controls_frame, text="Minimum")
        self.y_high_label = Tk.Label(master=self.controls_frame, text="Maximum")
        self.y_low_entry = Tk.Entry(master=self.controls_frame, textvariable=self.Y_RANGE_LOW, width=6)
        self.y_high_entry = Tk.Entry(master=self.controls_frame, textvariable=self.Y_RANGE_HIGH, width=6)
        self.scaling_label_under = Tk.Label(master=self.controls_frame, text="(Empty = auto-scaling)")
        
        # Setup the grid within panel_left
        self.rec_start_btn.grid(row=0, column=0, columnspan=2)
        self.rec_stop_btn.grid(row=1, column=0, columnspan=2)
        self.refresh_entry.grid(row=3, column=0, pady=10, columnspan=2)
        self.cutoff_entry.grid(row=4, column=0, columnspan=2)

        self.scaling_label.grid(row=5, column=0, pady=(10, 0), columnspan=2)
        self.y_low_label.grid(row=6, column=0)
        self.y_low_entry.grid(row=6, column=1)
        self.y_high_label.grid(row=7, column=0)
        self.y_high_entry.grid(row=7, column=1)
        self.scaling_label_under.grid(row=8, column=0, columnspan=2)

        self.unit_select_label.grid(row=9, column=0, columnspan=2, pady=(10, 0))
        self.unit_select_opts.grid(row=10, column=0, columnspan=2)
        
        self.status_frame.grid(row=0, column=0, sticky="nsew")
        self.controls_frame.grid(row=1, column=0, sticky="nsew", pady=10)

        self.panel_left.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        # Quit button
        self.quit_btn = Tk.Button(master=self.root, text="Quit", command=self.quit_gui)
        self.quit_btn.grid(row=0, column=0, sticky="s", pady=5)

        # Init matplotlib graph at this point
        self.init_mpl()

        # Right panel

        # Display selection frame
        self.sensor_select_frame = Tk.LabelFrame(master=self.panel_right, padx=5, text="Sensor selection")

        self.sensor_select_labels = [Tk.Label(master=self.sensor_select_frame, text="Pin A%i:" % i) for i in range(0, self.NUM_ANALOG)]
        self.sensor_record_boxes = []
        self.sensor_display_boxes = []
        self.sensor_record_vars = [Tk.IntVar() for i in range(0, self.NUM_ANALOG)]
        self.sensor_display_vars = [Tk.IntVar() for i in range(0, self.NUM_ANALOG)]
        j = 0
        for i in range(0, self.NUM_ANALOG):
            self.sensor_select_labels[i].grid(row=j, column=0)
            
            self.sensor_display_boxes.append(Tk.Checkbutton(master=self.sensor_select_frame, text="Display in graph", \
                                                            command=self.toggle_sensor_display, variable=self.sensor_display_vars[i]))
            
            self.sensor_record_boxes.append(Tk.Checkbutton(master=self.sensor_select_frame, text="Save data", \
                                                            command=self.toggle_sensor_record, variable=self.sensor_record_vars[i]))
            
            self.sensor_display_boxes[i].grid(row=j, column=1, sticky="w")
            self.sensor_record_boxes[i].grid(row=(j+1), column=1, sticky="w", pady=(0, (5 if i < (self.NUM_ANALOG - 1) else 0)))

            j += 2

        self.sensor_select_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Sensor readouts frame
        self.sensor_readout_frame = Tk.LabelFrame(master=self.panel_right, padx=5, text="Live readouts")

        # Create 1 label per pin
        self.sensor_readouts = [Tk.Label(master=self.sensor_readout_frame, text=("Pin A%i: 0 mV / 0.00 N" % i)) for i in range(0, self.NUM_ANALOG)]
        for i in range(0, self.NUM_ANALOG):
            self.sensor_readouts[i].pack(side=Tk.TOP, anchor="w")

        self.sensor_readout_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Apply grid to right panel
        self.panel_right.grid(row=0, column=2, sticky="n")

    def init_mpl(self):
        # Initialize matplotlib
        self.lines = []
        self.cols = ["b-", "r-", "g-", "b-", "m-", "c-"]
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_autoscale_on(True)
        self.ax1.set_title("Sensor Data\n")
        self.ax1.set_ylabel(self.y_unit.get())
        self.ax1.set_xlabel("Time (ms)")

        # Instantiate a line in the graph for every pin we could potentially read
        for i in range(0, self.NUM_ANALOG):
            tmp, = self.ax1.plot([], [], self.cols[i])
            self.lines.append(tmp)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_container)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=Tk.BOTH, expand=1)

        self.canvas_container.grid(row=0, column=1, sticky="nesw")

        # Instantiate Tk window for the first time
        self.update()

    def init_serial(self):
        self.can_start = False # To wait for Arduino to give the go-ahead

        # Wait for serial connection
        timer = millis()
        while True:
            self.update()

            if not self.recording:
                return False
            
            try:
                self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE)
                break
            except serial.serialutil.SerialException as e:
                if (millis() - timer) >= 1000: # Give an error every second
                    self.status("Connect Arduino to USB!")
                    self.log("Connect Arduino to USB!")
                    timer = millis()

        # Wait for the go-ahead from Arduino
        timer = millis()
        while True:
            self.update()

            if not self.recording:
                return False
            
            data_in = self.ser.readline()

            if len(data_in) > 0:
                try:
                    data_in = data_in.decode().rstrip()

                    if data_in == "INIT_COMPLETE":
                        self.can_start = True
                        return True
                except Exception as e:
                    self.log(e)

            if (millis() - timer) >= (self.INIT_TIMEOUT * 1000):
                self.log("Arduino failed to initialize after %i sec" % self.INIT_TIMEOUT)
                return False

    # Main loop
    def record(self):
        if not self.can_start:
            return False
        
        self.draw_timer = millis()
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

                    if pin in self.REC_PINS:
                        self.curr_rec_count += 1
                        self.save_data(data_in) # Save the data to file

                    # Display readout in the proper label
                    self.sensor_readouts[pin].config(text="Pin A%i: %i mV / %.02f N" % (pin, self.val_to_volt(res_val) * 1000, self.val_to_N(res_val)))
                    
                    if not pin in self.SHOW_PINS: # Skip the pins we don't want/need to read
                        continue
                   
                    self.times[pin].append(timestamp)
                    self.resistor_data_raw[pin].append(res_val)
                    
                    # Here we can interject and do calculations based on which y-axis unit we want to see
                    opt = self.y_unit_opts.index(self.y_unit.get())
                    
                    if opt == self.OPT_RAW:
                        self.resistor_data[pin].append(res_val)
                    elif opt == self.OPT_VOLTAGE:
                        a = self.val_to_volt(res_val) * 1000
                        self.resistor_data[pin].append(a)
                    elif opt == self.OPT_RESISTANCE:
                        a = self.volt_to_Rfsr(self.val_to_volt(res_val))
                        self.resistor_data[pin].append(a)
                    elif opt == self.OPT_CONDUCTANCE:
                        a = 10**6 / self.volt_to_Rfsr(self.val_to_volt(res_val)) if res_val > 0 else 0
                        self.resistor_data[pin].append(a)
                    elif opt == self.OPT_VOLTAGE_AVG:
                        a = sum([self.val_to_volt(v) * 1000 for v in self.resistor_data_raw[pin]]) / len(self.resistor_data_raw[pin]) if len(self.resistor_data_raw[pin]) > 0 else 0
                        self.resistor_data[pin].append(a)
                    elif opt == self.OPT_RESISTANCE_AVG:
                        a = sum([self.volt_to_Rfsr(self.val_to_volt(v)) for v in self.resistor_data_raw[pin]]) / len(self.resistor_data_raw[pin]) if len(self.resistor_data_raw[pin]) > 0 else 0
                        self.resistor_data[pin].append(a)
                    elif opt == self.OPT_CONDUCTANCE_AVG:
                        a = sum([10**6 / self.volt_to_Rfsr(self.val_to_volt(v)) if v > 0 else 0 for v in self.resistor_data_raw[pin]]) / len(self.resistor_data_raw[pin]) if len(self.resistor_data_raw[pin]) > 0 else 0
                        self.resistor_data[pin].append(a)

                    self.lines[pin].set_data(self.times[pin], self.resistor_data[pin])

                    if len(self.times[pin]) > self.POP_CUTOFF.get():
                        self.times[pin] = self.times[pin][-self.POP_CUTOFF.get():]
                        self.resistor_data_raw[pin] = self.resistor_data_raw[pin][-self.POP_CUTOFF.get():]
                        self.resistor_data[pin] = self.resistor_data[pin][-self.POP_CUTOFF.get():]

            self.draw()

    def draw(self):
        # Draw when it's time to draw!
        if (millis() - self.draw_timer) >= self.REFRESH_MS.get():
            self.draw_timer = millis()

            self.ax1.set_title("Sensor data\nRecording: %s\n" % self.timerunning(time.time() - self.__rec_start__))
            
            # Required to properly scale axes
            self.ax1.relim()
            self.ax1.autoscale_view(True, True, True)

            # Adjust scale of axes according to data/entries
            try:
                low_entry = int(self.Y_RANGE_LOW.get())
            except Exception as e:
                low_entry = None

            try:
                high_entry = int(self.Y_RANGE_HIGH.get())
            except Exception as e:
                high_entry = None

            low_data = None
            high_data = None
            
            for i in range(0, self.NUM_ANALOG):
                try:
                    min_ = min(self.resistor_data[i])
                    max_ = max(self.resistor_data[i])

                    if (low_data is None) or (min_ < low_data):
                        low_data = min_

                    if (high_data is None) or (max_ > high_data):
                        high_data = max_
                except ValueError:
                    pass
                except Exception:
                    raise

            if low_entry is not None:
                if high_entry is not None:
                    self.ax1.set_ylim(low_entry, high_entry)
                else:
                    self.ax1.set_ylim(low_entry, high_data + ((high_data if high_data > 0 else 1) * 0.05))
            else:
                if high_entry is not None:
                    self.ax1.set_ylim(low_data - ((low_data if low_data > 0 else 1) * 0.05), high_entry)
                else:
                    self.ax1.set_ylim(low_data - ((low_data if low_data > 0 else 1) * 0.05), \
                                      high_data + ((high_data if high_data > 0 else 1) * 0.05))

            # Speeds up drawing tremendously
            self.ax1.draw_artist(self.ax1.patch)

            for i in range(0, self.NUM_ANALOG):
                if i in self.SHOW_PINS:
                    self.ax1.draw_artist(self.lines[i])
                
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()

if __name__ == "__main__":
    try:
        fsr = FSR()
    except (KeyboardInterrupt, SystemExit): # Doesn't function yet
        fsr.quit_gui()
        raise
    except Exception as e:
        fsr.log(e)
