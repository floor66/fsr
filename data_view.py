import matplotlib.pyplot as plt

f = open("sensordata/data_1517492767_4.txt")
lines = f.readlines()

FREQ = 50
MOD_DIV = 1/50 # Show only every x seconds

ts = []
vals = []
volts = []
resists = []
i = 0
for l in lines:
    i += 1
    
    if l[0] != ";":
        if ((i % (FREQ * MOD_DIV)) == 0) or (i == 1):
            tmp = l.rstrip().split(",")

            if len(tmp) == 3:
                    t = int(tmp[0])
                    v = int(tmp[2])

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

N = 50 * 20 # mavg window, 50/sec
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
                r = 10000 * ((5.06 / voltage) - 1)

                volts_mavg.append(voltage)
                resists_mavg.append(r)

to_show = "resists"

plt.plot([t/60000 for t in ts], eval(to_show), "b-")
plt.plot([t/60000 for t in ts], eval("%s_avg" % to_show), "r-")
plt.plot([t/60000 for t in ts], eval("%s_mavg" % to_show), "m-", linewidth=2.0)
#plt.xlim(, ts[-1]/60000)
#plt.ylim(0, 1023)
plt.grid()
plt.show()
