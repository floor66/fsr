import matplotlib.pyplot as plt
import serial, time

# User defined variables
COM_PORT = "COM5"
SAVE_FILE = "sensordata/data_%i.txt" % time.time()

BAUD_RATE = 9600
REFRESH_MS = 100
POP_CUTOFF = 200

Y_RANGE_LOW = 0
Y_RANGE_HIGH = 0 # If both are 0, autofit is used

# Variable setup, don't touch
times = []
resistor_data = []
count = 0
zero_received = False # To wait for Arduino to give the first timestamp
last_draw_time = 0

# Initiate matplotlib
plt.ion()
fig, ax1 = plt.subplots()
ax1.set_autoscale_on(True)
ax1.set_ylabel("Sensor Value (lx)")
ax1.set_xlabel("Time (ms)")
line, = ax1.plot([], [], "r-")
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

file = open(SAVE_FILE, "w")
file.close()

def save_data(data):
    try:
        file = open(SAVE_FILE, "a")
        file.write(data)
        file.close()
    except:
        print("Error saving data")

while True:
    draw = False
    data_in = ser.readline()

    # Check the received data
    if len(data_in) > 1:
        data_in = data_in.decode()

        if zero_received:
            save_data(data_in)

        unpack = data_in.rstrip().split(",")

        if len(unpack) == 3:
            try:
                time = int(unpack[0])
                pin = int(unpack[1])
                res_val = int(unpack[2])
            except ValueError:
                print(unpack)
                pass

                continue
            
            if time == 0:
                zero_received = True
                save_data(data_in) # Else we ommit the 0-reading
                print("Time = 0 received, starting!")

            if zero_received:
                if len(times) > 0:
                    if ((time - last_draw_time) >= REFRESH_MS) or (len(times) == 1): # Only draw every REFRESH_MS ms, or the first time
                        last_draw_time = time
                        draw = True
                
                times.append(time)

                res_volt = res_val * (5 / 1024) # Calc voltage over resistor (5V supply, 10-bit reading, so 5/2^10 = 5/1024 V per value)
                lux = 500 / (10 * ((5 - res_volt) / res_volt))
                resistor_data.append(lux)
                
                count += 1
                
                if count > POP_CUTOFF:
                    times.pop(0)
                    resistor_data.pop(0)
    
    # Draw when it's time to draw!
    if zero_received and draw:
        line.set_data(times, resistor_data)

        # Somehow required?
        ax1.relim()
        ax1.autoscale_view(True, True, True)
        ax1.set_title("Photoresistor Sensor Data (Current: %i lx)\n" % resistor_data[-1])
        if (Y_RANGE_LOW > 0) and (Y_RANGE_HIGH > 0):
            ax1.set_ylim(Y_RANGE_LOW, Y_RANGE_HIGH)
        else:
            ax1.set_ylim(min(resistor_data), max(resistor_data))


        # Speeds up drawing tremendously
        ax1.draw_artist(ax1.patch)
        ax1.draw_artist(line)
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

plt.show()
