import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from utils import timerunning, millis
import numpy as np
from scipy import signal
from math import sqrt

trials = []
wires = []

##
plot_annot = False
to_show = "vals"
display_type = "raw"
run_stats = False

trials.append(("Varkens april/data_1554215695_4", "Mesh porcine 1", 63204))
trials.append(("Varkens april/data_1554215695_5", "Mesh porcine 1", 244208))

#trials.append(("varken/data_1548877691_2", "PDSII 2-0 porcine 1", 129904))
#trials.append(("varken/data_1548877691_3", "PDSII 2-0 porcine valid 2", 129208))

"""
trials.append(("data_1541493946_2", "Mesh 1", 250408))
trials.append(("data_1541493946_3", "Mesh 2", 121808))
trials.append(("data_1541493946_4", "Mesh 3", 121404))
trials.append(("data_1542112623_1", "Mesh 4", 118704))
trials.append(("data_1542112623_2", "Mesh 5", 117208))
trials.append(("data_1542112623_4", "Mesh 6", 23208))
trials.append(("data_1542704461_1", "Mesh 7", 315304))
trials.append(("data_1542710800_1", "Mesh 8", 124008))
trials.append(("data_1542718474_1", "Mesh 9", 129604))
trials.append(("data_1543304291_1", "Mesh 10", 120704))
trials.append(("data_1543308523_1", "Mesh 11", 171204))
trials.append(("data_1543308523_2", "Mesh 12", 126604))

trials.append(("data_1541501475_2", "PDSII 1", 174708))
trials.append(("data_1541501475_3", "PDSII 2", 67504))
trials.append(("data_1541501475_4", "PDSII 3", 114404))
trials.append(("data_1542276705_1", "PDSII 4", 30708))
trials.append(("data_1542276705_2", "PDSII 5", 182804))
trials.append(("data_1542276705_3", "PDSII 6", 198104))
trials.append(("data_1542891862_2", "PDSII 7", 114204))
trials.append(("data_1542895007_2", "PDSII 8", 120904))
trials.append(("data_1542895007_3", "PDSII 9", 120804))
trials.append(("data_1543308523_3", "PDSII 10", 130504))
trials.append(("data_1543308523_4", "PDSII 11", 120408))
trials.append(("data_1543308523_5", "PDSII 12", 180608))

trials.append(("data_1544520811_1", "PDSII validering 1", 120704))
trials.append(("data_1544520811_2", "PDSII validering 2", 120804))
trials.append(("data_1544520811_3", "PDSII validering 3", 120208))
"""
FREQ = 10 # Measuring frequency
SHOW_EVERY = 1 # Show only every x measurements
GAP_THRESHOLD = 2000 # delete gaps greater than x msec (likely artefacts, see Figures/Data_artefacts
MAVG_WIND = 1000 # Msec window for moving average (50 * 20 = 1 sec)
##

raws = []

# Note: Iterate through trials and append a new trial for each sensor

fig = None
art = []
for fn, wire, baseline in trials:
    __start__ = millis()
    wires.append(wire)

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
    newtons = []
    i = 0
    for l in data_lines:
        i += 1
        
        if l[0] != ";":
            tmp = l.rstrip().split(",")

            if len(tmp) == 3:
                try:
                    t = int(tmp[0])
                    v = int(tmp[2])
                except ValueError:
                    continue

                if v > 1023:
                    print("Off: %i at %i in %s" % (v, t, fn))

                if v > 0:
                    voltage = (v * (5.06 / 1023))
                    r = 10000 * ((5.06 / voltage) - 1)
                    n = (96892 * (r**-1.292)) * 9.8066500286389
                    
                    ts.append(t)
                    vals.append(v)
                    volts.append(voltage)
                    resists.append(r)
                    newtons.append(n)
                else:
                    ts.append(t)
                    vals.append(0)
                    volts.append(0)
                    resists.append(None)
                    newtons.append(None)

    # Get base tension
    base = ts.index(baseline)

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
        newtons.pop(i)

    # Averages
    vals_avg = [None]
    volts_avg = [None]
    resists_avg = [None]
    newtons_avg = [None]
    sum_ = 0

    for i, val in enumerate(vals):
        if i > 0:
            sum_ += val

            vals_avg.append(sum_ / i)

            if sum_ > 0:
                voltage = ((sum_ / i) * (5.06 / 1023))
                r = 10000 * ((5.06 / voltage) - 1)
                n = (96892 * (r**-1.292)) * 9.8066500286389

                volts_avg.append(voltage)
                resists_avg.append(r)
                newtons_avg.append(n)

    # Moving average
    N = MAVG_WIND # mavg window
    vals_mavg = [None for i in range(N)]
    volts_mavg = [None for i in range(N)]
    resists_mavg = [None for i in range(N)]
    newtons_mavg = [None for i in range(N)]
    sum_ = [0]

    for i, val in enumerate(vals):
        if i > 0:
            sum_.append(sum_[i - 1] + val)

            if i >= N:
                vals_mavg.append((sum_[i] - sum_[i - N]) / N)
                
                if (sum_[i - 1] + val) > 0:
                    voltage = (((sum_[i] - sum_[i - N]) / N) * (5.06 / 1023))
                    r = 10000 * ((5.06 / voltage) - 1) if voltage > 0 else 0
                    n = (96892 * (r**-1.292)) * 9.8066500286389 if voltage > 0 else 0

                    volts_mavg.append(voltage)
                    resists_mavg.append(r)
                    newtons_mavg.append(n)

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
    
    # Normalizing & drawing data
    col = "blue" if wire.find("valid") > -1 else "red"
    filter_n = 25
    a = None

    if display_type == "raw":
        # For relative measurements
        for i, r in enumerate(raw):
            if r is None:
                raw[i] = 0
        
        raw = [r - raw[base] for r in raw]

        #a, = ax.plot(ts[base::SHOW_EVERY], raw[base::SHOW_EVERY], col)
        a, = ax.plot(ts[base::SHOW_EVERY], signal.lfilter([1.0 / filter_n] * filter_n, 1, raw[base::SHOW_EVERY]), col)
        #raws.append(np.array(raw[base::SHOW_EVERY]))
    elif display_type == "avg":
        avg[1:] = [a - avg[base] for a in avg[1:]]
        a, = ax.plot(ts, avg, col)
    elif display_type == "mavg":
        mavg = [m - mavg[base] for m in mavg]
        a, = ax.plot(ts, mavg, col)

    art.append(a)
    nots = []
    msgs = []

    # Plot annotations
    if (len(annot_lines) > 0) and plot_annot:
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
        xstep = round(xwidth * 0.01)

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

if run_stats:
    # Statistics
    stats = []
    averages = []
    times = []
    confidence = []

    MESH = 0
    stats.append((0, 12))

    PDS = 1
    stats.append((12, 24))

    PDS_V = 2
    stats.append((24, 27))

    for a, b in stats:
        subset_raws = raws[a:b]
        print(len(subset_raws))
        L = min([len(r) for r in subset_raws])
        time = ts[0:L]
        subset_raws = [r[0:L] for r in subset_raws]

        all_data = [[] for i in range(L)]
        for i, line in enumerate(subset_raws):
            for j, point in enumerate(line):
                all_data[j].append(point)

        subset_avg = [np.mean(np.array(a)) for a in all_data]
        subset_std = [np.std(np.array(a)) for a in all_data]
        subset_sem = [std / sqrt(len(subset_raws)) for std in subset_std]
        ci_subset_upper = [subset_avg[i] + (1.96 * subset_sem[i]) for i in range(len(subset_avg))]
        ci_subset_lower = [subset_avg[i] - (1.96 * subset_sem[i]) for i in range(len(subset_avg))]

        times.append(time)
        averages.append(subset_avg)
        confidence.append((ci_subset_lower, ci_subset_upper))

    # Plot what needs to be plotted
    filter_n = 25
    i = MESH
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, averages[i]), "blue")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][0]), "black")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][1]), "black")

    i = PDS
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, averages[i]), "red")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][0]), "grey")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][1]), "grey")

    i = PDS_V
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, averages[i]), "blue")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][0]), "black")
    ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][1]), "black")

plt.xlim(0, 33 * 60 * 1000)
#plt.ylim(0, 16)
plt.grid()
#plt.gca().invert_yaxis()
#plt.legend(art, wires)
plt.ylabel("Force (N)")
plt.xlabel("Time (h:mm:ss)")
plt.title("Suture tension over 30 mins at 20 mmHg intra-abdominal pressure in a porcine abdominal wall\nPDS II 2-0 (N = 2)\n")
plt.show()

