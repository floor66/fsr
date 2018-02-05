import matplotlib.pyplot as plt

f = open("sensordata/data_1517492767_4.txt")
lines = f.readlines()

FREQ = 50
MOD_DIV = 1/50 # Show only every x seconds

ts = []
vs = []
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
                        vs.append(voltage)
                    else:
                        ts.append(t)
                        vs.append(0)

vs_avg = []
ct = 0
i = 0
for val in vs:
    i += 1
    ct += val

    vs_avg.append(ct / i)

#plt.plot([t/60000 for t in ts], vs_avg)
plt.plot([t/60000 for t in ts], vs)
#plt.xlim(, ts[-1]/60000)
plt.ylim(0, 5.07)
plt.grid()
plt.show()
