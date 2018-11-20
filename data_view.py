import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from utils import timerunning, millis
import numpy as np

##
to_show = "resists"
fns = (  "data_1541493946_2", "data_1541493946_3", "data_1541493946_4", "data_1541501475_2", "data_1541501475_3", "data_1541501475_4",)
wires = ("Mesh 1",            "Mesh 2",            "Mesh 3",            "PDSII 1",           "PDSII 2",           "PDSII 3",)
#fns = ("data_1541493946_2", "data_1541493946_3", "data_1541493946_4", "data_1541501475_2", "data_1541501475_3", "data_1541501475_4")
#wires = ("Mesh 1", "Mesh 2", "Mesh 3", "PDSII 1", "PDSII 2", "PDSII 3")

FREQ = 10
MOD_DIV = 1/10 # Show only every x seconds
GAP_THRESHOLD = 5000 # delete gaps greater than 5 sec (likely artefacts, see Figures/Data_artefacts
MAVG_WIND = 1000 # Window for moving average (50 * 20 = 1 sec)
##

fig = None
art = []
for fn in fns:
    __start__ = millis()
    f = open("sensordata/%s.txt" % fn.replace("annotations", "data"))
    data_lines = f.readlines()

    try:
        f = open("sensordata/%s.txt" % fn.replace("data", "annotations"))
        annot_lines = f.readlines()
    except FileNotFoundError:
        annot_lines = []

    # Get data + convert to val/volt/resist
    ts = []
    vals = []
    volts = []
    resists = []
    i = 0
    for l in data_lines:
        i += 1
        
        if l[0] != ";":
            if ((i % (FREQ * MOD_DIV)) == 0) or (i == 1):
                tmp = l.rstrip().split(",")

                if len(tmp) == 3:
                        try:
                            t = int(tmp[0])
                            v = int(tmp[2])
                        except ValueError:
                            continue

                        if v > 15000:
                            print("Off: %i" % t)

                        if v > 0:
                            voltage = (v * (5.06 / 1023))
                            r = 10000 * ((5.06 / voltage) - 1)
                            
                            ts.append(t)
                            vals.append(v)
                            volts.append(voltage)
                            resists.append(r)
                        else:
                            ts.append(t)
                            vals.append(0)
                            volts.append(0)
                            resists.append(None)

    # Remove gaps
    gaps = []
    print("Gaps:")

    for i, t in enumerate(ts):
        if i > 1:
            d = abs(ts[i] - ts[i - 1])
            
            if d > GAP_THRESHOLD:
                print("%i - %i = %i" % (ts[i], ts[i - 1], d))
                gaps.append(ts[i])
                gaps.append(ts[i - 1])

    for t in gaps:
        try:
            i = ts.index(t)
        except ValueError:
            continue
        
        ts.pop(i)
        vals.pop(i)
        volts.pop(i)
        resists.pop(i)

    # Averages
    vals_avg = [None]
    volts_avg = [None]
    resists_avg = [None]
    sum_ = 0

    for i, val in enumerate(vals):
        if i > 0:
            sum_ += val

            vals_avg.append(sum_ / i)

            if sum_ > 0:
                voltage = ((sum_ / i) * (5.06 / 1023))
                r = 10000 * ((5.06 / voltage) - 1)

                volts_avg.append(voltage)
                resists_avg.append(r)

    # Moving average
    N = MAVG_WIND # mavg window
    vals_mavg = [None for i in range(N)]
    volts_mavg = [None for i in range(N)]
    resists_mavg = [None for i in range(N)]
    sum_ = [0]

    for i, val in enumerate(vals):
        if i > 0:
            sum_.append(sum_[i - 1] + val)

            if i >= N:
                vals_mavg.append((sum_[i] - sum_[i - N]) / N)
                
                if (sum_[i - 1] + val) > 0:
                    voltage = (((sum_[i] - sum_[i - N]) / N) * (5.06 / 1023))
                    r = 10000 * ((5.06 / voltage) - 1) if voltage > 0 else 0

                    volts_mavg.append(voltage)
                    resists_mavg.append(r)

    raw = eval("%s" % to_show)
    avg = eval("%s_avg" % to_show)
    mavg = eval("%s_mavg" % to_show)

    if len(ts) < len(avg):
        avg = avg[:len(ts)]
    elif len(ts) > len(avg):
        ts = ts[:len(avg)]

    if len(ts) < len(mavg):
        mavg = mavg[:len(ts)]
    elif len(ts) > len(mavg):
        ts = ts[:len(mavg)]

    raw = raw[:len(ts)]

    # Format tickers
    def the_time(x, pos):
        return timerunning(x / 1000)

    formatter = FuncFormatter(the_time)

    # Plot data
    if fig is None:
        fig, ax = plt.subplots()
        
    ax.xaxis.set_major_formatter(formatter)
    
    #raw = [-r if r is not None else None for r in raw]
    #avg = [-a if a is not None else None for a in avg]
    #mavg = [-m if m is not None else None for m in mavg]

    #a, = ax.plot(ts, raw)
    #a, = ax.plot(ts, avg)
    a, = ax.plot(ts, mavg)

    art.append(a)
    nots = []
    msgs = []

    # Plot annotations
    if len(annot_lines) > 0:
        for l in annot_lines:
            t, msg = l.split(",")

            nots.append(ax.axvline(x=int(t), color=a.get_color(), linewidth=1, linestyle="dashed"))
            msgs.append(ax.text(int(t), 0, " %s" % msg, fontsize=16))
            
    # Bind hover event for annotations
    def hover(e):
        global __start__
        
        if ((millis() - __start__) < 50):
            return
        else:
            __start__ = millis()
        
        c = False
        
        for line in nots:
            if line.get_linestyle() != "dashed":
                line.set_linestyle("dashed")
                line.set_linewidth(1)
                c = True

            if e.inaxes == ax:
                cont, ind = line.contains(e)

                if cont:
                    line.set_linestyle("solid")
                    line.set_linewidth(2)
                    c = True

        if c:
            fig.canvas.draw_idle()

    def scroll(e):
        dir_ = e.button
        xlim = ax.get_xlim()
        xwidth = xlim[1] - xlim[0]
        xstep = round(xwidth * 0.1)

        if dir_ == "up":
            ax.set_xlim(left=xlim[0] + xstep, right=xlim[1] + xstep)
        elif dir_ == "down":
            ax.set_xlim(left=xlim[0] - xstep, right=xlim[1] - xstep)

        # Plot annotations
        if len(annot_lines) > 0:
            i = 0
            for l in annot_lines:
                t, msg = l.split(",")

                msgs[i].remove()
                msgs[i] = ax.text(int(t), ax.get_ylim()[0], " %s" % msg, fontsize=16)
                #del msgs[i]

                i += 1

        fig.canvas.draw_idle()
        
    #fig.canvas.mpl_connect("motion_notify_event", hover)
    fig.canvas.mpl_connect("scroll_event", scroll)

plt.xlim(0, 33 * 60 * 1000)
plt.ylim(4000, 13000)
plt.grid()
plt.gca().invert_yaxis()
plt.legend(art, wires)
plt.show()
