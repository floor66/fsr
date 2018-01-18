import matplotlib.pyplot as plt
import serial
import time

millis = lambda: int(round(time.time() * 1000.0))

# User defined variables
COM_PORT = "COM5"
SAVE_FILE = "sensordata/data_%i.txt" % time.time()

BAUD_RATE = 9600
REFRESH_MS = 100
POP_CUTOFF = 100 # The amount of data points to show on screen

Vcc = 5.06

Y_RANGE_LOW = 0
Y_RANGE_HIGH = 1000 # If both are -1, autofit is used

SHOW_PINS = [0, 1] # Only show from A0, A1, A..etc inputs

# Variable setup, don't touch
cols = ["b-", "r-", "g-", "b-", "m-", "c-"]
times = []
resistor_data = []

for pin in SHOW_PINS:
    times.append([])
    resistor_data.append([])

can_start = False # To wait for Arduino to give the first timestamp

# Initiate matplotlib
lines = []
plt.ion()
fig, ax1 = plt.subplots()
ax1.set_autoscale_on(True)
ax1.set_title("Photoresistor Sensor Data\n")
ax1.set_ylabel("Sensor Value (lx)")
ax1.set_xlabel("Time (ms)")

# Instantiate a line for every pin we're reading
for pin in SHOW_PINS:
    tmp, = ax1.plot([], [], cols[pin])
    lines.append(tmp)

plt.show(block=False)
plt.pause(0.001)

# Wait for serial connection
connected = False
while not connected:
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        connected = True
    except serial.serialutil.SerialException:
        print("Connect Arduino to USB!")
        connected = False

    time.sleep(1)

# Generate a data file
file = open(SAVE_FILE, "w")
file.close()

# Appending to data file
def save_data(data):
    try:
        file = open(SAVE_FILE, "a")
        file.write(data)
        file.close()
    except:
        print("Error saving data")

# Convert the 0..1024 value to lux
def sensor_val_to_lux(val):
    res_volt = val * (Vcc / 1024) # Calc voltage over resistor (5V supply, 10-bit reading, so 5/2^10 = 5/1024 V per value)
    return (500 / (10 * ((Vcc - res_volt) / res_volt)))
    
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
            print("Arduino initialized, starting! Using pin%s A%s." % ("s" if len(SHOW_PINS) > 1 else "", ", A".join(str(pin) for pin in SHOW_PINS)))
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
                print(unpack)
                pass

            if not pin in SHOW_PINS:
                continue
            
            if can_start:
                # Appending to the proper array
                i = SHOW_PINS.index(pin)
                
                times[i].append(timestamp)
                resistor_data[i].append(sensor_val_to_lux(res_val))
                
                if len(times[i]) > POP_CUTOFF:
                    times[i].pop(0)
                    resistor_data[i].pop(0)

                lines[i].set_data(times[i], resistor_data[i])
    
    # Draw when it's time to draw!
    if can_start:
        if (millis() - timer) >= REFRESH_MS:
            timer = millis()
            
            # Somehow required?
            ax1.relim()
            ax1.autoscale_view(True, True, True)

            # Adjust scale of axes
            if (Y_RANGE_LOW > -1) and (Y_RANGE_HIGH > -1):
                ax1.set_ylim(Y_RANGE_LOW, Y_RANGE_HIGH)
            else:
                ax1.set_ylim(min(resistor_data), max(resistor_data))

            # Speeds up drawing tremendously
            ax1.draw_artist(ax1.patch)

            for line in lines:
                ax1.draw_artist(line)
                
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

plt.show()
