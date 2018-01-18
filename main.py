import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial
import time
import tkinter as Tk

# User defined variables ##################################################
COM_PORT = "COM5" # Seen in the bottom-left of the Arduino IDE
SAVE_FILE = "sensordata/data_%i.txt" % time.time() # Name of the data file

BAUD_RATE = 9600 # Needs to coincide with Arduino code "Serial.begin(...)"
REFRESH_MS = 100 # Refresh the graph every (x) ms
POP_CUTOFF = 100 # The amount of data points to show on screen

Vcc = 5.06 # Input voltage of Arduino

# If both are -1, autofit is used
Y_RANGE_LOW = -1
Y_RANGE_HIGH = -1

SHOW_PINS = [0, 1] # Only show from A0, A1, A..etc inputs
###########################################################################

# Get current timestamp in ms
millis = lambda: int(round(time.time() * 1000.0))

# Appending to data file
def save_data(data):
    try:
        file = open(SAVE_FILE, "a")
        file.write(data)
        file.close()
    except Exception as e:
        print("Error saving data %s" % e)

# Convert the 0...1024 value to lux
def sensor_val_to_lux(val):
    res_volt = val * (Vcc / 1024) # Calc voltage over resistor (aprox. 5V supply, 10-bit reading, so 5/2^10 = 5/1024 V per value)
    return (500 / (10 * ((Vcc - res_volt) / res_volt)))
    
# Variable setup, don't touch
cols = ["b-", "r-", "g-", "b-", "m-", "c-"]
times = []
resistor_data = []

for pin in SHOW_PINS:
    times.append([])
    resistor_data.append([])

can_start = False # To wait for Arduino to give the go-ahead

# Initialize Tk
root = Tk.Tk()
root.wm_title("Sensor Data")

def _quit():
    root.quit()
    root.destroy()

button = Tk.Button(master=root, text="Quit", command=_quit)
button.pack(side=Tk.BOTTOM)

# Initialize matplotlib
# plt.rcParams["toolbar"] = "None" # Hide the toolbar for now, it breaks our code
lines = []
fig, ax1 = plt.subplots()
ax1.set_autoscale_on(True)
tmp = "Photoresistor Sensor Data\n%s" % (", ".join(("A%i: 0 lx" % pin) for pin in SHOW_PINS))
ax1.set_title(tmp)
ax1.set_ylabel("Sensor Value (lx)")
ax1.set_xlabel("Time (ms)")

# Instantiate a line in the graph for every pin we're reading
for pin in SHOW_PINS:
    tmp, = ax1.plot([], [], cols[pin])
    lines.append(tmp)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

# Instantiate Tk window for the first time
root.update_idletasks()
root.update()

# Wait for serial connection
while True:
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        break
    except serial.serialutil.SerialException as e:
        print("Connect Arduino to USB!")

    time.sleep(1)

# Generate an empty data file
file = open(SAVE_FILE, "w")
file.close()

# Main loop
timer = millis()
while True:
    draw = False
    data_in = ser.readline()

    # Check the received data
    if len(data_in) > 1:
        data_in = data_in.decode()

        if data_in.rstrip() == "INIT_COMPLETE":
            can_start = True
            print("Arduino initialized, starting!")
            print("Using pin%s A%s." % ("s" if len(SHOW_PINS) > 1 else "", ", A".join(str(pin) for pin in SHOW_PINS)))
            continue

        if can_start:
            save_data(data_in)

        unpack = data_in.rstrip().split(",")

        if len(unpack) == 3:
            try:
                timestamp = int(unpack[0])
                pin = int(unpack[1])
                res_val = int(unpack[2])
            except ValueError:
                print("Faulty serial communication: %s" % ",".join(unpack))
                continue

            if not pin in SHOW_PINS: # Skip the pins we don't want/need to read
                continue
            
            if can_start:
                # Appending to the proper array
                i = SHOW_PINS.index(pin)
                
                times[i].append(timestamp)
                #resistor_data[i].append(sensor_val_to_lux(res_val))
                resistor_data[i].append(res_val * ((Vcc * 1000) / 1024)) # Displays voltage in mV on y-axis
                
                if len(times[i]) > POP_CUTOFF:
                    times[i].pop(0)
                    resistor_data[i].pop(0)

                lines[i].set_data(times[i], resistor_data[i])
    
    # Draw when it's time to draw!
    if can_start:
        if (millis() - timer) >= REFRESH_MS:
            timer = millis()
            
            # Required to properly scale axes
            ax1.relim()
            ax1.autoscale_view(True, True, True)

            # Adjust scale of axes according to data
            if (Y_RANGE_LOW > -1) and (Y_RANGE_HIGH > -1):
                ax1.set_ylim(Y_RANGE_LOW, Y_RANGE_HIGH)
            else:
                if len(min(resistor_data)) > 0:
                    ax1.set_ylim(min([(min(i) - round(min(i) * 0.05)) for i in resistor_data]), \
                                 max([(max(i) + round(max(i) * 0.05)) for i in resistor_data])) # 5% margin above/below extreme values of lines

            if len(min(resistor_data)) > 0:
                tmp = "Photoresistor Sensor Data\n%s" % (", ".join(("A%i: %i lx" % (pin, resistor_data[i][-1])) for i, pin in enumerate(SHOW_PINS)))
                ax1.set_title(tmp)
            
            # Speeds up drawing tremendously
            ax1.draw_artist(ax1.patch)

            for line in lines:
                ax1.draw_artist(line)
                
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

    root.update_idletasks()
    root.update()


