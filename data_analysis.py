import numpy as np
import matplotlib.pyplot as plt
from calculations import calculations

fn = "data_1541493946_2"
wire = "Mesh"

fn = "data_1541501475_2"
wire = "PDSII 2-0"

fig = None
calc = calculations(5.06, 10000)

with open("sensordata/%s.txt" % fn) as f:
    # Load data
    data_lines = f.readlines()
    ts = []
    vals = []
    for l in data_lines:
        if l[0] != ";":
            tmp = l.rstrip().split(",")

            if len(tmp) == 3:
                t = int(tmp[0])
                v = int(tmp[2])

                ts.append(t)
                vals.append(v)

    ts = np.array(ts)
    vals = np.array(vals)
    volts = (vals * (5.06 / 1023))
    resists = 10000 * ((5.06 / volts) - 1)
    newtons = np.array([calc.val_to_N(v) for v in vals])

    newtons_n = [n - newtons[0] for n in newtons]

    if fig is None:
        fig, ax = plt.subplots()

    ax.plot(ts, newtons_n)
    #ax.plot(newtons_d)
    plt.show()
