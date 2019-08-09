import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
from utils import timerunning, millis
import numpy as np
from scipy import signal
from scipy.stats import *
from math import sqrt, floor

from data_input import trials
wires = []
stats = []

##
plot_annot = False
to_show = "newtons"
display_type = "raw"
##
run_stats = True
show_pvals = False
show_bands = False
stats.append((0, len(trials) // 2))
stats.append((len(trials) // 2, len(trials)))
##
FREQ = 10 # Measuring frequency
SHOW_EVERY = 1 # Show only every x measurements
GAP_THRESHOLD = 2000 # delete gaps greater than x msec (likely artefacts, see Figures/Data_artefacts
MAVG_WIND = 1000 # Msec window for moving average (50 * 20 = 1 sec)
##

raws = []

fig = None
art = []
for fn, wire, baseline, sensor in trials:
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
                    s = int(tmp[1])
                    v = int(tmp[2])
                except ValueError:
                    continue

                # s + 1 to prevent confusion (sensor 1 = 0, sensor 2 = 1, etc.)
                if (s + 1) != sensor:
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
    base = None
    for i, t in enumerate(ts):
        if t >= baseline:
            base = i
            break

    # Remove gaps
    gaps = []

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
        global SHOW_EVERY
        return timerunning(x / 1000 * SHOW_EVERY)

    formatter = FuncFormatter(the_time)

    # Plot data
    if fig is None:
        fig, ax = plt.subplots()
        
    ax.xaxis.set_major_formatter(formatter)
    
    # Normalizing & drawing data
    col = "blue" if wire.find("PDS L") > -1 else "red"
    filter_n = 25
    a = None

    if display_type == "raw":
        # For relative measurements
        for i, r in enumerate(raw):
            if r is None:
                raw[i] = 0
        
        raw = [r - raw[base] for r in raw]

        #a, = ax.plot(ts[base::SHOW_EVERY], raw[base::SHOW_EVERY], col)
        #a, = ax.plot(ts[base::SHOW_EVERY], signal.lfilter([1.0 / filter_n] * filter_n, 1, raw[base::SHOW_EVERY]), col)
        raws.append(np.array(raw[base::SHOW_EVERY]))
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
    averages = []
    medians = []
    times = []
    confidence = []
    all_datas = []

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
        subset_med = [np.median(np.array(a)) for a in all_data]

        if show_bands:
            ci_subset_upper = [np.percentile(np.array(a), 75) for a in all_data]
            ci_subset_lower = [np.percentile(np.array(a), 25) for a in all_data]
            
            #subset_std = [np.std(np.array(a)) for a in all_data]
            #subset_sem = [std / sqrt(len(subset_raws)) for std in subset_std]
            #ci_subset_upper = [subset_avg[i] + (1.96 * subset_sem[i]) for i in range(len(subset_avg))]
            #ci_subset_lower = [subset_avg[i] - (1.96 * subset_sem[i]) for i in range(len(subset_avg))]

            confidence.append((ci_subset_lower, ci_subset_upper))

        all_datas.append(all_data)
        times.append(time)
        averages.append(subset_avg)
        medians.append(subset_med)

    # Voor elk meetpunt -> test doen
    pvals = []
    pval_times = []

    L = min([len(all_datas[0]), len(all_datas[1])])
    PVAL_EVERY = 600 # 10 = 1 sec, 600 = 1 min
    for i in range(0, floor(L / PVAL_EVERY)):
        try:
            a = all_datas[0][i * PVAL_EVERY + 1]
            b = all_datas[1][i * PVAL_EVERY + 1]
            stat, pval = ranksums(a, b)
            pvals.append(pval)
            pval_times.append(times[0][i * PVAL_EVERY + 1])

            #print("Median %i, series 0: %.4f" % (i, np.median(np.array(a))))
            #print(" - 25th pct: %.4f; 75th pct: %.4f" % (np.percentile(np.array(a), 25), np.percentile(np.array(a), 75)))
            #print("Median %i, series 1: %.4f" % (i, np.median(np.array(b))))
            #print(" - 25th pct: %.4f; 75th pct: %.4f" % (np.percentile(np.array(b), 25), np.percentile(np.array(b), 75)))

        except ValueError:
            pass

    print(len(pvals))

    # Plot what needs to be plotted
    filter_n = 5000

    colors = ["red", "blue"]

    for i in range(len(stats)):
        ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, medians[i]), colors[i])

        if show_bands:
            ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][0]), "grey", linestyle="dashed", linewidth=0.5)
            ax.plot(times[i], signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][1]), "grey", linestyle="dashed", linewidth=0.5)
            ax.fill_between(times[i], \
                signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][0]), signal.lfilter([1.0 / filter_n] * filter_n, 1, confidence[i][1]), \
                color=colors[i], alpha=0.2)

ax.set_xlim(0, 30 * 60 * 1000)
#ax.set_ylim(0, 16)

plt.legend(handles=[mpatches.Patch(color="red", label="Small bites (5x5), n = 12"), \
    mpatches.Patch(color="blue", label="Large bites (10x10), n = 12"), \
    mpatches.Patch(color="black", alpha=0.2, label="Significant difference (p < 0.05)")])

plt.title("Suture tension over 30 mins at 20 mmHg IAP in six porcine abdominal walls\n")
plt.grid()
ax.set_ylabel("Change in force (N)")
ax.set_xlabel("Time (h:mm:ss)")

if show_pvals:
    ax2 = ax.twinx()
    ax2.set_ylabel("p-value")
    ax2.axhline(0.05, color="black")
    ax2.plot(pval_times, pvals, color="green")

# Code for drawing significant (p < 0.05) shading in the graph
a = None
b = None
for i, pval in enumerate(pvals):
    if a is None and pval < 0.05:
        a = pval_times[i]
    elif a is not None and pval >= 0.05:
        b = pval_times[i]

    if a is not None and b is not None:
        ax.axvspan(a, b, alpha=0.2, color="black")
        a = None
        b = None

if a is not None and b is None:
    ax.axvspan(a, ax.get_xlim()[1], alpha=0.2, color="black")

plt.show()

